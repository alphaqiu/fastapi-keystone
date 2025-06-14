"""
Server module for FastAPI-Keystone.

Provides the Server class for application lifecycle management, middleware registration, and integration with dependency injection.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from logging import Logger, getLogger
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from injector import inject
from starlette.middleware import _MiddlewareFactory
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from fastapi_keystone.config.config import Config
from fastapi_keystone.core.app import AppManagerProtocol
from fastapi_keystone.core.exceptions import (
    APIException,
    api_exception_handler,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from fastapi_keystone.core.middlewares import (
    EtagMiddleware,
    ExceptionMiddleware,
    HSTSMiddleware,
    SimpleTraceMiddleware,
    TenantMiddleware,
)
from fastapi_keystone.core.routing import register_controllers

logger = getLogger(__name__)

_EXCEPTION_HANDLERS = [
    (APIException, api_exception_handler),
    (HTTPException, http_exception_handler),
    (RequestValidationError, validation_exception_handler),
    (Exception, global_exception_handler),
]


class Server:
    """
    FastAPI application server wrapper.

    Manages application lifecycle, middleware, and dependency injection.

    Attributes:
        Methods:
        on_startup(func): Register a startup event handler.
        on_shutdown(func): Register a shutdown event handler.
        enable_tenant(): Enable multi-tenant support.
        enable_trusted_host(trusted_hosts, www_redirect): Enable trusted host validation.
        enable_simple_trace(trace_logger): Enable simple request tracing middleware.
        enable_etag(max_content_length): Enable ETag middleware.
        enable_hsts(): Enable HSTS middleware.
        force_https(): Force HTTPS redirection.
        disable_gzip(): Disable gzip compression.
        enable_cors(...): Enable and configure CORS middleware.
        add_middleware(middleware_class, **kwargs): Add custom middleware.
        setup_api(controllers, **kwargs): Register API controllers and setup routes.
        run(app): Run the FastAPI application.
    """

    @inject
    def __init__(self, manager: AppManagerProtocol):
        """
        Initialize the Server.

        Args:
            manager (AppManagerProtocol): The application manager (DI container).
        """
        self.manager = manager
        self.config = manager.get_instance(Config)
        self._on_startup: List[Callable[[FastAPI, Config], Awaitable[None]]] = []
        self._on_shutdown: List[Callable[[FastAPI, Config], Awaitable[None]]] = []
        self._middlewares: List[Tuple[_MiddlewareFactory, Dict[str, Any]]] = []

        # 跟踪已经调用过的配置方法，确保每个方法只能生效一次
        self._configured_features: set[str] = set()

        # Gzip 配置
        self._gzip_minimum_size: int = 500  # 默认值
        self._gzip_compresslevel: int = 9

        self.is_already_setup = False

        # 根据配置自动启用中间件
        self._auto_configure_middlewares()

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """
        Application lifespan context manager.

        Args:
            app (FastAPI): The FastAPI application instance.
        """
        logger.info("Starting server, init on startup callbacks")
        for func in self._on_startup:
            await func(app, self.config)

        yield

        logger.info("Stopping server, init on shutdown callbacks")
        for func in self._on_shutdown:
            await func(app, self.config)

    def on_startup(
        self, func: Optional[Callable[[FastAPI, Config], Awaitable[None]]] = None
    ) -> "Server":
        """
        Register a startup callback.

        Args:
            func (Optional[Callable]): The callback to run on startup.

        Returns:
            Server: The server instance (for chaining).
        """
        if func:
            self._on_startup.append(func)
        return self

    def on_shutdown(
        self, func: Optional[Callable[[FastAPI, Config], Awaitable[None]]] = None
    ) -> "Server":
        """
        Register a shutdown callback.

        Args:
            func (Optional[Callable]): The callback to run on shutdown.

        Returns:
            Server: The server instance (for chaining).
        """
        if func:
            self._on_shutdown.append(func)
        return self

    def enable_trusted_host(
        self, trusted_hosts: List[str] = ["*"], www_redirect: bool = True
    ) -> "Server":
        """
        Enable trusted host for all requests.

        Note: This method can only be called once. Subsequent calls will be ignored.

        Args:
            trusted_hosts (List[str]): List of trusted hosts. Defaults to ["*"].
            www_redirect (bool): Whether to redirect www. Defaults to True.

        Returns:
            Server: The server instance (for chaining).
        """
        if "trusted_host" in self._configured_features:
            return self

        self._configured_features.add("trusted_host")
        self.trusted_host_middleware = TrustedHostMiddleware
        self.trusted_host_configs: Tuple[Sequence[str], bool] = (
            trusted_hosts,
            www_redirect,
        )
        return self

    def enable_simple_trace(self, trace_logger: Optional[Logger] = None) -> "Server":
        """
        Enable simple trace middleware for all requests.

        Note: This method can only be called once. Subsequent calls will be ignored.

        Args:
            trace_logger (Optional[Logger]): Logger instance for tracing. Defaults to None.

        Returns:
            Server: The server instance (for chaining).
        """
        if "simple_trace" in self._configured_features:
            return self

        self._configured_features.add("simple_trace")
        self.simple_trace_middleware = SimpleTraceMiddleware
        self.simple_trace_configs: Optional[Logger] = trace_logger
        return self

    def enable_tenant(self) -> "Server":
        """
        Enable tenant middleware for multi-tenant support.

        Note: This method can only be called once. Subsequent calls will be ignored.

        Returns:
            Server: The server instance (for chaining).
        """
        if "tenant" in self._configured_features:
            return self

        self._configured_features.add("tenant")
        self.tenant_middleware = TenantMiddleware
        return self

    def enable_etag(self, max_content_length: int = 1024 * 1024) -> "Server":
        """
        Enable ETag for all requests.

        Note: This method can only be called once. Subsequent calls will be ignored.

        Returns:
            Server: The server instance (for chaining).
        """
        if "etag" in self._configured_features:
            return self

        self._configured_features.add("etag")
        self.etag_middleware = EtagMiddleware
        self.etag_configs: int = max_content_length
        return self

    def enable_hsts(self) -> "Server":
        """
        Enable HSTS for all requests.

        Note: This method can only be called once. Subsequent calls will be ignored.

        Returns:
            Server: The server instance (for chaining).
        """
        if "hsts" in self._configured_features:
            return self

        self._configured_features.add("hsts")
        self.hsts_middleware = HSTSMiddleware
        return self

    def force_https(self) -> "Server":
        """
        Force HTTPS for all requests.

        Note: This method can only be called once. Subsequent calls will be ignored.

        Returns:
            Server: The server instance (for chaining).
        """
        if "force_https" in self._configured_features:
            return self

        self._configured_features.add("force_https")
        self.force_https_middleware = HTTPSRedirectMiddleware
        return self

    def disable_gzip(self) -> "Server":
        """
        Disable gzip compression for all requests.

        Note: This method can only be called once. Subsequent calls will be ignored.

        Returns:
            Server: The server instance (for chaining).
        """
        if "disable_gzip" in self._configured_features:
            return self

        self._configured_features.add("disable_gzip")
        self._gzip_disabled = True
        return self

    def enable_cors(
        self,
        *,
        allow_credentials: bool = True,
        allow_origins: List[str] = ["*"],
        allow_methods: List[str] = ["*"],
        allow_headers: List[str] = ["*"],
    ) -> "Server":
        """
        Enable CORS for all requests.

        Note: This method can only be called once. Subsequent calls will be ignored.

        Args:
            allow_credentials (bool): Whether to allow credentials. Defaults to True.
            allow_origins (List[str]): List of allowed origins. Defaults to ["*"].
            allow_methods (List[str]): List of allowed methods. Defaults to ["*"].
            allow_headers (List[str]): List of allowed headers. Defaults to ["*"].

        Returns:
            Server: The server instance (for chaining).
        """
        if "cors" in self._configured_features:
            return self

        self._configured_features.add("cors")
        self.cors_middleware = CORSMiddleware
        if allow_origins is None or len(allow_origins) == 0:
            allow_origins = ["*"]
        if allow_methods is None or len(allow_methods) == 0:
            allow_methods = ["*"]
        if allow_headers is None or len(allow_headers) == 0:
            allow_headers = ["*"]
        self.cors_configs: Tuple[Sequence[str], Sequence[str], Sequence[str], bool] = (
            allow_origins,
            allow_methods,
            allow_headers,
            allow_credentials,
        )
        return self

    def add_middleware(self, middleware_class: _MiddlewareFactory, **kwargs: Any) -> "Server":
        """
        Add a custom middleware to the application.

        Args:
            middleware_class (Type[BaseHTTPMiddleware]): The middleware class.
            **kwargs: Additional keyword arguments for the middleware.

        Returns:
            Server: The server instance (for chaining).
        """
        self._middlewares.append((middleware_class, kwargs))
        return self

    def setup_api(self, controllers: List[Any], **kwargs) -> FastAPI:
        if self.is_already_setup:
            return self.app  # type: ignore

        logger.info("Setting up API")
        self.app = FastAPI(
            title=self.config.server.title,
            description=self.config.server.description,
            version=self.config.server.version,
            lifespan=self._lifespan,
            **kwargs,
        )

        logger.info("Setting up middlewares")
        for middleware_class, kwargs in self._middlewares:
            self.app.add_middleware(middleware_class, **kwargs)

        self.app.add_middleware(ExceptionMiddleware)

        if hasattr(self, "etag_middleware") and hasattr(self, "etag_configs"):
            logger.info("Setting up etag middleware")
            self.app.add_middleware(self.etag_middleware, max_content_length=self.etag_configs)

        if not hasattr(self, "_gzip_disabled") or not self._gzip_disabled:
            logger.info("Setting up gzip middleware")
            self.app.add_middleware(
                GZipMiddleware,
                minimum_size=self._gzip_minimum_size,
                compresslevel=self._gzip_compresslevel,
            )

        if hasattr(self, "hsts_middleware"):
            logger.info("Setting up HSTS middleware")
            self.app.add_middleware(self.hsts_middleware)

        if hasattr(self, "tenant_middleware"):
            logger.info("Setting up tenant middleware")
            self.app.add_middleware(self.tenant_middleware, config=self.config)

        if hasattr(self, "simple_trace_middleware") and hasattr(self, "simple_trace_configs"):
            logger.info("Setting up simple trace middleware")
            self.app.add_middleware(self.simple_trace_middleware, logger=self.simple_trace_configs)

        if hasattr(self, "cors_middleware") and hasattr(self, "cors_configs"):
            logger.info("Setting up CORS middleware")
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.cors_configs[0],
                allow_methods=self.cors_configs[1],
                allow_headers=self.cors_configs[2],
                allow_credentials=self.cors_configs[3],
            )

        if hasattr(self, "force_https_middleware"):
            logger.info("Setting up force https middleware")
            self.app.add_middleware(self.force_https_middleware)

        if hasattr(self, "trusted_host_middleware") and hasattr(self, "trusted_host_configs"):
            logger.info("Setting up trusted host middleware")
            self.app.add_middleware(
                self.trusted_host_middleware,
                allowed_hosts=self.trusted_host_configs[0],
                www_redirect=self.trusted_host_configs[1],
            )

        logger.info("Setting up exception handlers")
        # 设置异常处理
        for exc_type, handler in _EXCEPTION_HANDLERS:
            self.app.add_exception_handler(exc_type, handler)

        logger.info("Registering controllers")
        # 注册路由
        register_controllers(self.app, self.manager, controllers)
        self.is_already_setup = True
        return self.app

    def get_app(self) -> FastAPI:
        if not self.is_already_setup:
            raise RuntimeError("Server is not setup yet")
        return self.app

    def run(self, app: FastAPI):
        """作为一个独立的server运行"""
        import uvicorn

        host = self.config.server.host
        port = self.config.server.port
        reload = self.config.server.reload
        workers = self.config.server.workers
        logger.info(f"Running server on {host}:{port}")
        uvicorn.run(app, host=host, port=port, reload=reload, workers=workers)

    def _auto_configure_middlewares(self):
        """根据配置自动启用中间件"""
        try:
            if not hasattr(self.config, "server") or not hasattr(self.config.server, "middleware"):
                return

            middleware_config = self.config.server.middleware

            if middleware_config.etag and middleware_config.etag.enabled:
                self.enable_etag()

            # Gzip 配置处理
            if middleware_config.gzip:
                if not middleware_config.gzip.enabled:
                    self.disable_gzip()
                else:
                    # 存储 Gzip 配置
                    self._gzip_minimum_size = middleware_config.gzip.minimum_size

            if middleware_config.hsts and middleware_config.hsts.enabled:
                self.enable_hsts()

            if hasattr(self.config.server, "tenant_enabled") and self.config.server.tenant_enabled:
                self.enable_tenant()

            if middleware_config.simple_trace and middleware_config.simple_trace.enabled:
                self.enable_simple_trace()

            if middleware_config.cors and middleware_config.cors.enabled:
                self.enable_cors(
                    allow_credentials=middleware_config.cors.allow_credentials,
                    allow_origins=middleware_config.cors.allow_origins,
                    allow_methods=middleware_config.cors.allow_methods,
                    allow_headers=middleware_config.cors.allow_headers,
                )

            if middleware_config.force_https:
                self.force_https()

            # 自动启用配置的中间件
            if middleware_config.trusted_host and middleware_config.trusted_host.enabled:
                self.enable_trusted_host(
                    trusted_hosts=middleware_config.trusted_host.allowed_hosts,
                    www_redirect=middleware_config.trusted_host.www_redirect,
                )

        except (AttributeError, TypeError):
            logger.warning(
                "Middleware configuration is not complete, some middlewares may not be enabled"
            )
            pass

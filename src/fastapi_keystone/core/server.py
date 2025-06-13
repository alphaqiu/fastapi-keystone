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
from fastapi_keystone.core import AppManagerProtocol
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
        manager (AppManagerProtocol): The application manager (DI container).
        config (Config): The application configuration.
        _on_startup (List[Callable]): Startup callbacks.
        _on_shutdown (List[Callable]): Shutdown callbacks.
        _middlewares (List[Tuple[Type[BaseHTTPMiddleware], Any]]): Registered middlewares.
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
        """
        self.trusted_host_middleware = TrustedHostMiddleware
        self.trusted_host_configs: Tuple[Sequence[str], bool] = (
            trusted_hosts,
            www_redirect,
        )
        return self

    def enable_simple_trace(self, logger: Optional[Logger] = None) -> "Server":
        """
        Enable simple trace middleware for all requests.
        """
        self.simple_trace_middleware = SimpleTraceMiddleware
        self.simple_trace_configs: Optional[Logger] = logger
        return self

    def enable_tenant(self) -> "Server":
        """
        Enable tenant middleware for multi-tenant support.

        Returns:
            Server: The server instance (for chaining).
        """
        self.tenant_middleware = TenantMiddleware
        return self

    def enable_etag(self) -> "Server":
        """
        Enable ETag for all requests.
        """
        self.etag_middleware = EtagMiddleware
        return self

    def enable_hsts(self) -> "Server":
        """
        Enable HSTS for all requests.
        """
        self.hsts_middleware = HSTSMiddleware
        return self

    def force_https(self) -> "Server":
        """
        Force HTTPS for all requests.
        """
        self.force_https_middleware = HTTPSRedirectMiddleware
        return self

    def disable_gzip(self) -> "Server":
        """
        Disable gzip compression for all requests.
        """
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
        """
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
        logger.info("Setting up API")
        self.app = FastAPI(
            title=self.config.server.title,
            description=self.config.server.description,
            version=self.config.server.version,
            lifespan=self._lifespan,
            **kwargs,
        )

        if hasattr(self, "trusted_host_middleware"):
            logger.info("Setting up trusted host middleware")
            self.app.add_middleware(
                self.trusted_host_middleware,
                allowed_hosts=self.trusted_host_configs[0],
                www_redirect=self.trusted_host_configs[1],
            )

        if hasattr(self, "force_https_middleware"):
            logger.info("Setting up force https middleware")
            self.app.add_middleware(self.force_https_middleware)

        if hasattr(self, "simple_trace_middleware"):
            logger.info("Setting up simple trace middleware")
            self.app.add_middleware(self.simple_trace_middleware, logger=self.simple_trace_configs)

        if hasattr(self, "tenant_middleware"):
            logger.info("Setting up tenant middleware")
            self.app.add_middleware(self.tenant_middleware, config=self.config)        

        self.app.add_middleware(ExceptionMiddleware)

        if hasattr(self, "etag_middleware"):
            logger.info("Setting up etag middleware")
            self.app.add_middleware(self.etag_middleware)

        if hasattr(self, "hsts_middleware"):
            logger.info("Setting up HSTS middleware")
            self.app.add_middleware(self.hsts_middleware)

        # 设置中间件
        if hasattr(self, "cors_middleware"):
            logger.info("Setting up CORS middleware")
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.cors_configs[0],
                allow_methods=self.cors_configs[1],
                allow_headers=self.cors_configs[2],
                allow_credentials=self.cors_configs[3],
            )
        if not hasattr(self, "_gzip_disabled") or not self._gzip_disabled:
            logger.info("Setting up gzip middleware")
            self.app.add_middleware(
                GZipMiddleware,
                minimum_size=1024,
            )

        logger.info("Setting up middlewares")
        for middleware_class, kwargs in self._middlewares:
            self.app.add_middleware(middleware_class, **kwargs)

        logger.info("Setting up exception handlers")
        # 设置异常处理
        for exc_type, handler in _EXCEPTION_HANDLERS:
            self.app.add_exception_handler(exc_type, handler)

        logger.info("Registering controllers")
        # 注册路由
        register_controllers(self.app, self.manager, controllers)
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

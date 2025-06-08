from __future__ import annotations

from contextlib import asynccontextmanager
from logging import getLogger
from typing import Any, Awaitable, Callable, List, Optional, Tuple, Type

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from injector import inject
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi_keystone.config.config import Config
from fastapi_keystone.core.di import AppInjector
from fastapi_keystone.core.exceptions import (
    APIException,
    api_exception_handler,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from fastapi_keystone.core.middleware import TenantMiddleware
from fastapi_keystone.core.routing import register_controllers

logger = getLogger(__name__)


class Server:
    @inject
    def __init__(self, config: Config, **kwargs):
        self.config: Config = config
        self.kwargs = kwargs
        self._on_startup: List[Callable[[FastAPI, Config], Awaitable[None]]] = []
        self._on_shutdown: List[Callable[[FastAPI, Config], Awaitable[None]]] = []
        self._middlewares: List[Tuple[Type[BaseHTTPMiddleware], Any, Any]] = []

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
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
        """注册启动时回调"""
        if func:
            self._on_startup.append(func)
        return self

    def on_shutdown(
        self, func: Optional[Callable[[FastAPI, Config], Awaitable[None]]] = None
    ) -> "Server":
        """注册关闭时回调"""
        if func:
            self._on_shutdown.append(func)
        return self

    def enable_tenant_middleware(self) -> "Server":
        """启用租户中间件"""
        self._middlewares.append((TenantMiddleware, [], {}))
        return self

    def add_middleware(
        self, middleware_class: Type[BaseHTTPMiddleware], *args: Any, **kwargs: Any
    ) -> "Server":
        """添加中间件"""
        self._middlewares.append((middleware_class, args, kwargs))
        return self

    def setup_api(self, injector: AppInjector, controllers: List[Any]) -> FastAPI:
        logger.info("Setting up API")
        self.app = FastAPI(
            title=self.config.server.title,
            description=self.config.server.description,
            version=self.config.server.version,
            lifespan=self._lifespan,
            **self.kwargs,
        )

        logger.info("Setting up CORS middleware")
        # 设置中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("Setting up middlewares")
        for middleware_class, args, kwargs in self._middlewares:
            self.app.add_middleware(middleware_class, *args, **kwargs)

        logger.info("Setting up exception handlers")
        # 设置异常处理
        self.app.add_exception_handler(APIException, api_exception_handler)
        self.app.add_exception_handler(HTTPException, http_exception_handler)
        self.app.add_exception_handler(
            RequestValidationError, validation_exception_handler
        )
        self.app.add_exception_handler(Exception, global_exception_handler)

        logger.info("Registering controllers")
        # 注册路由
        register_controllers(self.app, injector, controllers)
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

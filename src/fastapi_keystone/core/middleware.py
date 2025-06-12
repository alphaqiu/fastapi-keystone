from logging import getLogger
from typing import Optional

from fastapi import Response
from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from fastapi_keystone.config import Config
from fastapi_keystone.core.db import tenant_id_context

logger = getLogger(__name__)


class Demo(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, config: Config):
        super().__init__(app)
        self.config = config

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        return await call_next(request)


class TenantMiddleware:
    def __init__(self, app: ASGIApp, config: Config):
        self.config = config
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        tenant_id: Optional[str] = None
        if not self.config.server.tenant_enabled:
            logger.debug("use without tenant mode. tenant_id is default")
            tenant_id = "default"
            # 将 tenant_id 存入 ContextVar
            token = tenant_id_context.set(tenant_id)
            await self.app(scope, receive, send)
            # 重置 ContextVar
            tenant_id_context.reset(token)
            return

        headers = Headers(scope=scope)
        # 多租户模式
        logger.debug("use with tenant mode")
        tenant_id = headers.get("X-Tenant-ID")
        if not tenant_id:
            # 可以根据业务需求返回错误或使用默认租户
            response = Response("X-Tenant-ID header is required", status_code=400)
            await response(scope, receive, send)
            return

        # 将 tenant_id 存入 ContextVar
        token = tenant_id_context.set(tenant_id)

        try:
            await self.app(scope, receive, send)
        finally:
            tenant_id_context.reset(token)

from logging import getLogger
from typing import Any, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from fastapi_keystone.config import Config
from fastapi_keystone.core.db import tenant_id_context

logger = getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, config: Config):
        super().__init__(app)
        self.config = config

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        tenant_id: Optional[str] = None
        if not self.config.server.tenant_enabled:
            logger.debug("use without tenant mode. tenant_id is default")
            tenant_id = "default"
            # 将 tenant_id 存入 ContextVar
            token = tenant_id_context.set(tenant_id)

            response = await call_next(request)

            # 重置 ContextVar
            tenant_id_context.reset(token)
            return response

        # 多租户模式
        logger.debug("use with tenant mode")
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            # 可以根据业务需求返回错误或使用默认租户
            return Response("X-Tenant-ID header is required", status_code=400)

        # 将 tenant_id 存入 ContextVar
        token = tenant_id_context.set(tenant_id)

        response = await call_next(request)

        # 重置 ContextVar
        tenant_id_context.reset(token)

        return response

import time
from contextvars import ContextVar
from logging import Logger, getLogger
from typing import Optional

from fastapi import Response, status
from starlette.datastructures import Headers, MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send
from ulid import ULID

from fastapi_keystone.config import Config
from fastapi_keystone.core.db import tenant_id_context
from fastapi_keystone.core.response import APIResponse

logger = getLogger(__name__)

request_context: ContextVar[dict] = ContextVar("request_context", default={})


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            return APIResponse.error(message=str(e), code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SimpleTraceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, logger: Optional[Logger] = None):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        ulid = ULID.from_timestamp(start_time)
        token = request_context.set({"x-request-id": str(ulid)})

        response = await call_next(request)

        end_time = time.time()
        if self.logger is not None:
            self.logger.info(
                (
                    f"{request.method.upper()} {request.url.path} "
                    f"Time elapsed:{end_time - start_time:.2f}s "
                    f"ULID:{str(ulid)}"
                )
            )

        headers: MutableHeaders = response.headers
        headers.append("X-Time-Elapsed", f"{end_time - start_time:.2f}s")
        headers.append("X-Request-ID", str(ulid))

        request_context.reset(token)
        return response


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

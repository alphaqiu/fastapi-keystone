from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from fastapi_keystone.core.db import tenant_id_context


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
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

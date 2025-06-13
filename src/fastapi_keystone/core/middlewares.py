import hashlib
import time
from contextvars import ContextVar
from logging import Logger, getLogger
from typing import Any, NotRequired, Optional, TypedDict

from fastapi import Response, status
from starlette.datastructures import Headers, MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from ulid import ULID

from fastapi_keystone.config import Config
from fastapi_keystone.core.response import APIResponse

logger = getLogger(__name__)


class ContextDict(TypedDict):
    """
    Typed dictionary for storing request-scoped context data.

    This context is used to pass metadata and control flags across middlewares
    and request handlers using ContextVar. It supports ETag control, request ID,
    tenant information, and arbitrary values.

    Attributes:
        etag_enabled (Optional[bool]): Whether ETag processing is enabled for this request.
        x_request_id (Optional[str]): Unique request identifier (e.g., ULID).
        value (Optional[Any]): Arbitrary value for middleware or handler use.
        tenant_id (Optional[str]): Tenant identifier for multi-tenant scenarios.

    Example:
        request_context.set({
            "etag_enabled": True,
            "x_request_id": "01H...ULID...",
            "tenant_id": "tenant-123"
        })
    """

    etag_enabled: NotRequired[bool]
    x_request_id: NotRequired[str]
    value: NotRequired[Any]
    tenant_id: NotRequired[str]


request_context: ContextVar[ContextDict] = ContextVar("request_context", default={})


class HSTSMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add HTTP Strict-Transport-Security (HSTS) headers.

    This middleware ensures that all responses include the
    'Strict-Transport-Security' header, which enforces secure (HTTPS)
    connections to the server.

    Args:
        app (ASGIApp): The ASGI application instance.

    Example:
        app.add_middleware(HSTSMiddleware)
    """

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        return response


class ExceptionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch unhandled exceptions and return a standardized error response.

    This middleware intercepts all exceptions raised during request processing
    and returns a JSON error response with HTTP 500 status code.

    Args:
        app (ASGIApp): The ASGI application instance.

    Example:
        app.add_middleware(ExceptionMiddleware)
    """

    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            return APIResponse.error(message=str(e), code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SimpleTraceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for simple request tracing and logging.

    This middleware generates a unique request ID (ULID), logs request method,
    path, elapsed time, and attaches tracing headers to the response.

    Args:
        app (ASGIApp): The ASGI application instance.
        logger (Optional[Logger]): Optional logger for request tracing.

    Example:
        app.add_middleware(SimpleTraceMiddleware, logger=logger)
    """

    def __init__(self, app: ASGIApp, logger: Optional[Logger] = None):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        ulid = ULID.from_timestamp(start_time)
        token = request_context.set({"x_request_id": str(ulid)})

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


class EtagMiddleware:
    """
    Middleware to add ETag support for JSON responses.

    This middleware calculates the ETag for JSON responses and handles
    conditional requests using the 'If-None-Match' header, returning 304
    if the content has not changed.

    Args:
        app (ASGIApp): The ASGI application instance.

    Example:
        app.add_middleware(EtagMiddleware)
        # Enable ETag in request context before response
        request_context.set({"etag_enabled": True})
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        ctx: ContextDict = request_context.get()
        if ctx.get("etag_enabled", False) is False:
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        response_start: Message = {}
        response_body: bytes = b""
        headers: MutableHeaders = MutableHeaders(scope=scope)

        send_buffer = []

        async def send_wrapper(message: Message):
            nonlocal response_start, response_body, headers
            if message["type"] == "http.response.start":
                response_start = message
                headers = MutableHeaders(scope=message)
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")
            send_buffer.append(message)

        await self.app(scope, receive, send_wrapper)

        # 只处理 application/json
        if not response_start or not headers:
            for message in send_buffer:
                await send(message)
            return

        content_type = headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            for message in send_buffer:
                await send(message)
            return

        # 计算 ETag
        etag = hashlib.sha256(response_body).hexdigest()[:32]
        if_none_match = request.headers.get("if-none-match")

        if if_none_match == etag:
            # 内容未变，返回 304
            response = Response(status_code=304)
            await response(scope, receive, send)
            return
        else:
            # 设置新的 ETag
            headers["etag"] = etag
            for message in send_buffer:
                await send(message)
            return


class TenantMiddleware:
    """
    Middleware for multi-tenant support.

    This middleware extracts the tenant ID from the 'X-Tenant-ID' header
    and stores it in the request context. If multi-tenancy is disabled,
    a default tenant ID is used.

    Args:
        app (ASGIApp): The ASGI application instance.
        config (Config): Application configuration object.

    Example:
        app.add_middleware(TenantMiddleware, config=config)
    """

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
            token = request_context.set({"tenant_id": tenant_id})
            await self.app(scope, receive, send)
            # 重置 ContextVar
            request_context.reset(token)
            return

        headers = Headers(scope=scope)
        # 多租户模式
        logger.debug("use with tenant mode")
        tenant_id = headers.get("X-Tenant-ID")
        if not tenant_id:
            # 可以根据业务需求返回错误或使用默认租户
            response = Response(
                "X-Tenant-ID header is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            await response(scope, receive, send)
            return

        # 将 tenant_id 存入 ContextVar
        token = request_context.set({"tenant_id": tenant_id})

        try:
            await self.app(scope, receive, send)
        finally:
            request_context.reset(token)

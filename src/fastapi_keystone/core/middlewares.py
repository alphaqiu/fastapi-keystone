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
        x_request_id (Optional[str]): Unique request identifier (e.g., ULID).
        value (Optional[Any]): Arbitrary value for middleware or handler use.
        tenant_id (Optional[str]): Tenant identifier for multi-tenant scenarios.

    Example:
        request_context.set({
            "x_request_id": "01H...ULID...",
            "tenant_id": "tenant-123"
        })
    """

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
        request_id = request.headers.get("X-Request-ID")
        if not request_id or request_id == "":
            ulid = ULID.from_timestamp(start_time)
            request_id = str(ulid)

        try:
            ctx: ContextDict = request_context.get()
        except LookupError:
            ctx = {}

        ctx["x_request_id"] = request_id
        token = request_context.set(ctx)

        print("simple trace middleware start")
        response = await call_next(request)
        print("simple trace middleware end")

        end_time = time.time()
        if self.logger is not None:
            self.logger.info(
                (
                    f"{request.method.upper()} {request.url.path} "
                    f"Time elapsed:{end_time - start_time:.2f}s "
                    f"Request ID:{request_id}"
                )
            )

        headers: MutableHeaders = response.headers
        headers.append("X-Time-Elapsed", f"{end_time - start_time:.2f}s")
        headers.append("X-Request-ID", request_id)

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
        max_content_length (int): Maximum content length to process ETag (default: 1MB)

    Example:
        app.add_middleware(EtagMiddleware, max_content_length=1024*1024)
        # Enable ETag in request context before response
        request_context.set({"etag_enabled": True})
    """

    def __init__(self, app: ASGIApp, max_content_length: int = 1024 * 1024):
        self.app = app
        self.max_content_length = max_content_length

    async def _process_etag_response(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        start_message: Optional[Message],
        body: bytes,
        if_none_match: Optional[str],
    ) -> None:
        """处理ETag响应"""
        if not start_message:
            return

        # 计算ETag
        etag: str = hashlib.sha256(body).hexdigest()[:32]

        # 检查是否匹配
        if if_none_match and if_none_match.strip('"') == etag:
            # 返回304 Not Modified，但保留原有的响应头
            # 修改原始响应的状态码而不是创建新响应，以保留其他中间件添加的头部
            headers = MutableHeaders(scope=start_message)
            headers["etag"] = etag

            # 修改状态码为304
            start_message_304 = {
                **start_message,
                "status": status.HTTP_304_NOT_MODIFIED,
            }

            # 发送修改后的start消息
            await send(start_message_304)
            # 304响应不应该有响应体
            await send({"type": "http.response.body", "body": b"", "more_body": False})
            return

        # 修改响应头添加ETag
        headers = MutableHeaders(scope=start_message)
        headers["etag"] = etag

        # 发送响应
        await send(start_message)
        await send({"type": "http.response.body", "body": body, "more_body": False})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        if_none_match = request.headers.get("if-none-match")

        # 用于收集响应信息
        response_start_message: Optional[Message] = None
        response_body = b""
        content_length = 0
        is_json_response = False
        etag_should_process = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_start_message, response_body, content_length
            nonlocal is_json_response, etag_should_process

            if message["type"] == "http.response.start":
                response_start_message = message
                headers = MutableHeaders(scope=message)
                content_type: str = headers.get("content-type", "")
                is_json_response = content_type.startswith("application/json")

                # 只有当满足条件时才处理ETag
                etag_should_process = (
                    is_json_response
                    and message.get("status", status.HTTP_200_OK)
                    == status.HTTP_200_OK  # 只对200状态码处理ETag
                )

                if not etag_should_process:
                    # 直接转发消息
                    await send(message)
                return

            elif message["type"] == "http.response.body":
                if not etag_should_process:
                    # 直接转发消息
                    await send(message)
                    return

                body = message.get("body", b"")

                # 收集响应体用于ETag计算
                content_length += len(body)

                # 如果内容太大，放弃ETag处理，直接转发
                if content_length > self.max_content_length:
                    # 发送之前收集的start消息（如果还没发送）
                    if response_start_message:
                        await send(response_start_message)
                        response_start_message = None

                    # 发送已收集的body
                    if response_body:
                        await send(
                            {
                                "type": "http.response.body",
                                "body": response_body,
                                "more_body": True,
                            }
                        )

                    # 发送当前body
                    await send(message)
                    etag_should_process = False
                    return

                response_body += body

                # 如果这是最后一个body消息，处理ETag
                if not message.get("more_body", False):
                    await self._process_etag_response(
                        scope,
                        receive,
                        send,
                        response_start_message,
                        response_body,
                        if_none_match,
                    )

        print("etag middleware start")
        await self.app(scope, receive, send_wrapper)
        print("etag middleware end")


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

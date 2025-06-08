from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi_keystone.core.response import APIResponse


class APIException(Exception):
    """统一的异常返回格式，用于在全局异常处理中使用"""

    def __init__(self, message: str, code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.code = code


def api_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """API异常处理"""
    if isinstance(exc, APIException):
        return JSONResponse(
            status_code=exc.code,
            content=APIResponse.error(exc.message, exc.code).model_dump(),
        )
    return global_exception_handler(request, exc)


def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """HTTP异常处理"""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=APIResponse.error(exc.detail, exc.status_code).model_dump(),
        )
    return global_exception_handler(request, exc)


def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """请求验证异常处理"""
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=APIResponse.error(
                message="Validation Error",
                data=jsonable_encoder(exc.errors()),
                code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            ).model_dump(),
        )
    return global_exception_handler(request, exc)


def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=APIResponse.error(
            "Internal Server Error", status.HTTP_500_INTERNAL_SERVER_ERROR
        ).model_dump(),
    )

from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi_keystone.core.response import APIResponse


class APIException(Exception):
    """
    Unified API exception for global exception handling.

    Args:
        message (str): Error message.
        code (int, optional): HTTP status code. Defaults to 400.
    """

    def __init__(self, message: str, code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.code = code


def api_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    FastAPI exception handler for APIException.

    Args:
        request (Request): The incoming request.
        exc (APIException): The API exception instance.

    Returns:
        JSONResponse: Standardized error response.
    """
    if isinstance(exc, APIException):
        return JSONResponse(
            status_code=exc.code,
            content=APIResponse.error(exc.message, exc.code).model_dump(),
        )

    return global_exception_handler(request, exc)


def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    FastAPI exception handler for HTTPException.

    Args:
        request (Request): The incoming request.
        exc (HTTPException): The HTTP exception instance.

    Returns:
        JSONResponse: Standardized error response.
    """
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=APIResponse.error(exc.detail, exc.status_code).model_dump(),
        )
    return global_exception_handler(request, exc)


def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    FastAPI exception handler for request validation errors.

    Args:
        request (Request): The incoming request.
        exc (RequestValidationError): The validation error instance.

    Returns:
        JSONResponse: Standardized error response with validation details.
    """
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


class DatabaseError(Exception):
    """
    Base exception for database operation errors.

    Args:
        message (str): Error message.
    """

    def __init__(self, message: str):
        self.message = message


class RecordNotFoundError(DatabaseError):
    """记录不存在异常"""

    def __init__(self, message: str):
        super().__init__(message)


class DuplicateRecordError(DatabaseError):
    """记录重复异常"""

    def __init__(self, message: str):
        super().__init__(message)


class DatabaseConnectionError(DatabaseError):
    """
    Exception for database connection errors.

    Args:
        message (str): Error message.
    """

    def __init__(self, message: str):
        super().__init__(message)

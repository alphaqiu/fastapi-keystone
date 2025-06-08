from typing import Generic, Optional, TypeVar

from fastapi import status
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """统一的API响应格式"""

    code: int
    message: str
    data: Optional[T] = None

    @classmethod
    def success(cls, data: Optional[T] = None) -> "APIResponse[T]":
        return cls(code=status.HTTP_200_OK, message="success", data=data)

    @classmethod
    def error(
        cls,
        message: str,
        code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[T] = None,
    ) -> "APIResponse[T]":
        return cls(code=code, message=message, data=data)

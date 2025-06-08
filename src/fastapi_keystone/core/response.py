from typing import Generic, Optional, TypeVar

from fastapi import status
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """统一的API响应格式"""

    model_config = ConfigDict(extra="allow")

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

    @classmethod
    def paginated(
        cls,
        data: Optional[T] = None,
        total: int = 0,
        page: int = 1,
        page_size: int = 10,
    ) -> "APIResponse[T]":
        return cls.model_validate(
            {
                "code": status.HTTP_200_OK,
                "message": "success",
                "data": data,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        )

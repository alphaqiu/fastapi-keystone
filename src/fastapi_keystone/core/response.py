from typing import Generic, Optional, TypeVar

from fastapi import status
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Standardized API response model for all endpoints.

    Attributes:
        code (int): Business status code, usually HTTP status code.
        message (str): Message describing the result.
        data (Optional[T]): The actual response data.
    """

    model_config = ConfigDict(extra="allow")

    code: int
    message: str
    data: Optional[T] = None

    @classmethod
    def success(cls, data: Optional[T] = None) -> "APIResponse[T]":
        """
        Create a successful API response.

        Args:
            data (Optional[T]): The response data.

        Returns:
            APIResponse[T]: A response with code 200 and message 'success'.
        """
        return cls(code=status.HTTP_200_OK, message="success", data=data)

    @classmethod
    def error(
        cls,
        message: str,
        code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[T] = None,
    ) -> "APIResponse[T]":
        """
        Create an error API response.

        Args:
            message (str): Error message.
            code (int, optional): Error code. Defaults to 400.
            data (Optional[T], optional): Additional data. Defaults to None.

        Returns:
            APIResponse[T]: A response with error code and message.
        """
        return cls(code=code, message=message, data=data)

    @classmethod
    def paginated(
        cls,
        data: Optional[T] = None,
        total: int = 0,
        page: int = 1,
        size: int = 10,
    ) -> "APIResponse[T]":
        """
        Create a paginated API response.

        Args:
            data (Optional[T]): The page data.
            total (int): Total number of items.
            page (int): Current page number.
            size (int): Page size.

        Returns:
            APIResponse[T]: A paginated response with metadata.
        """
        return cls.model_validate(
            {
                "code": status.HTTP_200_OK,
                "message": "success",
                "data": data,
                "total": total,
                "page": page,
                "size": size,
            }
        )

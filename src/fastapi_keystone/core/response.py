import json
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

# JSON 基本类型定义，参考 https://www.json.org/json-en.html
JSONPrimitive = Union[str, int, float, bool, None]
JSONValue = Union[
    JSONPrimitive,
    Dict[str, Any],  # JSON object
    List[Any],  # JSON array
]

# 约束类型变量，只允许以下三种类型：
# 1. JSON 格式的类型
# 2. 继承自 BaseModel 的类型
# 3. List[BaseModel] 的类型（BaseModel 实例的列表）
T = TypeVar(
    "T",
    bound=Union[
        JSONValue,  # JSON 格式的类型
        BaseModel,  # 继承自 BaseModel 的类型
        List[BaseModel],  # BaseModel 实例的列表
    ],
)


class APIResponseModel(BaseModel, Generic[T]):
    """
    Standardized API response data model.

    Attributes:
        code (int): Business status code, usually HTTP status code.
        message (str): Message describing the result.
        data (Optional[T]): The actual response data.
    """

    model_config = ConfigDict(extra="allow")

    code: int
    message: str
    data: Optional[T] = None


class APIResponse(JSONResponse):
    """
    Standardized API response for all endpoints.

    This class extends JSONResponse to provide a consistent response format
    while being compatible with FastAPI's response system.
    """

    def __init__(
        self,
        content: Any = None,
        status_code: int = status.HTTP_200_OK,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[Any] = None,
        code: Optional[int] = None,
        message: Optional[str] = None,
        data: Any = None,
    ):
        # 存储响应数据属性
        self.code = code or status_code
        self.message = message if message is not None else "success"
        self.data = data

        # 分页相关属性（可选）
        self.total: Optional[int] = None
        self.page: Optional[int] = None
        self.size: Optional[int] = None

        # 如果传入了 code, message, data，构建标准响应格式
        if code is not None or message is not None or data is not None:
            # 处理 BaseModel 对象的序列化
            serialized_data = self._serialize_data(data)
            response_data = {
                "code": self.code,
                "message": self.message,
                "data": serialized_data,
            }
            content = response_data

        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

    def _serialize_data(self, data: Any) -> Any:
        """
        Serialize data to JSON-compatible format.

        Args:
            data: The data to serialize.

        Returns:
            JSON-compatible data.
        """
        if data is None:
            return None
        elif isinstance(data, BaseModel):
            # BaseModel 对象转换为字典
            return data.model_dump()
        elif isinstance(data, list):
            if len(data) == 0:
                return []
            if isinstance(data[0], BaseModel):
                # BaseModel 列表转换为字典列表
                return [item.model_dump() if isinstance(item, BaseModel) else item for item in data]
        # 其他类型直接返回（JSON 基本类型）
        return data

    def model_dump(self, exclude_none: bool = False) -> Dict[str, Any]:
        """
        Convert the response to a dictionary.

        Args:
            exclude_none: Whether to exclude None values.

        Returns:
            Dictionary representation of the response.
        """
        # 序列化 data 字段
        serialized_data = self._serialize_data(self.data)

        result = {
            "code": self.code,
            "message": self.message,
            "data": serialized_data,
        }

        # 添加分页信息（如果存在）
        if self.total is not None:
            result["total"] = self.total
        if self.page is not None:
            result["page"] = self.page
        if self.size is not None:
            result["size"] = self.size

        if exclude_none:
            result = {k: v for k, v in result.items() if v is not None}

        return result

    def model_dump_json(self, exclude_none: bool = False) -> str:
        """
        Convert the response to a JSON string.

        Args:
            exclude_none: Whether to exclude None values.

        Returns:
            JSON string representation of the response.
        """
        return json.dumps(self.model_dump(exclude_none=exclude_none), separators=(",", ":"))

    @classmethod
    def success(
        cls, data: Optional[T] = None, status_code: int = status.HTTP_200_OK
    ) -> "APIResponse":
        """
        Create a successful API response.

        Args:
            data (Optional[T]): The response data.
            status_code (int): HTTP status code. Defaults to 200.

        Returns:
            APIResponse: A response with code 200 and message 'success'.
        """
        return cls(
            code=status_code,
            message="success",
            data=data,
            status_code=status_code,
        )

    @classmethod
    def error(
        cls,
        message: str,
        code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[T] = None,
    ) -> "APIResponse":
        """
        Create an error API response.

        Args:
            message (str): Error message.
            code (int, optional): Error code. Defaults to 400.
            data (Optional[T], optional): Additional data. Defaults to None.

        Returns:
            APIResponse: A response with error code and message.
        """
        return cls(
            code=code,
            message=message,
            data=data,
            status_code=code,
        )

    @classmethod
    def paginated(
        cls,
        data: Optional[T] = None,
        total: int = 0,
        page: int = 1,
        size: int = 10,
        status_code: int = status.HTTP_200_OK,
    ) -> "APIResponse":
        """
        Create a paginated API response.

        Args:
            data (Optional[T]): The page data.
            total (int): Total number of items.
            page (int): Current page number.
            size (int): Page size.
            status_code (int): HTTP status code. Defaults to 200.

        Returns:
            APIResponse: A paginated response with metadata.
        """
        # 创建响应实例并设置属性
        response = cls(code=status_code, message="success", data=data, status_code=status_code)

        # 设置分页属性
        response.total = total
        response.page = page
        response.size = size

        # 重新构建响应内容，包含分页信息
        serialized_data = response._serialize_data(data)
        response_data = {
            "code": status_code,
            "message": "success",
            "data": serialized_data,
            "total": total,
            "page": page,
            "size": size,
        }

        # 重新设置响应体
        response.body = json.dumps(response_data, separators=(",", ":")).encode("utf-8")

        return response


__all__ = ["APIResponse", "APIResponseModel"]

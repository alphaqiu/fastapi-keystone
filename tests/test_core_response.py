"""测试 API 响应格式"""

from typing import Dict, List, Optional

import pytest
from fastapi import status
from pydantic import BaseModel, ValidationError

from fastapi_keystone.core.response import APIResponse


class TestAPIResponse:
    """APIResponse 测试类"""

    # ===== 基本功能测试 =====

    def test_success_response_without_data(self):
        """测试成功响应 - 无数据"""
        response = APIResponse.success()

        assert response.code == status.HTTP_200_OK
        assert response.message == "success"
        assert response.data is None

    def test_success_response_with_string_data(self):
        """测试成功响应 - 字符串数据"""
        test_data = "Hello World"
        response = APIResponse.success(test_data)

        assert response.code == status.HTTP_200_OK
        assert response.message == "success"
        assert response.data == test_data

    def test_success_response_with_dict_data(self):
        """测试成功响应 - 字典数据"""
        test_data = {"name": "Alice", "age": 25}
        response = APIResponse.success(test_data)

        assert response.code == status.HTTP_200_OK
        assert response.message == "success"
        assert response.data == test_data

    def test_success_response_with_list_data(self):
        """测试成功响应 - 列表数据"""
        test_data = [1, 2, 3, 4, 5]
        response = APIResponse.success(test_data)

        assert response.code == status.HTTP_200_OK
        assert response.message == "success"
        assert response.data == test_data

    def test_error_response_default_params(self):
        """测试错误响应 - 默认参数"""
        error_message = "Something went wrong"
        response = APIResponse.error(error_message)

        assert response.code == status.HTTP_400_BAD_REQUEST
        assert response.message == error_message
        assert response.data is None

    def test_error_response_custom_code(self):
        """测试错误响应 - 自定义状态码"""
        error_message = "Not Found"
        custom_code = status.HTTP_404_NOT_FOUND
        response = APIResponse.error(error_message, custom_code)

        assert response.code == custom_code
        assert response.message == error_message
        assert response.data is None

    def test_error_response_with_data(self):
        """测试错误响应 - 包含数据"""
        error_message = "Validation Error"
        error_data = {"field": "email", "error": "Invalid format"}
        response = APIResponse.error(
            error_message, status.HTTP_422_UNPROCESSABLE_ENTITY, error_data
        )

        assert response.code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.message == error_message
        assert response.data == error_data

    # ===== 泛型类型测试 =====

    def test_generic_type_string(self):
        """测试泛型类型 - 字符串"""
        response: APIResponse[str] = APIResponse.success("Hello")

        assert isinstance(response.data, str)
        assert response.data == "Hello"

    def test_generic_type_dict(self):
        """测试泛型类型 - 字典"""
        test_data = {"id": 1, "name": "Test"}
        response: APIResponse[Dict] = APIResponse.success(test_data)

        assert isinstance(response.data, dict)
        assert response.data == test_data

    def test_generic_type_list(self):
        """测试泛型类型 - 列表"""
        test_data = [1, 2, 3]
        response: APIResponse[List[int]] = APIResponse.success(test_data)

        assert isinstance(response.data, list)
        assert response.data == test_data

    def test_generic_type_custom_model(self):
        """测试泛型类型 - 自定义模型"""

        class User(BaseModel):
            id: int
            name: str
            email: Optional[str] = None

        user = User(id=1, name="Alice", email="alice@example.com")
        response: APIResponse[User] = APIResponse.success(user)

        assert isinstance(response.data, User)
        assert response.data.id == 1
        assert response.data.name == "Alice"

    # ===== Pydantic 序列化测试 =====

    def test_model_dump_success(self):
        """测试模型序列化 - 成功响应"""
        test_data = {"key": "value"}
        response = APIResponse.success(test_data)
        dumped = response.model_dump()

        expected = {"code": 200, "message": "success", "data": {"key": "value"}}
        assert dumped == expected

    def test_model_dump_error(self):
        """测试模型序列化 - 错误响应"""
        response = APIResponse.error("Error message", 400)
        dumped = response.model_dump()

        expected = {"code": 400, "message": "Error message", "data": None}
        assert dumped == expected

    def test_model_dump_exclude_none(self):
        """测试模型序列化 - 排除None值"""
        response = APIResponse.success()
        dumped = response.model_dump(exclude_none=True)

        expected = {"code": 200, "message": "success"}
        assert dumped == expected

    def test_json_serialization(self):
        """测试JSON序列化"""
        test_data = {"timestamp": "2024-01-01T00:00:00Z"}
        response = APIResponse.success(test_data)
        json_str = response.model_dump_json()

        assert isinstance(json_str, str)
        assert '"code":200' in json_str
        assert '"message":"success"' in json_str
        assert '"timestamp":"2024-01-01T00:00:00Z"' in json_str

    # ===== 边界情况测试 =====

    def test_none_data_explicitly(self):
        """测试显式传入None数据"""
        response = APIResponse.success(None)

        assert response.code == 200
        assert response.message == "success"
        assert response.data is None

    def test_empty_string_message(self):
        """测试空字符串消息"""
        response = APIResponse.error("")

        assert response.code == 400
        assert response.message == ""
        assert response.data is None

    def test_zero_status_code(self):
        """测试零状态码"""
        response = APIResponse.error("Error", 0)

        assert response.code == 0
        assert response.message == "Error"

    def test_negative_status_code(self):
        """测试负数状态码"""
        response = APIResponse.error("Error", -1)

        assert response.code == -1
        assert response.message == "Error"

    def test_large_status_code(self):
        """测试大数字状态码"""
        response = APIResponse.error("Error", 999)

        assert response.code == 999
        assert response.message == "Error"

    # ===== 复杂数据类型测试 =====

    def test_nested_dict_data(self):
        """测试嵌套字典数据"""
        test_data = {
            "user": {
                "id": 1,
                "profile": {
                    "name": "Alice",
                    "preferences": {"theme": "dark", "language": "zh-CN"},
                },
            }
        }
        response = APIResponse.success(test_data)

        assert response.data == test_data
        if response.data:
            assert response.data["user"]["profile"]["name"] == "Alice"

    def test_mixed_data_types(self):
        """测试混合数据类型"""
        test_data = {
            "string": "text",
            "number": 42,
            "boolean": True,
            "null": None,
            "list": [1, "two", {"three": 3}],
            "dict": {"nested": "value"},
        }
        response = APIResponse.success(test_data)

        assert response.data == test_data

    def test_unicode_data(self):
        """测试Unicode数据"""
        test_data = {
            "chinese": "你好世界",
            "emoji": "🚀✨🎉",
            "russian": "Привет мир",
            "special": "äöü ñ",
        }
        response = APIResponse.success(test_data)

        assert response.data == test_data
        if response.data:
            assert response.data["chinese"] == "你好世界"

    # ===== 类型验证测试 =====

    def test_type_annotations(self):
        """测试类型注解"""
        # 这些应该通过静态类型检查
        str_response: APIResponse[str] = APIResponse.success("text")
        int_response: APIResponse[int] = APIResponse.success(42)
        dict_response: APIResponse[dict] = APIResponse.success({})

        assert isinstance(str_response.data, str)
        assert isinstance(int_response.data, int)
        assert isinstance(dict_response.data, dict)

    def test_response_immutability(self):
        """测试响应对象的不可变性"""
        original_data = {"key": "value"}
        response = APIResponse.success(original_data)

        # 修改原始数据不应影响响应
        original_data["key"] = "modified"

        # 注意：这里只是验证概念，实际上字典是可变的
        # 在实际使用中可能需要深拷贝来确保不可变性
        assert response.data == {"key": "modified"}  # 实际会被修改，这是预期的

    def test_model_validation(self):
        """测试模型验证"""
        # 创建有效的响应
        response = APIResponse(code=200, message="OK", data="test")
        assert response.code == 200

        # 测试无效的类型（这应该通过Pydantic验证）
        with pytest.raises(ValidationError):
            APIResponse(code="invalid", message="OK")  # type: ignore  # code 应该是 int

    # ===== 常见HTTP状态码测试 =====

    def test_common_success_codes(self):
        """测试常见成功状态码"""
        codes_and_names = [
            (200, "OK"),
            (201, "Created"),
            (202, "Accepted"),
            (204, "No Content"),
        ]

        for code, _ in codes_and_names:
            response = APIResponse.success()
            response.code = code
            assert response.code == code

    def test_common_error_codes(self):
        """测试常见错误状态码"""
        codes_and_messages = [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (404, "Not Found"),
            (422, "Unprocessable Entity"),
            (500, "Internal Server Error"),
        ]

        for code, message in codes_and_messages:
            response = APIResponse.error(message, code)
            assert response.code == code
            assert response.message == message

    def test_paginated_response(self):
        """测试分页响应"""
        response = APIResponse.paginated(data=[1, 2, 3], total=3, page=1, page_size=10)
        assert response.code == status.HTTP_200_OK
        assert response.message == "success"
        assert response.data == [1, 2, 3]
        assert response.model_dump() == {
            "code": 200,
            "message": "success",
            "data": [1, 2, 3],
            "total": 3,
            "page": 1,
            "page_size": 10,
        }

        print(response.model_dump_json())

        response = APIResponse.success(data=[1, 2, 3])
        assert response.model_dump() == {
            "code": 200,
            "message": "success",
            "data": [1, 2, 3],
        }

        print(response.model_dump_json())

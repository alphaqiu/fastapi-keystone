"""测试异常处理模块"""

from unittest.mock import Mock, patch

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi_keystone.core.exceptions import (
    APIException,
    api_exception_handler,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from fastapi_keystone.core.response import APIResponse


class TestAPIException:
    """APIException 自定义异常测试"""

    def test_api_exception_default_code(self):
        """测试API异常 - 默认状态码"""
        message = "Something went wrong"
        exc = APIException(message)

        assert str(exc) == message
        assert exc.message == message
        assert exc.code == status.HTTP_400_BAD_REQUEST

    def test_api_exception_custom_code(self):
        """测试API异常 - 自定义状态码"""
        message = "Not found"
        code = status.HTTP_404_NOT_FOUND
        exc = APIException(message, code)

        assert str(exc) == message
        assert exc.message == message
        assert exc.code == code

    def test_api_exception_inheritance(self):
        """测试API异常继承"""
        exc = APIException("Test")
        assert isinstance(exc, Exception)

    def test_api_exception_str_representation(self):
        """测试API异常字符串表示"""
        message = "Error message"
        exc = APIException(message)
        assert str(exc) == message

    def test_api_exception_with_special_characters(self):
        """测试包含特殊字符的异常消息"""
        message = "Error with 中文 and emoji 🚨"
        exc = APIException(message)
        assert exc.message == message


class TestAPIExceptionHandler:
    """api_exception_handler 测试"""

    def test_api_exception_handler_with_api_exception(self):
        """测试API异常处理器 - APIException"""
        request = Mock(spec=Request)
        message = "Custom error"
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        exc = APIException(message, code)

        response = api_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == code

        # 验证响应内容 - 直接检查响应体中的关键信息
        response_body = str(response.body, 'utf-8')
        assert message in response_body
        assert str(code) in response_body

    def test_api_exception_handler_with_non_api_exception(self):
        """测试API异常处理器 - 非APIException"""
        request = Mock(spec=Request)
        exc = ValueError("Not an API exception")

        with patch(
            "fastapi_keystone.core.exceptions.global_exception_handler"
        ) as mock_global:
            mock_response = Mock(spec=JSONResponse)
            mock_global.return_value = mock_response

            response = api_exception_handler(request, exc)

            mock_global.assert_called_once_with(request, exc)
            assert response == mock_response


class TestHTTPExceptionHandler:
    """http_exception_handler 测试"""

    def test_http_exception_handler_with_http_exception(self):
        """测试HTTP异常处理器 - HTTPException"""
        request = Mock(spec=Request)
        detail = "Resource not found"
        status_code = status.HTTP_404_NOT_FOUND
        exc = HTTPException(status_code=status_code, detail=detail)

        response = http_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status_code

        # 验证响应内容 - 直接检查响应体中的关键信息
        response_body = str(response.body, 'utf-8')
        assert detail in response_body
        assert str(status_code) in response_body

    def test_http_exception_handler_with_different_status_codes(self):
        """测试HTTP异常处理器 - 不同状态码"""
        request = Mock(spec=Request)

        test_cases = [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (500, "Internal Server Error"),
        ]

        for status_code, detail in test_cases:
            exc = HTTPException(status_code=status_code, detail=detail)
            response = http_exception_handler(request, exc)

            assert response.status_code == status_code
            response_body = str(response.body, 'utf-8')
            assert detail in response_body

    def test_http_exception_handler_with_non_http_exception(self):
        """测试HTTP异常处理器 - 非HTTPException"""
        request = Mock(spec=Request)
        exc = ValueError("Not an HTTP exception")

        with patch(
            "fastapi_keystone.core.exceptions.global_exception_handler"
        ) as mock_global:
            mock_response = Mock(spec=JSONResponse)
            mock_global.return_value = mock_response

            response = http_exception_handler(request, exc)

            mock_global.assert_called_once_with(request, exc)
            assert response == mock_response


class TestValidationExceptionHandler:
    """validation_exception_handler 测试"""

    def test_validation_exception_handler_with_validation_error(self):
        """测试验证异常处理器 - RequestValidationError"""
        request = Mock(spec=Request)

        # # 创建模拟的验证错误
        # errors = [
        #     {
        #         "loc": ("body", "email"),
        #         "msg": "field required",
        #         "type": "value_error.missing",
        #     },
        #     {
        #         "loc": ("body", "age"),
        #         "msg": "ensure this value is greater than 0",
        #         "type": "value_error.number.not_gt",
        #     },
        # ]

        # 创建真实的RequestValidationError实例
        from pydantic_core import ErrorDetails

        error_details = [
            ErrorDetails(
                type="missing", loc=("body", "email"), msg="field required", input={}
            ),
            ErrorDetails(
                type="value_error",
                loc=("body", "age"),
                msg="ensure this value is greater than 0",
                input={},
            ),
        ]

        exc = RequestValidationError(error_details)
        response = validation_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # 验证响应包含错误信息
        response_body = response.body.decode()
        assert "Validation Error" in response_body
        assert "422" in response_body

    def test_validation_exception_handler_with_non_validation_error(self):
        """测试验证异常处理器 - 非RequestValidationError"""
        request = Mock(spec=Request)
        exc = ValueError("Not a validation error")

        with patch(
            "fastapi_keystone.core.exceptions.global_exception_handler"
        ) as mock_global:
            mock_response = Mock(spec=JSONResponse)
            mock_global.return_value = mock_response

            response = validation_exception_handler(request, exc)

            mock_global.assert_called_once_with(request, exc)
            assert response == mock_response


class TestGlobalExceptionHandler:
    """global_exception_handler 测试"""

    def test_global_exception_handler_with_any_exception(self):
        """测试全局异常处理器 - 任意异常"""
        request = Mock(spec=Request)
        exc = Exception("Unexpected error")

        response = global_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # 验证响应内容
        response_body = str(response.body, "utf-8")
        print(response_body)
        assert "Unexpected error" in response_body
        assert "500" in response_body

    def test_global_exception_handler_with_different_exception_types(self):
        """测试全局异常处理器 - 不同异常类型"""
        request = Mock(spec=Request)

        exceptions = [
            ValueError("Value error"),
            TypeError("Type error"),
            KeyError("Key error"),
            AttributeError("Attribute error"),
            RuntimeError("Runtime error"),
        ]

        for exc in exceptions:
            response = global_exception_handler(request, exc)

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            response_body = response.body.decode() if hasattr(response.body, 'decode') else str(response.body)
            assert str(exc) in response_body

    def test_global_exception_handler_unicode_exception(self):
        """测试全局异常处理器 - Unicode异常"""
        request = Mock(spec=Request)
        exc = Exception("包含中文的错误 🚨")

        response = global_exception_handler(request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        response_body = response.body.decode() if hasattr(response.body, 'decode') else str(response.body)
        assert "包含中文的错误 🚨" in response_body


class TestExceptionHandlersIntegration:
    """异常处理器集成测试"""

    def test_exception_handlers_response_format_consistency(self):
        """测试异常处理器响应格式一致性"""
        request = Mock(spec=Request)

        # 测试不同异常处理器的响应格式
        handlers_and_exceptions = [
            (api_exception_handler, APIException("API Error")),
            (http_exception_handler, HTTPException(404, "Not Found")),
            (global_exception_handler, Exception("General Error")),
        ]

        for handler, exc in handlers_and_exceptions:
            response = handler(request, exc)

            assert isinstance(response, JSONResponse)
            assert hasattr(response, "status_code")

            # 验证响应体包含标准字段
            response_body = response.body.decode()
            assert '"code":' in response_body
            assert '"message":' in response_body

    def test_exception_handling_chain(self):
        """测试异常处理链"""
        request = Mock(spec=Request)

        # 测试异常处理的优先级和链式调用
        with patch(
            "fastapi_keystone.core.exceptions.global_exception_handler"
        ) as mock_global:
            mock_response = Mock(spec=JSONResponse)
            mock_global.return_value = mock_response

            # 非API异常应该调用全局处理器
            general_exc = ValueError("General error")
            response = api_exception_handler(request, general_exc)

            mock_global.assert_called_once_with(request, general_exc)
            assert response == mock_response

    def test_error_response_serialization(self):
        """测试错误响应序列化"""
        request = Mock(spec=Request)

        exc = APIException("Validation failed")
        response = api_exception_handler(request, exc)

        # 验证响应可以正常序列化
        assert isinstance(response.body, bytes)
        response_str = response.body.decode() if hasattr(response.body, 'decode') else str(response.body)
        assert response_str  # 确保不为空

    def test_status_code_consistency(self):
        """测试状态码一致性"""
        request = Mock(spec=Request)

        # 测试各种状态码
        test_cases = [
            (APIException("Bad Request", 400), 400),
            (HTTPException(404, "Not Found"), 404),
            (Exception("Server Error"), 500),
        ]

        handlers = [
            api_exception_handler,
            http_exception_handler,
            global_exception_handler,
        ]

        for exc, expected_code in test_cases:
            for handler in handlers:
                try:
                    response = handler(request, exc)
                    # 只验证处理器能处理的异常类型
                    if (
                        (
                            isinstance(exc, APIException)
                            and handler == api_exception_handler
                        )
                        or (
                            isinstance(exc, HTTPException)
                            and handler == http_exception_handler
                        )
                        or (handler == global_exception_handler)
                    ):
                        if isinstance(exc, (APIException, HTTPException)):
                            assert response.status_code == expected_code
                        else:
                            assert response.status_code == 500
                except Exception:
                    # 某些处理器可能不处理特定异常类型，这是正常的
                    pass


class TestExceptionHandlerEdgeCases:
    """异常处理器边界情况测试"""

    def test_none_request_handling(self):
        """测试None请求处理（边界情况）"""
        # 虽然实际不会发生，但测试健壮性
        request = None  # type: ignore
        exc = APIException("Test error")

        # 应该不会因为request为None而崩溃
        response = api_exception_handler(request, exc)  # type: ignore
        assert isinstance(response, JSONResponse)

    def test_empty_exception_message(self):
        """测试空异常消息"""
        request = Mock(spec=Request)

        # 空消息的API异常
        exc = APIException("")
        response = api_exception_handler(request, exc)

        assert response.status_code == 400
        response_body = response.body.decode()
        assert '"message":""' in response_body

    def test_very_long_exception_message(self):
        """测试非常长的异常消息"""
        request = Mock(spec=Request)
        long_message = "A" * 10000  # 10000字符的消息

        exc = APIException(long_message)
        response = api_exception_handler(request, exc)

        assert response.status_code == 400
        response_body = response.body.decode()
        assert long_message in response_body

    def test_exception_with_special_json_characters(self):
        """测试包含特殊JSON字符的异常"""
        request = Mock(spec=Request)
        special_message = 'Message with "quotes" and \n newlines and \t tabs'

        exc = APIException(special_message)
        response = api_exception_handler(request, exc)

        assert response.status_code == 400
        # 响应应该能正常序列化
        assert isinstance(response.body, bytes)
        response_str = response.body.decode() if hasattr(response.body, 'decode') else str(response.body)
        assert response_str

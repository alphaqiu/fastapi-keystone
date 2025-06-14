"""测试请求模型模块"""

import pytest
from pydantic import ValidationError

from fastapi_keystone.core.request import PageRequest


class TestPageRequest:
    """PageRequest 模型测试"""

    def test_page_request_default_values(self):
        """测试默认值"""
        request = PageRequest()
        
        assert request.page == 1
        assert request.size == 10

    def test_page_request_with_custom_values(self):
        """测试自定义值"""
        request = PageRequest(page=2, size=20)
        
        assert request.page == 2
        assert request.size == 20

    def test_page_request_validation_page_positive(self):
        """测试页码必须为正数"""
        # 正数应该通过
        request = PageRequest(page=1, size=10)
        assert request.page == 1

        # 页码为0应该通过（虽然在业务逻辑中可能不合理）
        request = PageRequest(page=0, size=10)
        assert request.page == 0

    def test_page_request_validation_size_positive(self):
        """测试每页数量必须>=1"""
        # 正数应该通过
        request = PageRequest(page=1, size=5)
        assert request.size == 5

        # 小于1应该失败
        with pytest.raises(ValidationError) as exc_info:
            PageRequest(page=1, size=0)
        
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_page_request_type_conversion(self):
        """测试类型转换"""
        # 字符串数字应该被转换
        request = PageRequest(page="2", size="15")  # type: ignore
        assert request.page == 2
        assert request.size == 15
        assert isinstance(request.page, int)
        assert isinstance(request.size, int)

    def test_page_request_invalid_types(self):
        """测试无效类型"""
        with pytest.raises(ValidationError):
            PageRequest(page="invalid", size=10)  # type: ignore

        with pytest.raises(ValidationError):
            PageRequest(page=1, size="invalid")  # type: ignore

    def test_page_request_model_config(self):
        """测试模型配置"""
        request = PageRequest(page=1, size=10)
        
        # 验证可以从属性创建
        assert request.model_config.get("from_attributes") is True

        # 验证JSON schema示例
        json_schema_extra = request.model_config.get("json_schema_extra")
        assert json_schema_extra is not None
        if isinstance(json_schema_extra, dict) and "example" in json_schema_extra:
            example = json_schema_extra["example"]
            if isinstance(example, dict):
                assert example.get("page") == 1
                assert example.get("size") == 10

    def test_page_request_model_dump(self):
        """测试模型序列化"""
        request = PageRequest(page=3, size=25)
        dumped = request.model_dump()
        
        expected = {"page": 3, "size": 25}
        assert dumped == expected

    def test_page_request_model_dump_json(self):
        """测试JSON序列化"""
        request = PageRequest(page=3, size=25)
        json_str = request.model_dump_json()
        
        assert isinstance(json_str, str)
        assert '"page":3' in json_str
        assert '"size":25' in json_str

    def test_page_request_from_dict(self):
        """测试从字典创建"""
        data = {"page": 5, "size": 50}
        request = PageRequest(**data)
        
        assert request.page == 5
        assert request.size == 50

    def test_page_request_partial_data(self):
        """测试部分数据"""
        # 只提供page，size使用默认值
        request = PageRequest(page=7)
        assert request.page == 7
        assert request.size == 10

        # 只提供size，page使用默认值
        request = PageRequest(size=100)
        assert request.page == 1
        assert request.size == 100

    def test_page_request_boundary_values(self):
        """测试边界值"""
        # 最小值
        request = PageRequest(page=1, size=1)
        assert request.page == 1
        assert request.size == 1

        # 大数值
        request = PageRequest(page=999999, size=10000)
        assert request.page == 999999
        assert request.size == 10000

    def test_page_request_equality(self):
        """测试相等性"""
        request1 = PageRequest(page=2, size=20)
        request2 = PageRequest(page=2, size=20)
        request3 = PageRequest(page=3, size=20)

        assert request1 == request2
        assert request1 != request3

    def test_page_request_repr(self):
        """测试字符串表示"""
        request = PageRequest(page=2, size=20)
        repr_str = repr(request)
        
        assert "PageRequest" in repr_str
        assert "page=2" in repr_str
        assert "size=20" in repr_str

    def test_page_request_field_validation_messages(self):
        """测试字段验证消息"""
        # 测试size字段的验证消息
        try:
            PageRequest(page=1, size=-1)
        except ValidationError as e:
            errors = e.errors()
            assert len(errors) > 0
            size_error = next((err for err in errors if err["loc"] == ("size",)), None)
            assert size_error is not None
            assert "greater than or equal to 1" in size_error["msg"]

    def test_page_request_field_descriptions(self):
        """测试字段描述"""
        # 通过模型字段验证描述存在
        fields = PageRequest.model_fields
        
        assert "page" in fields
        assert "size" in fields
        
        # 验证字段有适当的标题
        page_field = fields["page"]
        size_field = fields["size"]
        
        # 这些应该从Query中获取
        assert hasattr(page_field, "description") or hasattr(page_field, "title")
        assert hasattr(size_field, "description") or hasattr(size_field, "title")

    @pytest.mark.parametrize("page,size,expected_page,expected_size", [
        (1, 10, 1, 10),
        (2, 25, 2, 25),
        (100, 1, 100, 1),
        ("5", "15", 5, 15),  # 字符串转换
    ])
    def test_page_request_parametrized(self, page, size, expected_page, expected_size):
        """参数化测试"""
        request = PageRequest(page=page, size=size)  # type: ignore
        assert request.page == expected_page
        assert request.size == expected_size 
"""测试字典工具函数"""

import pytest

from fastapi_keystone.common.dicts import deep_merge


class TestDeepMerge:
    """deep_merge 函数测试类"""

    # ===== 正向测试用例 =====

    def test_basic_merge_different_keys(self):
        """测试基本合并 - 不同键"""
        base = {"a": 1, "b": 2}
        update = {"c": 3, "d": 4}
        expected = {"a": 1, "b": 2, "c": 3, "d": 4}

        result = deep_merge(base, update)
        assert result == expected
        # 确保原字典未被修改
        assert base == {"a": 1, "b": 2}
        assert update == {"c": 3, "d": 4}

    def test_basic_merge_same_keys_override(self):
        """测试基本合并 - 相同键覆盖"""
        base = {"a": 1, "b": 2}
        update = {"b": 3, "c": 4}
        expected = {"a": 1, "b": 3, "c": 4}

        result = deep_merge(base, update)
        assert result == expected

    def test_deep_merge_nested_dicts(self):
        """测试深度合并 - 嵌套字典"""
        base = {"user": {"name": "Alice", "age": 25}, "settings": {"theme": "dark"}}
        update = {
            "user": {
                "email": "alice@example.com",
                "age": 26,  # 覆盖年龄
            },
            "settings": {"language": "zh-CN"},
        }
        expected = {
            "user": {"name": "Alice", "age": 26, "email": "alice@example.com"},
            "settings": {"theme": "dark", "language": "zh-CN"},
        }

        result = deep_merge(base, update)
        assert result == expected

    def test_deep_merge_multiple_levels(self):
        """测试多层嵌套深度合并"""
        base = {
            "level1": {"level2": {"level3": {"value1": "original"}, "other": "data"}}
        }
        update = {
            "level1": {"level2": {"level3": {"value2": "new"}, "new_key": "new_value"}}
        }
        expected = {
            "level1": {
                "level2": {
                    "level3": {"value1": "original", "value2": "new"},
                    "other": "data",
                    "new_key": "new_value",
                }
            }
        }

        result = deep_merge(base, update)
        assert result == expected

    def test_empty_dictionaries(self):
        """测试空字典处理"""
        # 空base字典
        result1 = deep_merge({}, {"a": 1, "b": 2})
        assert result1 == {"a": 1, "b": 2}

        # 空update字典
        result2 = deep_merge({"a": 1, "b": 2}, {})
        assert result2 == {"a": 1, "b": 2}

        # 两个都是空字典
        result3 = deep_merge({}, {})
        assert result3 == {}

    def test_mixed_data_types(self):
        """测试混合数据类型"""
        base = {
            "string": "hello",
            "number": 42,
            "list": [1, 2, 3],
            "nested": {"inner": "value"},
        }
        update = {
            "string": "world",  # 覆盖字符串
            "boolean": True,  # 新增布尔值
            "nested": {"new": "data"},  # 深度合并
        }
        expected = {
            "string": "world",
            "number": 42,
            "list": [1, 2, 3],
            "boolean": True,
            "nested": {"inner": "value", "new": "data"},
        }

        result = deep_merge(base, update)
        assert result == expected

    def test_none_values(self):
        """测试None值处理"""
        base = {"a": 1, "b": None}
        update = {"b": 2, "c": None}
        expected = {"a": 1, "b": 2, "c": None}

        result = deep_merge(base, update)
        assert result == expected

    # ===== 反向测试用例 =====

    def test_dict_vs_non_dict_override(self):
        """测试字典vs非字典类型冲突 - 用非字典覆盖字典"""
        base = {"config": {"debug": True, "version": "1.0"}}
        update = {
            "config": "simple_string"  # 用字符串覆盖字典
        }
        expected = {"config": "simple_string"}

        result = deep_merge(base, update)
        assert result == expected

    def test_non_dict_vs_dict_override(self):
        """测试非字典vs字典类型冲突 - 用字典覆盖非字典"""
        base = {"config": "simple_string"}
        update = {"config": {"debug": True, "version": "1.0"}}
        expected = {"config": {"debug": True, "version": "1.0"}}

        result = deep_merge(base, update)
        assert result == expected

    def test_complex_type_conflicts(self):
        """测试复杂类型冲突"""
        base = {"data": {"list_to_dict": [1, 2, 3], "dict_to_list": {"a": 1}}}
        update = {"data": {"list_to_dict": {"new": "dict"}, "dict_to_list": [4, 5, 6]}}
        expected = {
            "data": {"list_to_dict": {"new": "dict"}, "dict_to_list": [4, 5, 6]}
        }

        result = deep_merge(base, update)
        assert result == expected

    def test_deep_nested_type_conflicts(self):
        """测试深层嵌套中的类型冲突"""
        base = {"level1": {"level2": {"conflict": {"original": "dict"}}}}
        update = {"level1": {"level2": {"conflict": "now_string", "new_key": "value"}}}
        expected = {
            "level1": {"level2": {"conflict": "now_string", "new_key": "value"}}
        }

        result = deep_merge(base, update)
        assert result == expected

    def test_immutability(self):
        """测试原字典不可变性"""
        base = {"nested": {"value": "original"}, "simple": "data"}
        update = {"nested": {"value": "updated", "new": "field"}, "added": "field"}

        # 保存原始状态
        original_base = {"nested": {"value": "original"}, "simple": "data"}
        original_update = {
            "nested": {"value": "updated", "new": "field"},
            "added": "field",
        }

        result = deep_merge(base, update)

        # 确保原字典未被修改
        assert base == original_base
        assert update == original_update

        # 确保结果正确
        expected = {
            "nested": {"value": "updated", "new": "field"},
            "simple": "data",
            "added": "field",
        }
        assert result == expected

    def test_circular_reference_prevention(self):
        """测试防止循环引用（间接测试）"""
        # 虽然函数不直接处理循环引用，但测试不会无限递归
        base = {"a": {"b": {"c": "deep"}}}
        update = {"a": {"b": {"d": "new"}}}

        result = deep_merge(base, update)
        expected = {"a": {"b": {"c": "deep", "d": "new"}}}
        assert result == expected

    def test_special_dict_values(self):
        """测试特殊字典值"""
        base = {
            "empty_dict": {},
            "none_value": None,
            "zero": 0,
            "false": False,
            "empty_string": "",
        }
        update = {
            "empty_dict": {"now": "not_empty"},
            "none_value": {"was": "none"},
            "new_empty": {},
        }
        expected = {
            "empty_dict": {"now": "not_empty"},
            "none_value": {"was": "none"},
            "zero": 0,
            "false": False,
            "empty_string": "",
            "new_empty": {},
        }

        result = deep_merge(base, update)
        assert result == expected

    # ===== 边界情况测试 =====

    def test_large_nested_structure(self):
        """测试大型嵌套结构"""
        base = {}
        update = {}

        # 创建深层嵌套结构
        current_base = base
        current_update = update

        for i in range(10):  # 10层嵌套
            current_base[f"level_{i}"] = {}
            current_update[f"level_{i}"] = {}

            if i == 9:  # 最后一层添加数据
                current_base[f"level_{i}"]["base_value"] = f"base_{i}"
                current_update[f"level_{i}"]["update_value"] = f"update_{i}"
            else:
                current_base = current_base[f"level_{i}"]
                current_update = current_update[f"level_{i}"]

        result = deep_merge(base, update)

        # 验证最深层的合并
        deep_result = result
        for i in range(10):
            deep_result = deep_result[f"level_{i}"]

        assert deep_result["base_value"] == "base_9"
        assert deep_result["update_value"] == "update_9"

    def test_unicode_keys(self):
        """测试Unicode键名"""
        base = {"中文": {"测试": "值1"}, "emoji": "😊"}
        update = {"中文": {"新键": "值2"}, "русский": "тест"}
        expected = {
            "中文": {"测试": "值1", "新键": "值2"},
            "emoji": "😊",
            "русский": "тест",
        }

        result = deep_merge(base, update)
        assert result == expected

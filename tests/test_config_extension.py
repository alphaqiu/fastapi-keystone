"""
测试配置扩展机制
"""

import json
import tempfile
from pathlib import Path
from typing import Optional

import pytest
from pydantic import Field
from pydantic_settings import BaseSettings

from fastapi_keystone.config import load_config


class MockRedisConfig(BaseSettings):
    """测试用Redis配置"""

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    password: Optional[str] = Field(default=None)
    database: int = Field(default=0)
    enable: bool = Field(default=True)


class MockEmailConfig(BaseSettings):
    """测试用邮件配置"""

    smtp_host: str = Field()
    smtp_port: int = Field(default=587)
    username: str = Field()
    password: str = Field()


def create_test_config_file(config_data: dict) -> str:
    """创建临时配置文件"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f, indent=2)
        return f.name


class TestConfigExtension:
    """配置扩展机制测试"""

    def test_get_section_success(self):
        """测试成功获取配置段"""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8080},
            "logger": {"level": "info"},
            "databases": {
                "default": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "test",
                    "password": "test",
                    "database": "test",
                }
            },
            "redis": {
                "host": "redis.example.com",
                "port": 6380,
                "password": "secret",
                "database": 1,
                "enable": True,
            },
        }

        config_file = create_test_config_file(config_data)
        try:
            config = load_config(config_file)
            redis_config = config.get_section("redis", MockRedisConfig)

            assert redis_config is not None
            assert redis_config.host == "redis.example.com"
            assert redis_config.port == 6380
            assert redis_config.password == "secret"
            assert redis_config.database == 1
            assert redis_config.enable is True
        finally:
            Path(config_file).unlink()

    def test_get_section_not_found(self):
        """测试获取不存在的配置段"""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8080},
            "logger": {"level": "info"},
            "databases": {
                "default": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "test",
                    "password": "test",
                    "database": "test",
                }
            },
        }

        config_file = create_test_config_file(config_data)
        try:
            config = load_config(config_file)
            redis_config = config.get_section("redis", MockRedisConfig)

            assert redis_config is None
        finally:
            Path(config_file).unlink()

    def test_get_section_validation_error(self):
        """测试配置段数据验证错误"""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8080},
            "logger": {"level": "info"},
            "databases": {
                "default": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "test",
                    "password": "test",
                    "database": "test",
                }
            },
            "email": {
                "smtp_host": "smtp.example.com",
                # 缺少必需的username和password字段
                "smtp_port": 587,
            },
        }

        config_file = create_test_config_file(config_data)
        try:
            config = load_config(config_file)

            with pytest.raises(ValueError) as exc_info:
                config.get_section("email", MockEmailConfig)

            assert "Failed to parse config section 'email'" in str(exc_info.value)
        finally:
            Path(config_file).unlink()

    def test_section_caching(self):
        """测试配置段缓存机制"""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8080},
            "logger": {"level": "info"},
            "databases": {
                "default": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "test",
                    "password": "test",
                    "database": "test",
                }
            },
            "redis": {"host": "redis.example.com", "port": 6379},
        }

        config_file = create_test_config_file(config_data)
        try:
            config = load_config(config_file)

            # 第一次获取
            redis_config1 = config.get_section("redis", MockRedisConfig)
            # 第二次获取
            redis_config2 = config.get_section("redis", MockRedisConfig)

            # 应该是同一个对象（缓存生效）
            assert redis_config1 is redis_config2
            assert len(config._section_cache) == 1
        finally:
            Path(config_file).unlink()

    def test_clear_section_cache(self):
        """测试清除配置段缓存"""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8080},
            "logger": {"level": "info"},
            "databases": {
                "default": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "test",
                    "password": "test",
                    "database": "test",
                }
            },
            "redis": {"host": "redis.example.com", "port": 6379},
            "email": {
                "smtp_host": "smtp.example.com",
                "username": "test",
                "password": "test",
            },
        }

        config_file = create_test_config_file(config_data)
        try:
            config = load_config(config_file)

            # 加载两个配置段
            config.get_section("redis", MockRedisConfig)
            config.get_section("email", MockEmailConfig)
            assert len(config._section_cache) == 2

            # 清除特定配置段缓存
            config.clear_section_cache("redis")
            assert len(config._section_cache) == 1

            # 清除所有缓存
            config.clear_section_cache()
            assert len(config._section_cache) == 0
        finally:
            Path(config_file).unlink()

    def test_has_section(self):
        """测试检查配置段是否存在"""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8080},
            "logger": {"level": "info"},
            "databases": {
                "default": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "test",
                    "password": "test",
                    "database": "test",
                }
            },
            "redis": {"host": "redis.example.com", "port": 6379},
        }

        config_file = create_test_config_file(config_data)
        try:
            config = load_config(config_file)

            assert config.has_section("redis") is True
            assert config.has_section("email") is False
            assert config.has_section("nonexistent") is False
        finally:
            Path(config_file).unlink()

    def test_get_section_keys(self):
        """测试获取配置段键名列表"""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8080},
            "logger": {"level": "info"},
            "databases": {
                "default": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "test",
                    "password": "test",
                    "database": "test",
                }
            },
            "redis": {"host": "redis.example.com"},
            "email": {"smtp_host": "smtp.example.com"},
            "cache": {"type": "redis"},
        }

        config_file = create_test_config_file(config_data)
        try:
            config = load_config(config_file)

            section_keys = config.get_section_keys()

            # 应该包含扩展配置段，但不包含标准配置段
            assert "redis" in section_keys
            assert "email" in section_keys
            assert "cache" in section_keys
            assert "server" not in section_keys
            assert "logger" not in section_keys
            assert "databases" not in section_keys
        finally:
            Path(config_file).unlink()

    def test_default_values_in_extension(self):
        """测试扩展配置中的默认值"""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8080},
            "logger": {"level": "info"},
            "databases": {
                "default": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "test",
                    "password": "test",
                    "database": "test",
                }
            },
            "redis": {
                "host": "redis.example.com"
                # 其他字段使用默认值
            },
        }

        config_file = create_test_config_file(config_data)
        try:
            config = load_config(config_file)
            redis_config = config.get_section("redis", MockRedisConfig)

            assert redis_config is not None
            assert redis_config.host == "redis.example.com"
            assert redis_config.port == 6379  # 默认值
            assert redis_config.password is None  # 默认值
            assert redis_config.database == 0  # 默认值
            assert redis_config.enable is True  # 默认值
        finally:
            Path(config_file).unlink()

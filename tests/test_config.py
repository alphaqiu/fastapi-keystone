import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
from injector import Injector
from pydantic import ValidationError
from pydantic_settings import BaseSettings
from rich import print

from fastapi_keystone.config import Config, ConfigModule, load_config


@pytest.fixture
def temp_config_file():
    """创建临时配置文件的fixture"""

    def _create_config_file(config_data: Dict[str, Any]) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f, indent=2)
            return f.name

    return _create_config_file


@pytest.fixture
def sample_config_data():
    """示例配置数据"""
    return {
        "server": {
            "host": "192.168.1.100",
            "port": 9000,
            "reload": True,
            "run_mode": "test",
            "workers": 2,
            "title": "Test API",
            "description": "Test Description",
            "version": "1.0.0",
        },
        "logger": {
            "level": "debug",
            "format": "custom format",
            "file": "test.log",
            "console": False,
        },
        "databases": {
            "default": {
                "enable": True,
                "host": "db.example.com",
                "port": 3306,
                "user": "testuser",
                "password": "testpass",
                "database": "testdb",
            },
            "cache": {
                "enable": False,
                "host": "cache.example.com",
                "port": 6379,
                "user": "cacheuser",
                "password": "cachepass",
                "database": "cachedb",
            },
        },
    }


@pytest.mark.asyncio
async def test_load_config():
    """测试基本配置加载功能"""
    # __file__ = ./fastapi-keystone/tests/test_config.py
    # Path(__file__).parent = ./fastapi-keystone/tests
    # Path(__file__).parent.parent = ./fastapi-keystone
    example_config_path = Path(__file__).parent.parent / "config.example.json"
    print(example_config_path)
    config: Config = load_config(str(example_config_path))
    assert config is not None
    assert config.server.host == "0.0.0.0"
    assert config.server.port == 8080
    assert config.server.run_mode == "dev"
    assert len(config.databases.keys()) > 1

    print(config)


@pytest.mark.asyncio
async def test_config_module():
    """测试ConfigModule的依赖注入功能"""
    example_config_path = Path(__file__).parent.parent / "config.example.json"
    print(example_config_path)
    injector = Injector([ConfigModule(config_path=str(example_config_path))])
    config: Config = injector.get(Config)
    assert config is not None
    assert config.server.host == "0.0.0.0"
    assert config.server.port == 8080
    assert config.server.run_mode == "dev"
    assert len(config.databases.keys()) > 1
    config2: Config = injector.get(Config)
    assert id(config) == id(config2)


class TestConfigPriority:
    """测试配置加载的优先级"""

    def test_config_file_basic_loading(self, temp_config_file, sample_config_data):
        """测试基本的配置文件加载"""
        config_path = temp_config_file(sample_config_data)
        try:
            config = load_config(config_path)

            # 验证服务器配置
            assert config.server.host == "192.168.1.100"
            assert config.server.port == 9000
            assert config.server.reload == True
            assert config.server.run_mode == "test"
            assert config.server.workers == 2
            assert config.server.title == "Test API"

            # 验证日志配置
            assert config.logger.level == "debug"
            assert config.logger.format == "custom format"
            assert config.logger.file == "test.log"
            assert config.logger.console == False

            # 验证数据库配置
            default_db = config.databases["default"]
            assert default_db is not None
            assert default_db.host == "db.example.com"
            assert default_db.port == 3306
            assert default_db.user == "testuser"
            cache_db = config.databases["cache"]
            assert cache_db is not None
            assert cache_db.enable == False

        finally:
            os.unlink(config_path)

    def test_config_file_basic_loading_yaml(self, temp_config_file, sample_config_data):
        """测试YAML配置文件加载"""
        # 生成yaml文件
        import yaml

        yaml_path = temp_config_file(sample_config_data).replace(".json", ".yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(sample_config_data, f, allow_unicode=True)
        try:
            config = load_config(yaml_path)
            assert config.server.host == sample_config_data["server"]["host"]
            assert config.server.port == sample_config_data["server"]["port"]
            assert config.logger.level == sample_config_data["logger"]["level"]
            default_db = config.databases["default"]
            assert default_db is not None
            assert default_db.host == sample_config_data["databases"]["default"]["host"]
        finally:
            os.unlink(yaml_path)

    def test_environment_variable_override(
        self, temp_config_file, sample_config_data, monkeypatch
    ):
        """测试环境变量覆盖配置文件"""
        config_path = temp_config_file(sample_config_data)

        try:
            # 清理可能存在的.env文件影响，只使用环境变量
            monkeypatch.delenv("ENV_FILE", raising=False)

            # 设置环境变量（需要匹配Pydantic Settings的格式）
            monkeypatch.setenv("SERVER__HOST", "env.example.com")
            monkeypatch.setenv("SERVER__PORT", "8888")
            monkeypatch.setenv("LOGGER__LEVEL", "error")

            # 使用没有配置文件的方式加载，只依赖环境变量
            config = load_config("nonexistent.json")

            # 验证环境变量生效
            assert config.server.host == "env.example.com"  # 被环境变量覆盖
            assert config.server.port == 8888  # 被环境变量覆盖
            assert config.logger.level == "error"  # 被环境变量覆盖

            # 验证其他字段使用默认值
            assert config.server.reload == False  # 默认值
            assert config.server.run_mode == "dev"  # 默认值

        finally:
            os.unlink(config_path)

    def test_parameter_override(
        self, temp_config_file, sample_config_data, monkeypatch
    ):
        """测试传入参数覆盖配置文件和环境变量"""
        config_path = temp_config_file(sample_config_data)

        try:
            # 设置环境变量
            monkeypatch.setenv("SERVER__HOST", "env.example.com")
            monkeypatch.setenv("LOGGER__LEVEL", "error")

            # 传入参数覆盖
            override_params = {
                "server": {
                    "host": "param.example.com",  # 应该覆盖环境变量和配置文件
                    "port": 7777,  # 应该覆盖配置文件
                    "title": "Param Title",  # 应该覆盖配置文件
                },
                "logger": {
                    "level": "warning",  # 应该覆盖环境变量和配置文件
                    "console": True,  # 应该覆盖配置文件
                },
            }

            config = load_config(config_path, **override_params)

            # 验证参数覆盖了环境变量和配置文件
            assert config.server.host == "param.example.com"  # 参数覆盖
            assert config.server.port == 7777  # 参数覆盖
            assert config.server.title == "Param Title"  # 参数覆盖
            assert config.server.reload == True  # 配置文件值，未被覆盖
            assert config.logger.level == "warning"  # 参数覆盖
            assert config.logger.console == True  # 参数覆盖
            assert config.logger.format == "custom format"  # 配置文件值，未被覆盖

        finally:
            os.unlink(config_path)

    def test_default_values_when_no_config(self, monkeypatch):
        """测试没有配置文件时使用默认值"""
        # 清理可能存在的环境变量
        for key in ["SERVER__HOST", "SERVER__PORT", "LOGGER__LEVEL"]:
            monkeypatch.delenv(key, raising=False)

        config = load_config("nonexistent.json")

        # 验证使用了默认值
        assert config.server.host == "127.0.0.1"  # 默认值
        assert config.server.port == 8080  # 默认值
        assert config.server.reload == False  # 默认值
        assert config.server.run_mode == "dev"  # 默认值
        assert config.server.workers == 1  # 默认值
        assert config.server.title == "FastAPI Keystone"  # 默认值
        assert config.logger.level == "info"  # 默认值
        assert config.logger.console == True  # 默认值

    def test_partial_configuration_override(self, temp_config_file, monkeypatch):
        """测试部分配置覆盖"""
        # 只配置部分字段的配置文件
        partial_config = {
            "server": {
                "host": "partial.example.com",
                "port": 3000,
                # 其他字段缺失，应该使用默认值
            },
            "databases": {
                "default": {
                    "enable": True,
                    "host": "partial-db.example.com",
                    "port": 5432,
                    "user": "postgres",
                    "password": "postgres",
                    "database": "fastapi_keystone",
                }
            },
            # logger配置完全缺失，应该使用默认值
        }

        config_path = temp_config_file(partial_config)

        try:
            # 设置部分环境变量
            monkeypatch.setenv("LOGGER__LEVEL", "debug")

            config = load_config(config_path)

            # 验证配置文件值
            assert config.server.host == "partial.example.com"
            assert config.server.port == 3000

            # 验证默认值
            assert config.server.reload == False  # 默认值
            assert config.server.workers == 1  # 默认值
            assert config.server.title == "FastAPI Keystone"  # 默认值

            # 验证环境变量覆盖默认值
            assert config.logger.level == "debug"  # 环境变量

            # 验证其他logger字段使用默认值
            assert config.logger.console == True  # 默认值
            assert config.logger.file is None  # 默认值

        finally:
            os.unlink(config_path)


class TestConfigFileHandling:
    """测试配置文件处理的各种情况"""

    def test_nonexistent_config_file(self):
        """测试配置文件不存在的情况"""
        # 不应该抛出异常，应该使用默认配置
        config = load_config("definitely_nonexistent_file.json")
        assert config is not None
        assert config.server.host == "127.0.0.1"  # 默认值

    def test_unsupported_file_format(self, temp_config_file):
        """测试不支持的文件格式"""
        # 创建一个.ini文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write("[server]\nhost = test.com\n")
            ini_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported config file type"):
                load_config(ini_path)
        finally:
            os.unlink(ini_path)

    def test_invalid_json_format(self):
        """测试无效的JSON格式"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"server": {"host": "test.com",}}')  # 无效JSON（多余的逗号）
            invalid_json_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                load_config(invalid_json_path)
        finally:
            os.unlink(invalid_json_path)

    def test_empty_json_file(self, temp_config_file):
        """测试空的JSON文件"""
        config_path = temp_config_file({})

        try:
            # 空的JSON应该能够加载，使用默认配置
            config = load_config(config_path)
            assert config is not None
            assert config.server.host == "127.0.0.1"  # 默认值
            assert config.databases["default"] is not None  # 默认数据库配置
        finally:
            os.unlink(config_path)


class TestConfigValidation:
    """测试配置验证"""

    def test_database_default_required(self, temp_config_file):
        """测试数据库配置必须包含default条目"""
        invalid_config = {
            "server": {"host": "test.com"},
            "databases": {
                "cache": {
                    "enable": True,
                    "host": "cache.com",
                    "port": 6379,
                    "user": "user",
                    "password": "pass",
                    "database": "cache",
                }
                # 缺少required的"default"条目
            },
        }

        config_path = temp_config_file(invalid_config)

        try:
            with pytest.raises(ValidationError) as exc_info:
                load_config(config_path)
            assert "default" in str(exc_info.value)
        finally:
            os.unlink(config_path)

    def test_type_validation_and_conversion(self, temp_config_file):
        """测试数据类型验证和自动转换"""
        config_with_types = {
            "server": {
                "host": "test.com",
                "port": "9000",  # 字符串，应该转换为整数
                "reload": "true",  # 字符串，应该转换为布尔值
                "workers": "2",  # 字符串，应该转换为整数
            },
            "databases": {
                "default": {
                    "enable": "false",  # 字符串，应该转换为布尔值
                    "host": "db.com",
                    "port": "5432",  # 字符串，应该转换为整数
                    "user": "user",
                    "password": "pass",
                    "database": "db",
                }
            },
        }

        config_path = temp_config_file(config_with_types)

        try:
            config = load_config(config_path)

            # 验证类型转换
            assert isinstance(config.server.port, int)
            assert config.server.port == 9000
            assert isinstance(config.server.reload, bool)
            assert config.server.reload == True
            assert isinstance(config.server.workers, int)
            assert config.server.workers == 2
            default_db = config.databases["default"]
            assert default_db is not None
            assert isinstance(default_db.enable, bool)
            assert default_db.enable == False
            assert isinstance(default_db.port, int)
            assert default_db.port == 5432

        finally:
            os.unlink(config_path)

    def test_invalid_worker_count(self, temp_config_file):
        """测试无效的worker数量（必须>=1）"""
        invalid_config = {
            "server": {"workers": 0},  # 无效值，必须>=1
            "databases": {
                "default": {
                    "enable": True,
                    "host": "db.com",
                    "port": 5432,
                    "user": "user",
                    "password": "pass",
                    "database": "db",
                }
            },
        }

        config_path = temp_config_file(invalid_config)

        try:
            with pytest.raises(ValidationError) as exc_info:
                load_config(config_path)
            assert "greater than or equal to 1" in str(exc_info.value)
        finally:
            os.unlink(config_path)


class TestConfigExtensions:
    """测试配置扩展功能"""

    def test_extra_fields_allowed(self, temp_config_file):
        """测试允许额外字段（extra='allow'）"""
        config_with_extra = {
            "server": {
                "host": "test.com",
                "custom_field": "custom_value",  # 额外字段
            },
            "logger": {
                "level": "info",
                "extra_logger_field": 123,  # 额外字段
            },
            "databases": {
                "default": {
                    "enable": True,
                    "host": "db.com",
                    "port": 5432,
                    "user": "user",
                    "password": "pass",
                    "database": "db",
                    "extra_db_field": ["list", "value"],  # 额外字段
                }
            },
            "custom_section": {  # 完全自定义的配置段
                "key1": "value1",
                "key2": 42,
                "nested": {"inner": "value"},
            },
        }

        config_path = temp_config_file(config_with_extra)

        try:
            config = load_config(config_path)

            # 验证基本配置正常加载
            assert config.server.host == "test.com"
            assert config.logger.level == "info"

            # 验证额外字段存在
            assert hasattr(config, "model_extra")
            assert config.model_extra is not None
            assert "custom_section" in config.model_extra

            # 验证自定义配置段的数据
            custom_section = config.model_extra["custom_section"]
            assert custom_section["key1"] == "value1"
            assert custom_section["key2"] == 42
            assert custom_section["nested"]["inner"] == "value"

        finally:
            os.unlink(config_path)


@pytest.mark.parametrize(
    "host,port,expected_host,expected_port",
    [
        ("127.0.0.1", 8080, "127.0.0.1", 8080),
        ("0.0.0.0", 3000, "0.0.0.0", 3000),
        ("localhost", 9999, "localhost", 9999),
    ],
)
def test_server_config_parametrized(
    temp_config_file, host, port, expected_host, expected_port
):
    """参数化测试服务器配置"""
    config_data = {
        "server": {"host": host, "port": port},
        "databases": {
            "default": {
                "enable": True,
                "host": "db.com",
                "port": 5432,
                "user": "user",
                "password": "pass",
                "database": "db",
            }
        },
    }

    config_path = temp_config_file(config_data)

    try:
        config = load_config(config_path)
        assert config.server.host == expected_host
        assert config.server.port == expected_port
    finally:
        os.unlink(config_path)


def test_deep_merge_functionality(temp_config_file):
    """测试深度合并功能"""
    base_config = {
        "server": {"host": "base.com", "port": 8000, "title": "Base Title"},
        "databases": {
            "default": {
                "enable": True,
                "host": "base-db.com",
                "port": 5432,
                "user": "baseuser",
                "password": "basepass",
                "database": "basedb",
            }
        },
    }

    config_path = temp_config_file(base_config)

    try:
        # 传入部分参数进行深度合并
        override_params = {
            "server": {
                "host": "override.com",  # 覆盖
                "description": "New Description",  # 新增
                # port和title保持原值
            },
            "databases": {
                "default": {
                    "password": "newpass",  # 覆盖
                    "database": "newdb",  # 覆盖
                    # 其他字段保持原值
                }
            },
        }

        config = load_config(config_path, **override_params)

        # 验证覆盖的字段
        assert config.server.host == "override.com"
        default_db = config.databases["default"]
        assert default_db is not None
        assert default_db.password == "newpass"
        assert default_db.database == "newdb"

        # 验证保持的字段
        assert config.server.port == 8000
        assert config.server.title == "Base Title"
        assert default_db.host == "base-db.com"
        assert default_db.user == "baseuser"

        # 验证新增的字段
        assert config.server.description == "New Description"

    finally:
        os.unlink(config_path)


def test_database_config_driver_and_dsn():
    from fastapi_keystone.config import DatabaseConfig

    # PostgreSQL
    cfg = DatabaseConfig(driver="postgresql+asyncpg", host="localhost", port=5432, user="u", password="p", database="d")
    assert cfg.dsn().startswith("postgresql+asyncpg://u:p@localhost:5432/d")
    # MySQL
    cfg = DatabaseConfig(driver="mysql+aiomysql", host="127.0.0.1", port=3306, user="u", password="p", database="d")
    assert cfg.dsn().startswith("mysql+aiomysql://u:p@127.0.0.1:3306/d")
    # SQLite file
    cfg = DatabaseConfig(driver="sqlite+aiosqlite", host="file", database="/tmp/test.db")
    assert cfg.dsn() == "sqlite+aiosqlite:////tmp/test.db"
    # SQLite memory
    cfg = DatabaseConfig(driver="sqlite+aiosqlite", host="memory", database="irrelevant")
    assert cfg.dsn() == "sqlite+aiosqlite:///:memory:"


def test_database_config_extra_field():
    from fastapi_keystone.config import DatabaseConfig
    cfg = DatabaseConfig(extra={"foo": "bar"})
    assert cfg.extra["foo"] == "bar"


class RedisConfig(BaseSettings):
    host: str
    port: int


def test_config_get_section_and_keys():
    from fastapi_keystone.config import Config

    # 构造带自定义section的Config
    config = Config.model_validate({
        "server": {},
        "logger": {},
        "databases": {"default": {}},
        "redis": {"host": "localhost", "port": 6379},
        "custom": {"foo": 1},
    })
    # get_section_keys
    keys = config.get_section_keys()
    assert "redis" in keys and "custom" in keys
    # has_section
    assert config.has_section("redis")
    # get_section
    redis_cfg = config.get_section("redis", RedisConfig)
    assert redis_cfg is not None and redis_cfg.host == "localhost"
    # 缓存命中
    redis_cfg2 = config.get_section("redis", RedisConfig)
    assert redis_cfg2 is redis_cfg
    # 清除缓存
    config.clear_section_cache("redis")
    assert config.get_section("redis", RedisConfig) is not None

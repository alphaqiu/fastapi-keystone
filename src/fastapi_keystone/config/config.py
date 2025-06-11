"""
FastAPI-Keystone Configuration System
====================================

This module defines the core configuration structure for FastAPI-Keystone, supporting multi-environment, layered, and extensible configuration management.

Key features:
- Supports JSON, YAML, and environment variable loading
- Multi-tenant database configuration
- Extensible custom sections (e.g., redis, oss, third-party services)
- All configuration is based on Pydantic v2 for type safety and validation
- Use get_section to dynamically extract custom config sections

Usage Example:
--------------

.. code-block:: python

    from fastapi_keystone.config.config import load_config, Config
    from pydantic import BaseSettings

    class RedisConfig(BaseSettings):
        host: str = "localhost"
        port: int = 6379

    config = load_config("config.yaml")
    redis_cfg = config.get_section("redis", RedisConfig)
    if redis_cfg:
        print(redis_cfg.host, redis_cfg.port)

Custom Extension Config:
-----------------------

You can add custom sections directly in config.json/yaml, for example:

.. code-block:: yaml

    server:
      host: 0.0.0.0
      port: 8000
    redis:
      host: redis.local
      port: 6380
    oss:
      endpoint: oss-cn-shanghai.aliyuncs.com
      access_key: ...

Then retrieve dynamically via get_section("redis", RedisConfig).

See below for detailed field explanations in each config class.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

import yaml
from pydantic import Field, RootModel, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from fastapi_keystone.common import deep_merge

_DEFAULT_CONFIG_PATH = "config.json"

# TypeVar for generic config section
T = TypeVar("T", bound=BaseSettings)


class RunMode(str, Enum):
    """
    Enum for application run mode.

    Attributes:
        DEV: Development environment
        TEST: Test environment
        STG: Staging environment
        PROD: Production environment
    """

    DEV = "dev"
    TEST = "test"
    STG = "stg"
    PROD = "prod"


class ServerConfig(BaseSettings):
    """
    Server base configuration.

    Supports loading from environment variables, JSON, or YAML files.

    Attributes:
        host (str): Listen address, default 127.0.0.1
        port (int): Listen port, default 8080
        reload (bool): Enable auto-reload, recommended only for development
        run_mode (RunMode): Run mode, dev/test/stg/prod
        workers (int): Worker process count, only effective when starting uvicorn internally
        title (str): API documentation title
        description (str): API documentation description
        version (str): API version
        tenant_enabled (bool): Enable multi-tenancy
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    host: str = Field(default="127.0.0.1", description="Listen address")
    port: int = Field(default=8080, description="Listen port")
    reload: bool = Field(
        default=False,
        description="Enable auto-reload, recommended only for development",
    )
    run_mode: RunMode = Field(
        default=RunMode.DEV,
        description="Run mode, dev, test, stg, prod, respectively corresponding to development, test, staging, production",
    )
    workers: int = Field(
        default=1,
        description="Worker process count, this parameter only affects when starting uvicorn internally",
        ge=1,
    )
    title: str = Field(
        default="FastAPI Keystone", description="API documentation title"
    )
    description: str = Field(
        default="FastAPI Keystone", description="API documentation description"
    )
    version: str = Field(default="0.0.1", description="API version")
    tenant_enabled: bool = Field(default=False, description="Enable multi-tenancy")


class LoggerConfig(BaseSettings):
    """
    Logger configuration.

    Supports loading from environment variables, JSON, or YAML files.

    Attributes:
        level (str): Log level, default info
        format (str): Log format string
        file (Optional[str]): Log file path, if None, do not write to file
        console (bool): Output to console
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    level: str = Field(default="info", description="Log level")
    format: str = Field(
        default=(
            "%(asctime)s.%(msecs)03d |%(levelname)s| %(name)s.%(funcName)s"
            ":%(lineno)d |logmsg| %(message)s"
        ),
        description="Log format string",
    )
    file: Optional[str] = Field(
        default=None,
        description="Log file path, if None, do not write to file",
        examples=["logs/app.log"],
    )
    console: bool = Field(default=True, description="Output to console")


class DatabaseConfig(BaseSettings):
    """
    Single database configuration.

    Supported database types:

    - PostgreSQL: ``postgresql+asyncpg://...``, requires ``asyncpg``
    - MySQL: ``mysql+aiomysql://...``, requires ``aiomysql``
    - SQLite: ``sqlite+aiosqlite://...``, requires ``aiosqlite``

    See driver field for details.

    Reference:
    - `SQLAlchemy Docs - Database URLs <https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls>`_
    - `SQLAlchemy Docs - Asyncio Support <https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html>`_
    - `FastAPI Docs - SQL (Relational) Databases <https://fastapi.tiangolo.com/advanced/sql-databases/>`_

    Attributes:
        enable (bool): Whether to enable this database config
        driver (str): Database driver, supports postgresql+asyncpg, mysql+aiomysql, sqlite+aiosqlite
        host (str): Database host
        port (int): Database port
        user (str): Username
        password (str): Password
        database (str): Database name, if using sqlite, this is the file path
        echo (bool): Print SQL logs
        pool_size (int): Connection pool size
        max_overflow (int): Max overflow connections
        pool_timeout (int): Connection timeout (seconds)
        extra (Dict[str, Any]): Other SQLAlchemy supported parameters
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    enable: bool = Field(
        default=True, description="Whether to enable this database config"
    )
    driver: str = Field(default="postgresql+asyncpg", description="Database driver")
    host: str = Field(default="127.0.0.1", description="Database host")
    port: int = Field(default=5432, description="Database port")
    user: str = Field(default="postgres", description="Username")
    password: str = Field(default="postgres", description="Password")
    database: str = Field(
        default="fastapi_keystone",
        description="Database name, if using sqlite, this is the file path",
    )
    echo: bool = Field(default=False, description="Print SQL logs")
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")
    pool_timeout: int = Field(default=10, description="Connection timeout (seconds)")
    extra: Dict[str, Any] = Field(
        default_factory=dict, description="Other SQLAlchemy supported parameters"
    )

    def dsn(self) -> str:
        """
        Generate a SQLAlchemy-compatible DSN string.

        Returns:
            str: Database connection string
        """
        driver = self.driver.strip().lower()
        if driver == "sqlite+aiosqlite" and self.host.strip() == "file":
            return f"{self.driver}:///{self.database}"
        elif driver == "sqlite+aiosqlite" and self.host.strip() == "memory":
            return f"{self.driver}:///:memory:"

        return (
            f"{driver}://{self.user}:{self.password}@{self.host}:"
            f"{self.port}/{self.database}"
        )


_DATABASE_ITEM = TypeVar("_DATABASE_ITEM", bound=Dict[str, DatabaseConfig])


class DatabasesConfig(RootModel[_DATABASE_ITEM]):
    """
    Multi-database configuration, supports multiple named databases.

    Must include a default database config.

    Attributes:
        root (Dict[str, DatabaseConfig]): Database config dict, key is database name
    """

    @field_validator("root")
    @classmethod
    def must_have_default(cls, v: _DATABASE_ITEM) -> _DATABASE_ITEM:
        if "default" not in v:
            raise ValueError("The 'databases' config must contain a 'default' entry.")
        return v

    def __getitem__(self, item: str) -> Optional[DatabaseConfig]:
        return self.root.get(item)

    def keys(self):
        return self.root.keys()

    def values(self):
        return self.root.values()

    def items(self):
        return self.root.items()


class Config(BaseSettings):
    """
    FastAPI-Keystone main configuration object.

    Supports standard fields (server, logger, databases) and arbitrary custom extension fields.

    Attributes:
        server (ServerConfig): Server config
        logger (LoggerConfig): Logger config
        databases (DatabasesConfig): Multi-database config
        _section_cache (Dict[str, Any]): Section cache (private)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    server: ServerConfig = Field(
        default_factory=ServerConfig, description="Server config"
    )
    logger: LoggerConfig = Field(
        default_factory=LoggerConfig, description="Logger config"
    )
    databases: DatabasesConfig = Field(
        default_factory=lambda: DatabasesConfig({"default": DatabaseConfig()}),
        description="Multi-database config",
    )

    # 私有缓存字典，用于缓存已解析的配置段
    _section_cache: Dict[str, Any] = {}

    def get_section(self, key: str, model_type: Type[T]) -> Optional[T]:
        """
        Extract a custom extension config section and parse as the given Pydantic type.

        Args:
            key (str): Section key (e.g. 'redis', 'oss')
            model_type (Type[T]): Target Pydantic model type

        Returns:
            Optional[T]: Parsed config object, or None if not present

        Raises:
            ValidationError: If config data format is invalid

        Example:
            >>> class RedisConfig(BaseSettings):
            ...     host: str = "localhost"
            ...     port: int = 6379
            >>> config = load_config()
            >>> redis_config = config.get_section('redis', RedisConfig)
        """
        # 生成缓存键
        cache_key = f"{key}:{model_type.__name__}"

        # 检查缓存
        if cache_key in self._section_cache:
            return self._section_cache[cache_key]

        # 获取额外字段数据
        extra_data = self.model_extra
        if not extra_data or key not in extra_data:
            return None

        try:
            # 提取指定key的配置数据
            section_data = extra_data[key]

            # 使用Pydantic模型验证并创建配置对象
            config_instance = model_type.model_validate(section_data)

            # 缓存结果
            self._section_cache[cache_key] = config_instance

            return config_instance

        except ValidationError as e:
            # 重新抛出验证错误，但添加上下文信息
            raise ValueError(
                f"Failed to parse config section '{key}' as {model_type.__name__}: {str(e)}"
            ) from e
        except Exception as e:
            # 处理其他异常
            raise ValueError(
                f"Error processing config section '{key}': {str(e)}"
            ) from e

    def clear_section_cache(self, key: Optional[str] = None) -> None:
        """
        Clear the section cache.

        Args:
            key (Optional[str]): Section key to clear, if None clear all
        """
        if key is None:
            self._section_cache.clear()
        else:
            # 清除指定key相关的所有缓存
            keys_to_remove = [
                cache_key
                for cache_key in self._section_cache
                if cache_key.startswith(f"{key}:")
            ]
            for cache_key in keys_to_remove:
                del self._section_cache[cache_key]

    def has_section(self, key: str) -> bool:
        """
        Check if a custom extension config section exists.

        Args:
            key (str): Section key

        Returns:
            bool: True if section exists, else False
        """
        extra_data = self.model_extra
        return extra_data is not None and key in extra_data

    def get_section_keys(self) -> list[str]:
        """
        Get all available custom extension section keys.

        Returns:
            list[str]: List of section keys
        """
        extra_data = self.model_extra
        if not extra_data:
            return []

        # 排除已知的标准配置字段
        standard_fields = {"server", "logger", "databases"}
        return [key for key in extra_data.keys() if key not in standard_fields]


def load_config(config_path: str = _DEFAULT_CONFIG_PATH, **kwargs) -> Config:
    """
    Load configuration file, supports JSON, YAML, and environment variables.

    Args:
        config_path (str): Path to config file, supports .json/.yaml/.yml
        **kwargs: Extra parameters, will override file content

    Returns:
        Config: Parsed config object

    Raises:
        ValueError: If file type is not supported
    """
    config_file_path = Path(config_path)
    if not config_file_path.exists():
        # 如果没有指定配置文件，尝试从默认 .env 文件加载
        # 同时也会从环境变量加载
        # 最后用传入的参数覆盖
        config = Config(**kwargs)
        return config

    if config_file_path.suffix == ".json":
        # 从 JSON 文件加载
        config_data = {}
        with open(config_file_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        config_data = deep_merge(config_data, kwargs)
        config = Config.model_validate(config_data)
        return config

    if config_file_path.suffix in {".yaml", ".yml"}:
        # 从 YAML 文件加载
        config_data = {}
        with open(config_file_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        config_data = deep_merge(config_data, kwargs)
        config = Config.model_validate(config_data)
        return config

    raise ValueError(f"Unsupported config file type: {config_file_path.suffix}")

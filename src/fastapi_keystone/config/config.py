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
    DEV = "dev"
    TEST = "test"
    STG = "stg"
    PROD = "prod"


class ServerConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    # 服务器配置
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8080)
    reload: bool = Field(default=False)
    run_mode: RunMode = Field(
        default=RunMode.DEV,
        description="运行模式, dev, test, stg, prod, 分别对应开发, 测试, 预发布, 生产",
    )
    workers: int = Field(
        default=1,
        description="工作进程数, 这个参数只影响在程序内部启动uvicorn时生效",
        ge=1,
    )
    title: str = Field(default="FastAPI Keystone")
    description: str = Field(default="FastAPI Keystone")
    version: str = Field(default="0.0.1")
    tenant_enabled: bool = Field(default=False)


class LoggerConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    # 日志配置
    level: str = Field(default="info")
    format: str = Field(
        default=(
            "%(asctime)s.%(msecs)03d |%(levelname)s| %(name)s.%(funcName)s"
            ":%(lineno)d |logmsg| %(message)s"
        )
    )
    file: Optional[str] = Field(
        default=None,
        description="日志文件路径, 如果为空则不写入文件",
        examples=["logs/app.log"],
    )
    console: bool = Field(default=True)


class DatabaseConfig(BaseSettings):
    """
    数据库配置。

    支持的数据库类型：

    - PostgreSQL: ``postgresql+asyncpg://...``，需安装 ``asyncpg``
    - MySQL: ``mysql+aiomysql://...``，需安装 ``aiomysql``
    - SQLite: ``sqlite+aiosqlite://...``，需安装 ``aiosqlite``

    参考文档：

    - `SQLAlchemy 官方文档 - Database URLs <https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls>`_
    - `SQLAlchemy 官方文档 - Asyncio Support <https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html>`_
    - `FastAPI 官方文档 - SQL (Relational) Databases <https://fastapi.tiangolo.com/advanced/sql-databases/>`_
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    # 数据库配置
    enable: bool = Field(default=True)
    driver: str = Field(default="postgresql+asyncpg")
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=5432)
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")
    database: str = Field(default="fastapi_keystone")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=20)
    max_overflow: int = Field(default=10)
    pool_timeout: int = Field(default=10)
    extra: Dict[str, Any] = Field(default_factory=dict)

    def dsn(self) -> str:
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
    """数据库配置，支持多个数据库，默认使用default数据库，default 数据库配置必须存在

    Pydantic v1: 可以在 BaseModel 里用 __root__ 字段实现根模型。
    Pydantic v2：必须用 pydantic.RootModel，不能在 BaseModel 里用 __root__ 字段，
    否则会报你遇到的错误。
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
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    server: ServerConfig = Field(default_factory=ServerConfig)
    logger: LoggerConfig = Field(default_factory=LoggerConfig)
    databases: DatabasesConfig = Field(
        default_factory=lambda: DatabasesConfig({"default": DatabaseConfig()})
    )

    # 私有缓存字典，用于缓存已解析的配置段
    _section_cache: Dict[str, Any] = {}

    def get_section(self, key: str, model_type: Type[T]) -> Optional[T]:
        """
        从配置的extra字段中提取指定key的配置，并解析为指定的Pydantic类型

        Args:
            key: 配置项的键名
            model_type: 目标Pydantic模型类型

        Returns:
            解析后的配置对象，如果配置项不存在则返回None

        Raises:
            ValidationError: 当配置数据格式不正确时

        Example:
            >>> from pydantic import BaseSettings
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
        清除配置段缓存

        Args:
            key: 要清除的配置项键名，如果为None则清除所有缓存
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
        检查是否存在指定的配置段

        Args:
            key: 配置项的键名

        Returns:
            如果配置段存在则返回True，否则返回False
        """
        extra_data = self.model_extra
        return extra_data is not None and key in extra_data

    def get_section_keys(self) -> list[str]:
        """
        获取所有可用的配置段键名

        Returns:
            配置段键名列表
        """
        extra_data = self.model_extra
        if not extra_data:
            return []

        # 排除已知的标准配置字段
        standard_fields = {"server", "logger", "databases"}
        return [key for key in extra_data.keys() if key not in standard_fields]


def load_config(config_path: str = _DEFAULT_CONFIG_PATH, **kwargs) -> Config:
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

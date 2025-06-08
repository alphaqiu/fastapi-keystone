import json
from pathlib import Path
from typing import Dict, Optional

from pydantic import Field, RootModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from fastapi_keystone.common import deep_merge

_DEFAULT_CONFIG_PATH = "config.json"


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
    run_mode: str = Field(
        default="dev",
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
        default="%(asctime)s.%(msecs)03d |%(levelname)s| %(name)s.%(funcName)s:%(lineno)d |logmsg| %(message)s"
    )
    file: Optional[str] = Field(
        default=None,
        description="日志文件路径, 如果为空则不写入文件",
        examples=["logs/app.log"],
    )
    console: bool = Field(default=True)


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    # 数据库配置
    enable: bool = Field(default=True)
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=5432)
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")
    database: str = Field(default="fastapi_keystone")


class DatabasesConfig(RootModel[Dict[str, DatabaseConfig]]):
    """数据库配置，支持多个数据库，默认使用default数据库，default 数据库配置必须存在

    Pydantic v1: 可以在 BaseModel 里用 __root__ 字段实现根模型。
    Pydantic v2：必须用 pydantic.RootModel，不能在 BaseModel 里用 __root__ 字段，
    否则会报你遇到的错误。
    """

    @field_validator("root")
    @classmethod
    def must_have_default(
        cls, v: Dict[str, DatabaseConfig]
    ) -> Dict[str, DatabaseConfig]:
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
    databases: DatabasesConfig


async def load_config(config_path: str = _DEFAULT_CONFIG_PATH, **kwargs) -> Config:
    config_file_path = Path(config_path)
    if not config_file_path.exists():
        # 如果没有指定配置文件，尝试从默认 .env 文件加载
        # 同时也会从环境变量加载
        # 最后用传入的参数覆盖
        config = Config(**kwargs)
        return config

    if config_file_path.suffix == ".json":
        # 从 JSON 文件加载
        # 1. 从配置文件加载基础配置
        config_data = {}
        with open(config_file_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        # 2. 合并基础配置和传入的参数
        config_data = deep_merge(config_data, kwargs)
        # 3. 创建 Config 实例
        config = Config.model_validate(config_data)
        return config

    raise ValueError(f"Unsupported config file type: {config_file_path.suffix}")

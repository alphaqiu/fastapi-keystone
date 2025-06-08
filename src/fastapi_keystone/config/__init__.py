from injector import Module, provider, singleton

from fastapi_keystone.config.logger import setup_logger

from .config import (
    Config,
    DatabaseConfig,
    DatabasesConfig,
    LoggerConfig,
    ServerConfig,
    load_config,
)


class ConfigModule(Module):
    def __init__(self, config_path: str) -> None:
        self._config_path = config_path

    @provider
    @singleton
    def config(self) -> Config:
        # injector 不支持 异步provider
        config = load_config(config_path=self._config_path)
        setup_logger(config)
        return config


__all__ = [
    "Config",
    "load_config",
    "ServerConfig",
    "LoggerConfig",
    "DatabaseConfig",
    "DatabasesConfig",
    "ConfigModule",
]

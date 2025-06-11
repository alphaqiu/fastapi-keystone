from __future__ import annotations

from logging import getLogger
from typing import Any, Dict, List, Optional, Type, TypeVar

from injector import Injector, Module, ScopeDecorator
from injector import singleton as injector_singleton

from fastapi_keystone.config import Config, ConfigModule
from fastapi_keystone.core.db import DatabaseModule
from fastapi_keystone.core.logger import setup_logger
from fastapi_keystone.core.server import Server

logger = getLogger(__name__)
T = TypeVar("T")


class AppManager:
    """
    Application manager for dependency injection and service registry.

    Wraps an Injector instance and provides helpers for service registration and retrieval.

    Attributes:
        injector (Injector): The underlying Injector instance.
    """
    def __init__(self, config_path: str, modules: List[Module]):
        """
        Initialize the AppManager.

        Args:
            config_path (str): Path to the configuration file.
            modules (List[Module]): List of Injector modules to load.
        """
        _internal_modules = [
            ConfigModule(config_path),
            DatabaseModule,
        ]
        self.injector = Injector(_internal_modules + modules)
        self.injector.binder.bind(AppManager, to=self, scope=injector_singleton)
        setup_logger(self.injector.get(Config))
        logger.info("AppManager initialized. 🚀 🚀 🚀")

    def get_server(self) -> Server:
        return self.injector.get(Server)

    def get_instance(self, cls: Type[T]) -> T:
        """
        Get an instance of the given class from the injector.

        Args:
            cls (Type[T]): The class to retrieve.

        Returns:
            T: The instance of the class.
        """
        return self.injector.get(cls)

    def get_injector(self) -> Injector:
        """
        获取底层的 Injector 实例

        Returns:
            Injector 实例
        """
        return self.injector

    def register_singleton(self, cls: Type[T], instance: T) -> None:
        """
        Register a singleton instance for the given class.

        Args:
            cls (Type[T]): The class type.
            instance (T): The instance to register.
        """
        self.injector.binder.bind(cls, to=instance, scope=injector_singleton)

    def register_provider(self, cls: Type[T], provider: Any, scope: ScopeDecorator = injector_singleton) -> None:
        """
        Register a provider for the given class.

        Args:
            cls (Type[T]): The class type.
            provider (Any): The provider function or class.
            scope (ScopeDecorator, optional): The scope for the provider. Defaults to singleton.
        """
        self.injector.binder.bind(cls, to=provider, scope=scope)


def create_app_manager(
    *,
    config_path: str,
    modules: Optional[List[Module]] = None,
) -> AppManager:
    """
    创建应用程序管理器

    Args:
        config_path: 配置文件路径
        modules: 依赖注入模块列表
        server_kwargs: 服务器参数

    Returns:
        应用程序管理器

    Example:
        >>> app_manager = create_app_manager(
        ...     config_path="config.yaml",
        ...     modules=[],
        ...     server_kwargs={"port": 8000},
        ... )
        >>> app = app_manager.get_server().setup_api([])
    """
    return AppManager(config_path, modules or [])

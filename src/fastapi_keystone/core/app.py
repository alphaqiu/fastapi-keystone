from __future__ import annotations

from logging import getLogger
from typing import Any, List, Optional, Type, TypeVar, Union

from injector import Injector, Module, ScopeDecorator
from injector import singleton as injector_singleton

from fastapi_keystone.config import Config, ConfigModule
from fastapi_keystone.core.contracts import ServerProtocol
from fastapi_keystone.core.db import DatabaseModule
from fastapi_keystone.core.logger import setup_logger

logger = getLogger(__name__)
T = TypeVar("T")


class AppManager:
    """
    Application manager for dependency injection and service registry.

    Wraps an Injector instance and provides helpers for service registration and retrieval.

    Attributes:
        injector (Injector): The underlying Injector instance.
    """

    def __init__(self, config_path: str, modules: List[Union[Module, Type[Module]]]):
        """
        Initialize the AppManager.

        Args:
            config_path (str): Path to the configuration file.
            modules (List[Module]): List of Injector modules to load.
        """
        _internal_modules: List[Union[Module, Type[Module]]] = [
            ConfigModule(config_path),
            DatabaseModule,
        ]
        modules = modules or []
        self.injector = Injector(_internal_modules + modules)
        self.injector.binder.bind(AppManager, to=self, scope=injector_singleton)
        setup_logger(self.injector.get(Config))
        logger.info("AppManager initialized. 🚀 🚀 🚀")

    def get_server(self) -> ServerProtocol:
        # 延迟导入，避免循环依赖
        from fastapi_keystone.core.server import Server

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

    def register_provider(
        self, cls: Type[T], provider: Any, scope: ScopeDecorator = injector_singleton
    ) -> None:
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
    modules: Optional[List[Union[Module, Type[Module]]]] = None,
) -> AppManager:
    """
    Create an application manager for FastAPI-Keystone.

    This function initializes the dependency injection container, loads configuration, and prepares the application manager for use.

    Args:
        config_path (str): Path to the configuration file (e.g., 'config.yaml', 'config.json').
        modules (Optional[List[Union[Module, Type[Module]]]]): List of Injector modules for dependency injection.

    Returns:
        AppManager: The application manager instance.

    Example:
        # --- MVC-style API with DI: Controller -> Service -> DAO ---
        from fastapi import APIRouter, Depends
        from fastapi_keystone.core.app import create_app_manager
        from injector import Module, provider, singleton, inject

        # --- DAO Layer ---
        class UserDAO:
            def get_user(self, user_id: int) -> dict:
                return {"id": user_id, "name": f"User{user_id}"}

        # --- Service Layer ---
        class UserService:
            @inject
            def __init__(self, dao: UserDAO):
                self.dao = dao
            def get_user_info(self, user_id: int) -> dict:
                user = self.dao.get_user(user_id)
                user["role"] = "admin"
                return user

        # --- Controller Layer ---
        class UserController:
            @inject
            def __init__(self, service: UserService):
                self.service = service
                self.router = APIRouter()
                self.router.add_api_route(
                    "/user/{user_id}", self.get_user, methods=["GET"]
                )
            async def get_user(self, user_id: int):
                return self.service.get_user_info(user_id)

        # --- DI Module ---
        class UserModule(Module):
            @singleton
            @provider
            def provide_dao(self) -> UserDAO:
                return UserDAO()
            @singleton
            @provider
            def provide_service(self, dao: UserDAO) -> UserService:
                return UserService(dao)
            @singleton
            @provider
            def provide_controller(self, service: UserService) -> UserController:
                return UserController(service)

        # --- AppManager and API Setup ---
        app_manager = create_app_manager(
            config_path="config.yaml",
            modules=[UserModule()],
        )
        user_controller = app_manager.get_instance(UserController)
        app = app_manager.get_server().setup_api([user_controller.router])

        # Now, GET /user/1 will return: {"id": 1, "name": "User1", "role": "admin"}
    """
    return AppManager(config_path, modules or [])

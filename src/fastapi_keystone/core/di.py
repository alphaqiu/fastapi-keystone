from __future__ import annotations

from typing import List, Optional, Type, TypeVar

from injector import Injector, Module

from fastapi_keystone.common.singleton import singleton

T = TypeVar("T")


class AppInjector:
    """
    应用程序依赖注入器单例

    确保整个应用程序使用同一个依赖注入器实例
    """

    def __init__(self, modules: List[Module]):
        """
        初始化依赖注入器

        Args:
            modules: 依赖注入模块列表
        """
        self.injector = Injector(modules)
        global _app_injector
        _app_injector = self

    def get_instance(self, cls: Type[T]) -> T:
        """
        获取类型的实例

        Args:
            cls: 要获取实例的类型

        Returns:
            类型的实例
        """
        return self.injector.get(cls)

    def get_injector(self) -> Injector:
        """
        获取底层的 Injector 实例

        Returns:
            Injector 实例
        """
        return self.injector


# Apply singleton decorator and store type references
_AppInjectorType = AppInjector
AppInjector = singleton(AppInjector)  # type: ignore[misc]
_app_injector: Optional[_AppInjectorType] = None


def get_app_injector() -> _AppInjectorType:
    """
    获取应用程序依赖注入器单例

    Returns:
        AppInjector 实例
    """
    if _app_injector is None:
        raise RuntimeError("AppInjector not initialized")
    return _app_injector

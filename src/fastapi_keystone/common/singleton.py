"""
单例模式实现

提供线程安全的单例模式装饰器和基类
"""

import threading
from typing import Any, Callable, Dict, Type, TypeVar

T = TypeVar("T")


class SingletonMeta(type):
    """
    线程安全的单例元类
    """

    _instances: Dict[Type, Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        """控制实例创建"""
        if cls not in cls._instances:
            with cls._lock:
                # 双重检查锁定
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance

        return cls._instances[cls]


def singleton(cls: Type[T]) -> Callable[..., T]:
    """
    单例装饰器

    将普通类转换为单例类

    Args:
        cls: 要转换为单例的类

    Returns:
        单例工厂函数

    Example:
        @singleton
        class MyService:
            def __init__(self):
                self.data = "shared data"
    """
    instances: Dict[Type, Any] = {}
    lock = threading.Lock()

    def get_instance(*args, **kwargs) -> T:
        """获取单例实例"""
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    # 复制类的属性到工厂函数
    get_instance.__name__ = cls.__name__
    get_instance.__doc__ = cls.__doc__
    get_instance.__module__ = cls.__module__

    return get_instance


class Singleton:
    """
    单例基类

    继承此类的子类将自动成为单例
    """

    _instances: Dict[Type, Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """
        控制实例的创建

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            类的单例实例
        """
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__new__(cls)
                    cls._instances[cls] = instance
        return cls._instances[cls]


def reset_singleton(cls_or_factory) -> None:
    """
    重置单例实例

    主要用于测试场景

    Args:
        cls_or_factory: 要重置的单例类或工厂函数
    """
    # 重置基于元类的单例
    if hasattr(SingletonMeta, "_instances"):
        # 寻找匹配的类
        to_remove = []
        for key in SingletonMeta._instances:
            if key == cls_or_factory or (
                hasattr(key, "__name__")
                and hasattr(cls_or_factory, "__name__")
                and key.__name__ == cls_or_factory.__name__
            ):
                to_remove.append(key)
        for key in to_remove:
            del SingletonMeta._instances[key]

    # 重置基于基类的单例
    if hasattr(Singleton, "_instances"):
        to_remove = []
        for key in Singleton._instances:
            if key == cls_or_factory or (
                hasattr(key, "__name__")
                and hasattr(cls_or_factory, "__name__")
                and key.__name__ == cls_or_factory.__name__
            ):
                to_remove.append(key)
        for key in to_remove:
            del Singleton._instances[key]

    # 如果是装饰器函数，需要清理其内部的实例字典
    if hasattr(cls_or_factory, "__closure__") and cls_or_factory.__closure__:
        for cell in cls_or_factory.__closure__:
            if hasattr(cell.cell_contents, "clear") and hasattr(
                cell.cell_contents, "get"
            ):
                # 这可能是一个字典
                try:
                    cell.cell_contents.clear()
                except (AttributeError, TypeError):
                    pass


def reset_all_singletons() -> None:
    """
    重置所有单例实例

    主要用于测试场景
    """
    if hasattr(SingletonMeta, "_instances"):
        SingletonMeta._instances.clear()

    if hasattr(Singleton, "_instances"):
        Singleton._instances.clear()


# 导出公共接口
__all__ = [
    "SingletonMeta",
    "singleton",
    "Singleton",
    "reset_singleton",
    "reset_all_singletons",
]

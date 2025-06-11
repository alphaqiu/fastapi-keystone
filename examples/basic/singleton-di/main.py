"""
依赖注入器单例模式示例

演示 FastAPI Keystone 中 AppInjector 的单例模式使用
"""

from injector import Module, provider
from injector import singleton as injector_singleton

from fastapi_keystone.common.singleton import reset_singleton
from fastapi_keystone.core.app import AppManager


class DatabaseService:
    """数据库服务"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        print(f"DatabaseService 初始化: {connection_string}")

    def connect(self) -> str:
        return f"已连接到: {self.connection_string}"


class CacheService:
    """缓存服务"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        print(f"CacheService 初始化: {redis_url}")

    def get(self, key: str) -> str:
        return f"从 {self.redis_url} 获取 {key}"


class UserService:
    """用户服务"""

    def __init__(self, db: DatabaseService, cache: CacheService):
        self.db = db
        self.cache = cache
        print("UserService 初始化完成")

    def get_user(self, user_id: int) -> str:
        # 先从缓存获取
        cache_result = self.cache.get(f"user:{user_id}")
        # 如果缓存没有，从数据库获取
        db_result = self.db.connect()
        return f"用户 {user_id}: {cache_result}, {db_result}"


class AppModule(Module):
    """应用程序依赖注入模块"""

    @provider
    @injector_singleton
    def provide_database_service(self) -> DatabaseService:
        return DatabaseService("postgresql://localhost:5432/app")

    @provider
    @injector_singleton
    def provide_cache_service(self) -> CacheService:
        return CacheService("redis://localhost:6379/0")

    @provider
    @injector_singleton
    def provide_user_service(
        self, db: DatabaseService, cache: CacheService
    ) -> UserService:
        return UserService(db, cache)


def test_singleton_di():
    """测试依赖注入器单例"""
    print("=== 测试 AppInjector 单例模式 ===")

    # 创建两个 AppInjector 实例
    injector1 = AppManager([AppModule()])
    injector2 = AppManager([AppModule()])

    print(f"injector1 is injector2: {injector1 is injector2}")
    print(f"injector1 id: {id(injector1)}")
    print(f"injector2 id: {id(injector2)}")

    # 验证是同一个实例
    assert injector1 is injector2, "AppInjector 应该是单例"

    print("\n=== 测试依赖注入 ===")

    # 从两个"不同"的注入器获取相同的服务
    user_service1 = injector1.get_instance(UserService)
    user_service2 = injector2.get_instance(UserService)

    print(f"user_service1 is user_service2: {user_service1 is user_service2}")

    # 使用服务
    result = user_service1.get_user(123)
    print(f"服务调用结果: {result}")


def test_multiple_modules():
    """测试多个模块的情况"""
    print("\n=== 测试多个模块 ===")

    class SecondaryModule(Module):
        pass

    # 重置单例以便重新测试
    reset_singleton(AppManager)

    # 创建带多个模块的注入器
    injector1 = AppManager([AppModule(), SecondaryModule()])
    injector2 = AppManager([AppModule(), SecondaryModule()])

    print(f"多模块注入器是否单例: {injector1 is injector2}")

    # 获取服务实例
    user_service = injector1.get_instance(UserService)
    db_service = injector1.get_instance(DatabaseService)
    cache_service = injector1.get_instance(CacheService)

    print(f"UserService: {type(user_service).__name__}")
    print(f"DatabaseService: {type(db_service).__name__}")
    print(f"CacheService: {type(cache_service).__name__}")


def test_injector_access():
    """测试底层注入器访问"""
    print("\n=== 测试底层注入器访问 ===")

    # 重置单例
    reset_singleton(AppManager)

    app_injector = AppManager([AppModule()])

    # 获取底层注入器
    raw_injector = app_injector.get_injector()
    print(f"底层注入器类型: {type(raw_injector)}")

    # 直接使用底层注入器
    user_service = raw_injector.get(UserService)
    print(f"通过底层注入器获取的服务: {type(user_service).__name__}")


if __name__ == "__main__":
    test_singleton_di()
    test_multiple_modules()
    test_injector_access()

    print("\n✅ 所有测试完成！")

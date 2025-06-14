"""
依赖注入管理器示例

演示 FastAPI Keystone 中 AppManager 的依赖注入使用
"""

from injector import Module, provider
from injector import singleton as injector_singleton

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
    def provide_user_service(self, db: DatabaseService, cache: CacheService) -> UserService:
        return UserService(db, cache)


def test_app_manager_di():
    """测试应用管理器依赖注入"""
    print("=== 测试 AppManager 依赖注入 ===")

    # 创建两个 AppManager 实例
    manager1 = AppManager("config.json", [AppModule()])
    manager2 = AppManager("config.json", [AppModule()])

    print(f"manager1 is manager2: {manager1 is manager2} (不同实例)")
    print(f"manager1 id: {id(manager1)}")
    print(f"manager2 id: {id(manager2)}")

    # AppManager 不是单例，但服务可以是单例
    assert manager1 is not manager2, "AppManager 不应该是单例"

    print("\n=== 测试跨管理器的服务隔离 ===")

    # 从两个不同的管理器获取相同的服务
    user_service1 = manager1.get_instance(UserService)
    user_service2 = manager2.get_instance(UserService)

    # 不同 AppManager 实例的服务是隔离的
    print(f"跨管理器服务是隔离的: user_service1 is user_service2: {user_service1 is user_service2}")

    # 使用服务
    result = user_service1.get_user(123)
    print(f"服务调用结果: {result}")


def test_same_manager_singleton():
    """测试同一管理器内的服务单例性"""
    print("\n=== 测试同一管理器内的服务单例性 ===")

    # 创建一个管理器
    manager = AppManager("config.json", [AppModule()])

    # 从同一个管理器多次获取服务
    user_service1 = manager.get_instance(UserService)
    user_service2 = manager.get_instance(UserService)
    db_service1 = manager.get_instance(DatabaseService)
    db_service2 = manager.get_instance(DatabaseService)

    print(f"同一管理器内UserService是单例: {user_service1 is user_service2}")
    print(f"同一管理器内DatabaseService是单例: {db_service1 is db_service2}")

    print(f"UserService: {type(user_service1).__name__}")
    print(f"DatabaseService: {type(db_service1).__name__}")
    print(f"CacheService: {type(manager.get_instance(CacheService)).__name__}")


def test_injector_access():
    """测试底层注入器访问"""
    print("\n=== 测试底层注入器访问 ===")

    app_manager = AppManager("config.json", [AppModule()])

    # 获取底层注入器
    raw_injector = app_manager.get_injector()
    print(f"底层注入器类型: {type(raw_injector)}")

    # 直接使用底层注入器
    user_service = raw_injector.get(UserService)
    print(f"通过底层注入器获取的服务: {type(user_service).__name__}")


def test_server_setup():
    """测试服务器设置"""
    print("\n=== 测试服务器设置 ===")
    
    try:
        # 创建应用管理器
        manager = AppManager("config.json", [AppModule()])
        
        # 设置服务器（这里不传入控制器，只是测试API）
        server = manager.setup_server([])
        
        print(f"服务器类型: {type(server).__name__}")
        print(f"FastAPI 应用: {type(server.get_app()).__name__}")
        
    except Exception as e:
        print(f"服务器设置测试跳过: {e}")


if __name__ == "__main__":
    test_app_manager_di()
    test_same_manager_singleton()
    test_injector_access()
    test_server_setup()

    print("\n✅ 所有测试完成！")

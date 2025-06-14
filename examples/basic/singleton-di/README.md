# AppManager 依赖注入示例

本示例演示了 FastAPI Keystone 框架中 AppManager 依赖注入管理器的使用。

## 🎯 主要特性

### 1. AppManager 依赖注入
- `AppManager` 是应用程序的核心依赖注入管理器
- 基于 `injector` 库实现依赖注入
- 支持模块化的服务注册和管理
- 每个 AppManager 实例都有独立的依赖注入容器

### 2. 依赖注入整合
- 与 `injector` 库无缝集成
- 支持 provider 模式
- 支持单例服务注册
- 自动处理依赖关系

## 🚀 运行示例

```bash
cd examples/basic/singleton-di
python main.py
```

## 📋 示例输出

```
=== 测试 AppManager 依赖注入 ===
manager1 is manager2: False (不同实例)
manager1 id: 4403156640
manager2 id: 4401608848

=== 测试跨管理器的服务隔离 ===
DatabaseService 初始化: postgresql://localhost:5432/app
CacheService 初始化: redis://localhost:6379/0
UserService 初始化完成
DatabaseService 初始化: postgresql://localhost:5432/app
CacheService 初始化: redis://localhost:6379/0
UserService 初始化完成
跨管理器服务是隔离的: user_service1 is user_service2: False
服务调用结果: 用户 123: 从 redis://localhost:6379/0 获取 user:123, 已连接到: postgresql://localhost:5432/app

=== 测试同一管理器内的服务单例性 ===
DatabaseService 初始化: postgresql://localhost:5432/app
CacheService 初始化: redis://localhost:6379/0
UserService 初始化完成
同一管理器内UserService是单例: True
同一管理器内DatabaseService是单例: True
UserService: UserService
DatabaseService: DatabaseService
CacheService: CacheService

=== 测试底层注入器访问 ===
底层注入器类型: <class 'injector.Injector'>
通过底层注入器获取的服务: UserService

=== 测试服务器设置 ===
服务器类型: Server
FastAPI 应用: FastAPI

✅ 所有测试完成！
```

## 💡 核心概念

### AppManager 依赖注入
```python
from fastapi_keystone.core.app import AppManager

# 创建应用管理器
manager = AppManager("config.json", [MyModule()])

# 获取服务实例
user_service = manager.get_instance(UserService)
```

### 依赖注入模块
```python
from injector import Module, provider
from injector import singleton as injector_singleton

class AppModule(Module):
    @provider
    @injector_singleton
    def provide_database_service(self) -> DatabaseService:
        return DatabaseService("postgresql://localhost:5432/app")
    
    @provider
    @injector_singleton  
    def provide_user_service(self, db: DatabaseService) -> UserService:
        return UserService(db)
```

### 服务获取
```python
# 获取服务实例
user_service = app_manager.get_instance(UserService)

# 或者直接使用底层注入器
raw_injector = app_manager.get_injector()
user_service = raw_injector.get(UserService)
```

## 🛠️ 实际应用场景

### 1. FastAPI 应用中使用
```python
from fastapi import FastAPI, Depends
from fastapi_keystone.core.app import AppManager

# 创建应用管理器
app_manager = AppManager("config.json", [AppModule()])

def get_user_service() -> UserService:
    return app_manager.get_instance(UserService)

@app.get("/users/{user_id}")
async def get_user(user_id: int, user_service: UserService = Depends(get_user_service)):
    return user_service.get_user(user_id)
```

### 2. 使用 setup_server 方法
```python
from fastapi_keystone.core.app import AppManager
from fastapi_keystone.core.routing import Router, group

router = Router()

@group("/api/v1")
class UserController:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    @router.get("/users/{user_id}")
    async def get_user(self, user_id: int):
        return self.user_service.get_user(user_id)

# 创建应用管理器并设置服务器
manager = AppManager("config.json", [AppModule()])
server = manager.setup_server([UserController])
app = server.get_app()
```

### 3. 配置管理
```python
from fastapi_keystone.config import Config

class ConfigModule(Module):
    @provider
    @injector_singleton
    def provide_config(self) -> Config:
        return Config.from_file("config.json")

# 在任何地方获取配置
manager = AppManager("config.json", [ConfigModule()])
config = manager.get_instance(Config)
```

### 4. 数据库连接池
```python
class DatabaseModule(Module):
    @provider
    @injector_singleton
    def provide_connection_pool(self) -> ConnectionPool:
        return create_connection_pool(database_url)

# 共享连接池
manager = AppManager("config.json", [DatabaseModule()])
pool = manager.get_instance(ConnectionPool)
```

## 🧪 测试支持

AppManager 本身不是单例，每个实例都有独立的依赖注入容器：

```python
def test_with_clean_manager():
    # 创建新的测试管理器
    test_manager = AppManager("test_config.json", [TestModule()])
    
    # 获取测试服务
    test_service = test_manager.get_instance(TestService)
    # ... 测试代码
```

## ⚠️ 注意事项

1. **AppManager 不是单例**: 每次创建 AppManager 都是新实例
2. **服务单例范围**: 服务只在同一个 AppManager 实例内是单例的
3. **跨管理器隔离**: 不同 AppManager 实例的服务是完全隔离的
4. **模块一致性**: 确保相同的模块配置产生相同的服务实例
5. **线程安全**: injector 库保证线程安全
6. **生命周期**: 服务的生命周期由其所属的 AppManager 管理

## 📝 最佳实践

1. **单一管理器**: 在应用中通常只创建一个 AppManager 实例
2. **模块化**: 将相关的服务组织到独立的模块中
3. **单例服务**: 对于共享资源使用 `@injector_singleton` 装饰器
4. **依赖声明**: 明确声明服务之间的依赖关系
5. **测试友好**: 为测试创建独立的 AppManager 实例
6. **配置管理**: 使用配置文件管理应用设置
7. **服务隔离**: 利用不同 AppManager 实例实现服务隔离 
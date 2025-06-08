# AppInjector 单例模式示例

本示例演示了 FastAPI Keystone 框架中 AppInjector 依赖注入器的单例模式使用。

## 🎯 主要特性

### 1. AppInjector 单例
- `AppInjector` 使用 `@singleton` 装饰器实现单例模式
- 整个应用程序共享同一个依赖注入器实例
- 线程安全的实现

### 2. 依赖注入整合
- 与 `injector` 库无缝集成
- 支持 provider 模式
- 支持单例服务注册

## 🚀 运行示例

```bash
cd examples/basic/singleton-di
python main.py
```

## 📋 示例输出

```
=== 测试 AppInjector 单例模式 ===
injector1 is injector2: True
injector1 id: 4368609168
injector2 id: 4368609168

=== 测试依赖注入 ===
DatabaseService 初始化: postgresql://localhost:5432/app
CacheService 初始化: redis://localhost:6379/0
UserService 初始化完成
user_service1 is user_service2: True
服务调用结果: 用户 123: 从 redis://localhost:6379/0 获取 user:123, 已连接到: postgresql://localhost:5432/app

=== 测试多个模块 ===
多模块注入器是否单例: True
UserService: UserService
DatabaseService: DatabaseService
CacheService: CacheService

=== 测试底层注入器访问 ===
底层注入器类型: <class 'injector.Injector'>
通过底层注入器获取的服务: UserService

✅ 所有测试完成！
```

## 💡 核心概念

### AppInjector 单例
```python
from fastapi_keystone.core.di import AppInjector

# 无论创建多少次，都是同一个实例
injector1 = AppInjector([MyModule()])
injector2 = AppInjector([MyModule()])

assert injector1 is injector2  # True
```

### 依赖注入模块
```python
from injector import Module, provider, singleton

class AppModule(Module):
    @provider
    @singleton
    def provide_database_service(self) -> DatabaseService:
        return DatabaseService("postgresql://localhost:5432/app")
    
    @provider
    @singleton  
    def provide_user_service(self, db: DatabaseService) -> UserService:
        return UserService(db)
```

### 服务获取
```python
# 获取服务实例
user_service = app_injector.get_instance(UserService)

# 或者直接使用底层注入器
raw_injector = app_injector.get_injector()
user_service = raw_injector.get(UserService)
```

## 🛠️ 实际应用场景

### 1. FastAPI 应用中使用
```python
from fastapi import FastAPI, Depends
from fastapi_keystone.core.di import AppInjector

app = FastAPI()

# 全局依赖注入器
def get_injector() -> AppInjector:
    return AppInjector([AppModule()])

def get_user_service(injector: AppInjector = Depends(get_injector)) -> UserService:
    return injector.get_instance(UserService)

@app.get("/users/{user_id}")
async def get_user(user_id: int, user_service: UserService = Depends(get_user_service)):
    return user_service.get_user(user_id)
```

### 2. 配置管理
```python
class ConfigModule(Module):
    @provider
    @singleton
    def provide_config(self) -> AppConfig:
        return AppConfig.from_env()

# 在任何地方获取配置
injector = AppInjector([ConfigModule()])
config = injector.get_instance(AppConfig)
```

### 3. 数据库连接池
```python
class DatabaseModule(Module):
    @provider
    @singleton
    def provide_connection_pool(self) -> ConnectionPool:
        return create_connection_pool(database_url)

# 共享连接池
injector = AppInjector([DatabaseModule()])
pool = injector.get_instance(ConnectionPool)
```

## 🧪 测试支持

在测试环境中可以重置单例：

```python
from fastapi_keystone.common.singleton import reset_singleton

def test_with_clean_injector():
    # 重置单例状态
    reset_singleton(AppInjector)
    
    # 创建新的测试注入器
    test_injector = AppInjector([TestModule()])
    # ... 测试代码
```

## ⚠️ 注意事项

1. **模块一致性**: 确保所有地方使用相同的模块配置
2. **线程安全**: AppInjector 是线程安全的
3. **测试隔离**: 在测试中适当使用 `reset_singleton()`
4. **生命周期**: AppInjector 的生命周期是应用程序级别的

## 📝 最佳实践

1. **统一配置**: 在应用启动时配置 AppInjector
2. **模块化**: 将相关的服务组织到独立的模块中
3. **单例服务**: 对于共享资源使用 `@singleton` 装饰器
4. **依赖声明**: 明确声明服务之间的依赖关系
5. **测试友好**: 支持测试时的依赖替换 
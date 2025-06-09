# 配置扩展机制设计文档

## 概述

FastAPI Keystone 的配置扩展机制允许开发者在不修改核心配置类的情况下，轻松地添加自定义配置段。该机制基于 Pydantic V2 的 `extra="allow"` 功能，提供了类型安全的配置扩展方案。

## 设计目标

1. **灵活性**: 允许项目根据需求添加任意自定义配置段
2. **类型安全**: 利用 Pydantic 提供强类型验证和IDE支持
3. **性能优化**: 提供缓存机制避免重复解析
4. **易用性**: 提供简洁的API接口
5. **兼容性**: 不影响现有的核心配置功能

## 核心特性

### 1. 泛型配置段获取

```python
def get_section(self, key: str, model_type: Type[T]) -> Optional[T]:
    """从配置的extra字段中提取指定key的配置，并解析为指定的Pydantic类型"""
```

### 2. 缓存机制

- 自动缓存已解析的配置对象
- 支持按配置段清除缓存
- 避免重复解析提升性能

### 3. 辅助方法

- `has_section(key: str)`: 检查配置段是否存在
- `get_section_keys()`: 获取所有可用配置段键名
- `clear_section_cache()`: 清除缓存

## 使用方法

### 步骤1: 定义配置类

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class RedisConfig(BaseSettings):
    host: str = Field(default="127.0.0.1", description="Redis服务器地址")
    port: int = Field(default=6379, description="Redis端口")
    password: Optional[str] = Field(default=None, description="Redis密码")
    database: int = Field(default=0, description="Redis数据库编号")
    enable: bool = Field(default=True, description="是否启用Redis")
```

### 步骤2: 配置文件

```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 8080
    },
    "logger": {
        "level": "info"
    },
    "databases": {
        "default": {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "postgres",
            "database": "fastapi_keystone"
        }
    },
    "redis": {
        "host": "redis.example.com",
        "port": 6380,
        "password": "secret",
        "database": 1
    }
}
```

### 步骤3: 使用配置

```python
from fastapi_keystone.config import load_config

# 加载配置
config = load_config("config.json")

# 获取扩展配置段
redis_config = config.get_section('redis', RedisConfig)
if redis_config and redis_config.enable:
    # 使用Redis配置
    print(f"Redis: {redis_config.host}:{redis_config.port}")
```

## 实现细节

### 1. 核心机制

利用 Pydantic V2 的 `extra="allow"` 配置，额外的字段会存储在 `model_extra` 属性中：

```python
class Config(BaseSettings):
    model_config = SettingsConfigDict(extra="allow")
    
    # 标准配置字段
    server: ServerConfig
    logger: LoggerConfig
    databases: DatabasesConfig
```

### 2. 类型安全

使用 TypeVar 确保返回类型与传入的模型类型一致：

```python
T = TypeVar('T', bound=BaseSettings)

def get_section(self, key: str, model_type: Type[T]) -> Optional[T]:
    # 实现细节...
```

### 3. 缓存实现

使用字典缓存已解析的配置对象，键格式为 `"{key}:{model_type.__name__}"`：

```python
_section_cache: Dict[str, Any] = {}

cache_key = f"{key}:{model_type.__name__}"
if cache_key in self._section_cache:
    return self._section_cache[cache_key]
```

### 4. 错误处理

提供详细的错误信息和异常处理：

```python
try:
    config_instance = model_type.model_validate(section_data)
except ValidationError as e:
    raise ValueError(
        f"Failed to parse config section '{key}' as {model_type.__name__}: {str(e)}"
    ) from e
```

## 最佳实践

### 1. 配置类设计

- 继承自 `BaseSettings` 以获得环境变量支持
- 提供合理的默认值
- 使用 `Field` 添加描述和验证规则
- 保持配置类的简洁性

### 2. 配置文件组织

- 按功能模块组织配置段
- 使用描述性的键名
- 保持配置层次结构的一致性

### 3. 错误处理

- 检查配置段是否存在：`config.has_section('redis')`
- 处理配置解析错误
- 提供配置缺失时的降级方案

### 4. 性能优化

- 利用缓存机制避免重复解析
- 在配置变更时清除相关缓存
- 延迟加载非关键配置

## 示例场景

### 1. Redis 配置

```python
class RedisConfig(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 6379
    password: Optional[str] = None
    database: int = 0
    max_connections: int = 10

redis_config = config.get_section('redis', RedisConfig)
```

### 2. 邮件服务配置

```python
class EmailConfig(BaseSettings):
    smtp_host: str
    smtp_port: int = 587
    username: str
    password: str
    use_tls: bool = True

email_config = config.get_section('email', EmailConfig)
```

### 3. 第三方服务配置

```python
class ThirdPartyConfig(BaseSettings):
    api_key: str
    base_url: str
    timeout: int = 30
    retry_count: int = 3

service_config = config.get_section('third_party', ThirdPartyConfig)
```

## 与现有配置的兼容性

该扩展机制与现有的核心配置（server, logger, databases）完全兼容：

- 不影响现有配置的使用方式
- 现有配置仍可以直接通过属性访问
- 扩展配置段不会与核心配置冲突

## 总结

配置扩展机制为 FastAPI Keystone 框架提供了强大的扩展能力，允许开发者根据项目需求灵活地添加自定义配置，同时保持了类型安全和性能优化。这个设计既满足了框架的通用性需求，又保证了使用的简洁性和可维护性。 
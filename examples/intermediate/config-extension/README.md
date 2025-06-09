# 配置扩展机制示例

本示例展示了如何使用 FastAPI Keystone 的配置扩展机制来支持自定义配置段。

## 功能特性

- **类型安全的配置扩展**: 使用 Pydantic 模型定义配置结构
- **自动缓存**: 避免重复解析提升性能
- **灵活的API**: 支持检查配置存在性、获取配置段列表等
- **完整的错误处理**: 提供详细的验证错误信息
- **支持 JSON/YAML 配置文件**: 可直接加载 `.json`、`.yaml`、`.yml` 格式

## 文件说明

- `config_extension_example.py`: 主要的示例程序
- `config.example.json`: 扩展后的示例配置文件
- `config.example.yaml`: YAML 格式的示例配置文件

## 配置文件格式

支持如下格式：
- JSON: `config.example.json`
- YAML: `config.example.yaml`

YAML 示例片段：

```yaml
server:
  host: 0.0.0.0
  port: 8080
  reload: false
  workers: 1
  run_mode: dev
  title: FastAPI Keystone
  description: FastAPI Keystone
  version: 0.0.1
```

## 运行示例

```bash
# 在项目根目录运行
PYTHONPATH=src python examples/intermediate/config-extension/config_extension_example.py
```

## 输出示例

```
=== FastAPI Keystone 配置扩展机制演示 ===

[1] 加载JSON配置:
   服务器: 0.0.0.0:8080
   运行模式: dev

[2] 加载YAML配置:
   服务器: 0.0.0.0:8080
   运行模式: dev

1. 基础配置信息:
   日志级别: info
   数据库: 127.0.0.1

2. 检查扩展配置段:
   可用的扩展配置段: ['redis', 'email', 'cache', 'auth']

3. 加载并使用扩展配置:
   ✓ Redis: 127.0.0.1:6379 (DB 0)
   ✓ Email: smtp.gmail.com:587 (TLS: True)
   ✓ Cache: redis (TTL: 3600s)
   ✓ Auth: HS256 (Token过期: 30分钟)

4. 缓存机制演示:
   第一次加载Redis配置: 4368694832
   第二次加载Redis配置: 4368694832
   是否为同一对象: True

=== 演示完成 ===
```

## 核心API

### 获取配置段

```python
redis_config = config.get_section('redis', RedisConfig)
```

### 检查配置段是否存在

```python
if config.has_section('redis'):
    # 处理Redis配置
```

### 获取所有扩展配置段

```python
sections = config.get_section_keys()
```

### 缓存管理

```python
# 清除特定配置段缓存
config.clear_section_cache('redis')

# 清除所有缓存
config.clear_section_cache()
```

## 自定义配置类示例

```python
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class RedisConfig(BaseSettings):
    host: str = Field(default="127.0.0.1", description="Redis服务器地址")
    port: int = Field(default=6379, description="Redis端口")
    password: Optional[str] = Field(default=None, description="Redis密码")
    database: int = Field(default=0, description="Redis数据库编号")
    enable: bool = Field(default=True, description="是否启用Redis")
```

## 配置文件格式

```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 8080
    },
    "redis": {
        "host": "redis.example.com",
        "port": 6380,
        "password": "secret",
        "database": 1
    },
    "email": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "user@example.com",
        "password": "password",
        "use_tls": true
    }
}
```

这个机制允许你轻松地扩展配置系统，而不需要修改核心框架代码。

## 参考

- [Pydantic 官方文档](https://docs.pydantic.dev/)
- [PyYAML 官方文档](https://pyyaml.org/wiki/PyYAMLDocumentation) 
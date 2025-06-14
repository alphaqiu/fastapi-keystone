# FastAPI Keystone

[![PyPI version](https://badge.fury.io/py/fastapi-keystone.svg?icon=si%3Apython)](https://badge.fury.io/py/fastapi-keystone)
[![Python Version](https://img.shields.io/pypi/pyversions/fastapi-keystone.svg)](https://pypi.org/project/fastapi-keystone/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

🚀 **一个基于 FastAPI 的轻量级开发框架，提供一些常用的企业级功能组件。**

## 项目简介

FastAPI Keystone 是一个围绕 FastAPI 构建的开发框架，旨在简化常见的 Web 应用开发任务。它提供了一些开箱即用的功能，如配置管理、路由装饰器、标准化响应格式、依赖注入集成等。

**注意：** 本项目仍在开发阶段，API 可能会发生变化。建议在生产环境使用前仔细评估。

## 核心特性

- **配置管理**：支持 JSON/YAML 配置文件，环境变量覆盖
- **路由装饰器**：基于类的路由定义方式
- **标准化响应**：统一的 API 响应格式
- **依赖注入**：与 injector 库的集成
- **中间件支持**：内置常用中间件（CORS、GZIP、异常处理等）
- **多租户支持**：基础的多数据库配置管理
- **分页查询**：简单的分页查询工具

## 安装

```bash
pip install fastapi-keystone
```

### 使用 uv (推荐)

```bash
uv add fastapi-keystone
```

## 快速开始

### 1. 基础使用

```python
import uvicorn
from fastapi_keystone.core.response import APIResponse
from fastapi_keystone.core.routing import Router, group
from fastapi_keystone.core.app import AppManager

# 创建路由器
router = Router()

@group("/api/v1")
class HelloController:
    @router.get("/hello")
    async def hello_world(self) -> APIResponse[str]:
        return APIResponse.success("Hello, FastAPI Keystone!")

    @router.get("/hello/{name}")
    async def hello_name(self, name: str) -> APIResponse[str]:
        return APIResponse.success(f"Hello, {name}!")

def main():
    # 创建应用管理器并设置服务器
    manager = AppManager("config.json", modules=[])
    server = manager.setup_server([HelloController])
    
    # 启动服务器
    uvicorn.run(server.get_app(), host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
```

### 2. 配置文件示例

创建 `config.json`：

```json
{
  "server": {
    "title": "My FastAPI App",
    "description": "基于 FastAPI Keystone 的应用",
    "version": "1.0.0",
    "host": "0.0.0.0",
    "port": 8000
  },
  "logger": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  },
  "databases": {
    "default": {
      "host": "localhost",
      "port": 5432,
      "user": "postgres",
      "password": "password",
      "database": "myapp"
    }
  }
}
```

或使用 YAML 格式 `config.yaml`：

```yaml
server:
  title: My FastAPI App
  description: 基于 FastAPI Keystone 的应用
  version: 1.0.0
  host: 0.0.0.0
  port: 8000

logger:
  level: INFO
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

databases:
  default:
    host: localhost
    port: 5432
    user: postgres
    password: password
    database: myapp
```

### 3. 依赖注入

```python
from injector import Module, provider, singleton, inject
from fastapi_keystone.config import Config
from fastapi_keystone.core.app import AppManager

# 定义服务
class UserService:
    def __init__(self, config: Config):
        self.config = config
    
    def get_user(self, user_id: int):
        return {"id": user_id, "name": f"User {user_id}"}

# 依赖注入模块
class ServiceModule(Module):
    @provider
    @singleton
    def user_service(self, config: Config) -> UserService:
        return UserService(config)

@group("/api/v1/users")
class UserController:
    @inject
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    @router.get("/{user_id}")
    async def get_user(self, user_id: int) -> APIResponse[dict]:
        user = self.user_service.get_user(user_id)
        return APIResponse.success(user)

def main():
    # 创建应用管理器并注册模块
    manager = AppManager("config.json", modules=[ServiceModule()])
    server = manager.setup_server([UserController])
    
    return server.get_app()
```

### 4. 中间件配置

```python
from fastapi_keystone.core.server import Server

def main():
    manager = AppManager("config.json", modules=[])
    
    # 获取服务器实例并配置中间件
    server = manager.get_instance(Server)
    server.enable_cors(
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"]
    )
    server.enable_simple_trace()
    # Gzip 默认启用，如需禁用可调用 server.disable_gzip()
    
    # 设置 API
    app = server.setup_api([HelloController])
    return app
```

### 5. 异常处理

```python
from fastapi_keystone.core.exceptions import APIException

@group("/api/v1/users")
class UserController:
    @router.get("/{user_id}")
    async def get_user(self, user_id: int) -> APIResponse[dict]:
        if user_id <= 0:
            raise APIException("Invalid user ID", code=400)
        
        if user_id > 1000:
            raise APIException("User not found", code=404)
        
        return APIResponse.success({"id": user_id, "name": f"User {user_id}"})
```

## API 响应格式

所有 API 响应都遵循统一格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "User 1"
  }
}
```

错误响应：

```json
{
  "code": 404,
  "message": "User not found",
  "data": null
}
```

分页响应：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {"id": 1, "name": "User 1"},
    {"id": 2, "name": "User 2"}
  ],
  "total": 100,
  "page": 1,
  "size": 10
}
```

## 项目结构建议

```
my-app/
├── app/
│   ├── __init__.py
│   ├── main.py              # 应用入口
│   ├── config.json          # 配置文件
│   ├── controllers/         # 控制器
│   │   ├── __init__.py
│   │   └── user_controller.py
│   ├── services/           # 业务逻辑
│   │   ├── __init__.py
│   │   └── user_service.py
│   └── models/             # 数据模型
│       ├── __init__.py
│       └── user.py
├── tests/                  # 测试文件
├── requirements.txt
└── README.md
```

## 配置扩展

框架支持自定义配置段：

```python
from pydantic import BaseModel, Field
from typing import Optional

class RedisConfig(BaseModel):
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=6379)
    password: Optional[str] = None
    database: int = Field(default=0)

# 在配置文件中添加
{
  "redis": {
    "host": "redis.example.com",
    "port": 6380,
    "password": "secret",
    "database": 1
  }
}

# 在代码中使用
config = load_config("config.json")
redis_config = config.get_section("redis", RedisConfig)
```

## 测试

```bash
# 运行测试
pytest

# 运行测试并查看覆盖率
pytest --cov=src --cov-report=html

# 运行特定测试
pytest tests/test_routing.py
```

## 开发

```bash
# 克隆项目
git clone https://github.com/alphaqiu/fastapi-keystone.git
cd fastapi-keystone

# 安装开发依赖
uv sync

# 运行测试
uv run pytest

# 代码格式化
uv run black .
uv run isort .

# 代码检查
uv run ruff check .
```

## 注意事项

1. **版本兼容性**：本项目仍在开发中，API 可能会发生变化
2. **生产使用**：建议在生产环境使用前进行充分测试
3. **依赖管理**：确保 FastAPI 和相关依赖版本兼容
4. **配置安全**：生产环境中注意保护敏感配置信息

## 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request。在提交代码前，请确保：

- 代码通过所有测试
- 遵循项目的代码风格
- 添加必要的测试用例
- 更新相关文档

## 链接

- **GitHub**: https://github.com/alphaqiu/fastapi-keystone
- **PyPI**: https://pypi.org/project/fastapi-keystone/
- **文档**: https://github.com/alphaqiu/fastapi-keystone#readme
- **问题反馈**: https://github.com/alphaqiu/fastapi-keystone/issues

# FastAPI Keystone

[![PyPI version](https://badge.fury.io/py/fastapi-keystone.svg?icon=si%3Apython)](https://badge.fury.io/py/fastapi-keystone)
[![Python Version](https://img.shields.io/pypi/pyversions/fastapi-keystone.svg)](https://pypi.org/project/fastapi-keystone/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

🚀 **基于 FastAPI 的现代化快速开发框架**

FastAPI Keystone 是一个企业级的 Python Web 开发框架，基于 FastAPI 构建，采用契约优先的设计理念，为开发者提供开箱即用的多租户、依赖注入、路由管理、配置管理等企业级特性。

## ✨ 核心特性

- 🎯 **契约优先**：基于 Pydantic 的强类型配置和数据模型
- 🏢 **多租户支持**：内置多数据库配置管理
- 💉 **依赖注入**：基于 injector 的 DI 容器
- 🎨 **装饰器路由**：支持类级别的路由定义
- ⚡ **异步优先**：全面支持 async/await
- 🛡️ **异常处理**：统一的 API 异常处理机制
- 📝 **标准化响应**：统一的 API 响应格式
- 🔧 **灵活配置**：支持 JSON、环境变量、.env 文件

## 📦 安装

### 使用 pip

```bash
pip install fastapi-keystone
```

### 使用 uv (推荐)

```bash
uv add fastapi-keystone
```

### 开发依赖

```bash
pip install fastapi-keystone[dev]
```

## 🚀 快速开始

### 1. 基础使用

```python
import uvicorn
from injector import Injector
from fastapi_keystone.config import ConfigModule
from fastapi_keystone.core.response import APIResponse
from fastapi_keystone.core.routing import group, router
from fastapi_keystone.core.server import Server
from fastapi_keystone.core.di import AppInjector

@group("/api/v1")
class IndexController:
    @router.get("/hello")
    async def hello_world(self) -> APIResponse[str]:
        return APIResponse.success("Hello, FastAPI Keystone!")

    @router.get("/users/{user_id}")
    async def get_user(self, user_id: int) -> APIResponse[dict]:
        return APIResponse.success({"id": user_id, "name": f"User {user_id}"})

def main():
    # 创建依赖注入容器
    injector = AppInjector([ConfigModule("config.json")])
    
    # 创建服务器
    server = injector.get_instance(Server)
    
    # 设置API
    app = server.setup_api(injector, [IndexController])
    
    # 启动服务器
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
```

### 2. 类级别路由定义与依赖注入

```python
import uvicorn
from typing import List
from injector import Module, provider, singleton, inject
from fastapi_keystone.config import ConfigModule
from fastapi_keystone.core.response import APIResponse
from fastapi_keystone.core.routing import group, router
from fastapi_keystone.core.server import Server
from fastapi_keystone.core.di import AppInjector

# 定义用户服务
class UserService:
    def get_user(self, user_id: int):
        return {"id": user_id, "name": f"User {user_id}"}
    
    def get_users(self):
        return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

# 服务模块，用于依赖注入
class ServiceModule(Module):
    @provider
    @singleton
    def user_service(self) -> UserService:
        return UserService()

# 使用类级别路由
@group("/api/v1/users")
class UserController:
    @inject
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    @router.get("/{user_id}")
    async def get_user(self, user_id: int) -> APIResponse[dict]:
        user = self.user_service.get_user(user_id)
        return APIResponse.success(user)
    
    @router.get("/")
    async def list_users(self) -> APIResponse[List[dict]]:
        users = self.user_service.get_users()
        return APIResponse.success(users)
    
    @router.post("/")
    async def create_user(self, user_data: dict) -> APIResponse[dict]:
        # 创建用户逻辑
        return APIResponse.success({"message": "User created", "data": user_data})

def main():
    # 创建依赖注入容器
    injector = AppInjector([
        ConfigModule("config.json"),
        ServiceModule()
    ])
    
    # 创建服务器
    server = injector.get_instance(Server)
    
    # 设置API
    app = server.setup_api(injector, [UserController])
    
    # 启动服务器
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
```

### 3. 配置管理

创建 `config.json` 文件：

```json
{
  "server": {
    "title": "My FastAPI Keystone App",
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
      "enable": true,
      "host": "localhost",
      "port": 3306,
      "user": "root",
      "password": "password",
      "database": "myapp"
    },
    "tenant_a": {
      "enable": true,
      "host": "localhost",
      "port": 3306,
      "user": "root",
      "password": "password",
      "database": "tenant_a_db"
    }
  }
}
```

使用配置：

```python
from injector import inject
from fastapi_keystone.config import Config, ConfigModule
from fastapi_keystone.core.server import Server
from fastapi_keystone.core.di import AppInjector

@group("/api/v1")
class ConfigController:
    @inject
    def __init__(self, config: Config):
        self.config = config
    
    @router.get("/info")
    async def get_app_info(self) -> APIResponse[dict]:
        return APIResponse.success({
            "title": self.config.server.title,
            "version": self.config.server.version,
            "db_host": self.config.databases.root["default"].host
        })

def main():
    # 创建依赖注入容器，自动加载配置
    injector = AppInjector([ConfigModule("config.json")])
    
    # 创建服务器
    server = injector.get_instance(Server)
    
    # 设置API
    app = server.setup_api(injector, [ConfigController])
    
    return app
```

### 4. 依赖注入

```python
import uvicorn
from injector import Module, provider, singleton, inject
from fastapi_keystone.config import Config, ConfigModule
from fastapi_keystone.core.response import APIResponse
from fastapi_keystone.core.routing import group, router
from fastapi_keystone.core.server import Server
from fastapi_keystone.core.di import AppInjector

class DatabaseService:
    def __init__(self, db_config):
        self.db_config = db_config
    
    def get_connection(self):
        return f"Connected to {self.db_config.host}:{self.db_config.port}"

class ServiceModule(Module):
    @provider
    @singleton
    def database_service(self, config: Config) -> DatabaseService:
        return DatabaseService(config.databases.root["default"])

# 在控制器中使用
@group("/api/v1/db")
class DatabaseController:
    @inject
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    @router.get("/status")
    async def get_db_status(self) -> APIResponse[str]:
        status = self.db_service.get_connection()
        return APIResponse.success(status)

def main():
    # 设置依赖注入容器
    injector = AppInjector([
        ConfigModule("config.json"),
        ServiceModule()
    ])
    
    # 创建服务器
    server = injector.get_instance(Server)
    
    # 设置API
    app = server.setup_api(injector, [DatabaseController])
    
    # 启动服务器
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
```

### 5. 异常处理

```python
from fastapi_keystone.core.exceptions import APIException
from fastapi_keystone.core.response import APIResponse

# 自定义异常
class UserNotFoundError(APIException):
    def __init__(self, user_id: int):
        super().__init__(
            status_code=404,
            code="USER_NOT_FOUND",
            message=f"User with ID {user_id} not found"
        )

@router.get("/users/{user_id}")
async def get_user(user_id: int) -> APIResponse[dict]:
    if user_id > 1000:
        raise UserNotFoundError(user_id)
    
    return APIResponse.success({"id": user_id, "name": f"User {user_id}"})
```

### 6. 中间件使用

```python
from fastapi_keystone.core.middleware import BaseMiddleware

class RequestLoggingMiddleware(BaseMiddleware):
    async def dispatch(self, request, call_next):
        print(f"Processing request: {request.method} {request.url}")
        response = await call_next(request)
        print(f"Response status: {response.status_code}")
        return response

# 添加中间件
server.add_middleware(RequestLoggingMiddleware)

# 在路由中使用中间件
@router.get("/protected", middlewares=[RequestLoggingMiddleware])
async def protected_endpoint() -> APIResponse[str]:
    return APIResponse.success("This endpoint is protected by middleware")
```

## 📖 API 文档

启动应用后，访问以下地址查看自动生成的 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🏗️ 项目结构

推荐的项目结构：

```
my-fastapi-app/
├── app/
│   ├── __init__.py
│   ├── main.py              # 应用入口
│   ├── config.json          # 配置文件
│   ├── controllers/         # 控制器
│   │   ├── __init__.py
│   │   ├── user_controller.py
│   │   └── auth_controller.py
│   ├── services/           # 业务逻辑
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── auth_service.py
│   ├── models/             # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── auth.py
│   └── middleware/         # 自定义中间件
│       ├── __init__.py
│       └── auth_middleware.py
├── tests/                  # 测试文件
├── requirements.txt        # 依赖列表
└── README.md
```

## 🔧 高级配置

### 环境变量支持

```python
# 支持环境变量覆盖配置
import os
os.environ["SERVER__HOST"] = "127.0.0.1"
os.environ["DATABASES__DEFAULT__HOST"] = "prod-db.example.com"

config = await load_config("config.json")  # 环境变量会覆盖文件配置
```

### 自定义响应格式

```python
from fastapi_keystone.core.response import APIResponse

# 成功响应
response = APIResponse.success(
    data={"user_id": 123, "name": "Alice"},
    message="User retrieved successfully"
)

# 错误响应
response = APIResponse.error(
    code="VALIDATION_ERROR",
    message="Invalid input parameters",
    details={"field": "email", "error": "Invalid format"}
)

# 分页响应
response = APIResponse.paginated(
    data=[{"id": 1}, {"id": 2}],
    total=100,
    page=1,
    page_size=10
)
```

## 🧪 测试

运行测试：

```bash
# 运行所有测试
pytest

# 运行测试并查看覆盖率
pytest --cov=app --cov-report=html

# 运行特定测试文件
pytest tests/test_user_controller.py
```

示例测试：

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_hello_world():
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"] == "Hello, FastAPI Keystone!"

@pytest.mark.asyncio
async def test_user_controller():
    response = client.get("/api/v1/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == 1
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/your-username/fastapi-keystone.git
cd fastapi-keystone

# 使用 uv 安装依赖
uv sync

# 运行测试
uv run pytest

# 代码格式化
uv run black .
uv run isort .

# 代码检查
uv run ruff check .
```

### 提交规范

- 🐛 `fix:` 修复 bug
- ✨ `feat:` 新功能
- 📝 `docs:` 文档更新
- 🎨 `style:` 代码格式化
- ♻️ `refactor:` 代码重构
- ✅ `test:` 添加测试
- 🔧 `chore:` 构建或工具变动

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。


## 📞 联系我们

- 🐛 **问题反馈**: [GitHub Issues](https://github.com/your-username/fastapi-keystone/issues)
- 💬 **讨论**: [GitHub Discussions](https://github.com/your-username/fastapi-keystone/discussions)

## ❓ 常见问题 (FAQ)

### Q: 如何启用多租户支持？

A: 在配置文件中定义多个数据库配置，每个租户对应一个数据库：

```json
{
  "databases": {
    "default": { "host": "localhost", "database": "main_db" },
    "tenant_a": { "host": "localhost", "database": "tenant_a_db" },
    "tenant_b": { "host": "localhost", "database": "tenant_b_db" }
  }
}
```

### Q: 如何自定义异常处理？

A: 继承 `APIException` 类并在 Server 中注册异常处理器：

```python
class CustomException(APIException):
    def __init__(self, message: str):
        super().__init__(status_code=400, code="CUSTOM_ERROR", message=message)

server.app.add_exception_handler(CustomException, custom_exception_handler)
```

### Q: 如何添加认证中间件？

A: 创建自定义中间件并在路由或全局级别应用：

```python
class AuthMiddleware(BaseMiddleware):
    async def dispatch(self, request, call_next):
        # 认证逻辑
        if not request.headers.get("Authorization"):
            raise APIException(401, "AUTH_REQUIRED", "Authentication required")
        return await call_next(request)

# 全局应用
server.add_middleware(AuthMiddleware)

# 或在特定路由应用
@router.get("/protected", middlewares=[AuthMiddleware])
async def protected_route():
    pass
```

## ✨ 未来计划

- [ ] 添加更多企业级特性，如审计日志、缓存、分布式锁等
- [ ] 提供更多开箱即用的中间件，如 CORS、GZIP、JWT 认证等
- [ ] 支持更多数据库，如 MySQL、Redis、MongoDB 等
- [ ] 提供更多开箱即用的工具类，如分页、排序、搜索等
- [ ] 提供更多开箱即用的组件，如数据库、缓存、队列等


## 写在最后

本项目的功能还在开发中，可能相关的API还不稳定，随时可能调整。在使用的时候注意版本号。
另外，本项目是基于FastAPI的，所以需要熟悉FastAPI的开发者使用起来会更加得心应手。
本项目的测试部分有部分是基于AI生成的，可能存在一些问题，请谨慎使用。

---

⭐ 如果这个项目对你有帮助，请考虑给我们一个 Star！

## 配置文件格式支持

FastAPI Keystone 支持以下配置文件格式：

- `.json`（如 `config.example.json`）
- `.yaml` 或 `.yml`（如 `config.example.yaml`）

配置内容结构完全一致，推荐使用 YAML 或 JSON 任选其一。

### YAML 配置示例

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

logger:
  enable: true
  level: info
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  file: logs/app.log
  console: true

databases:
  default:
    enable: true
    host: 127.0.0.1
    port: 5432
    user: postgres
    password: postgres
    database: fastapi_keystone
  main:
    enable: true
    host: 127.0.0.1
    port: 5432
    user: postgres
    password: postgres
    database: fastapi_keystone

redis:
  host: 127.0.0.1
  port: 6379
  password: null
  database: 0
  max_connections: 10
  enable: true

email:
  smtp_host: smtp.gmail.com
  smtp_port: 587
  username: your_email@gmail.com
  password: your_password
  use_tls: true
  from_address: noreply@example.com

cache:
  type: redis
  ttl: 3600
  prefix: fastapi_keystone:
  enable_compression: false

auth:
  secret_key: your-secret-key-here
  algorithm: HS256
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7
  enable_refresh_token: true
```

### 加载配置用法

```python
from fastapi_keystone.config import load_config

# 自动根据后缀选择解析方式
config = load_config("config.example.yaml")
# 或
config = load_config("config.example.json")
```

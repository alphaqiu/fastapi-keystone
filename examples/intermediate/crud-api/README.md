# CRUD API 示例

这个示例展示如何使用 FastAPI Keystone 构建完整的 CRUD (Create, Read, Update, Delete) API。

## 功能特性

- 完整的 CRUD 操作
- 数据验证和序列化
- 依赖注入模式
- 业务逻辑分层
- 异常处理
- API 文档自动生成

## 文件结构

```
crud-api/
├── README.md
├── main.py              # 应用入口
├── requirements.txt     # 依赖列表
├── models/             # 数据模型
│   ├── __init__.py
│   └── user.py         # 用户模型
├── services/           # 业务逻辑层
│   ├── __init__.py
│   └── user_service.py # 用户服务
├── controllers/        # 控制器层
│   ├── __init__.py
│   └── user_controller.py # 用户控制器
└── config.json         # 配置文件
```

## API 端点

### 用户管理

- `GET /api/v1/users` - 获取用户列表
- `GET /api/v1/users/{user_id}` - 获取指定用户
- `POST /api/v1/users` - 创建新用户
- `PUT /api/v1/users/{user_id}` - 更新用户信息
- `DELETE /api/v1/users/{user_id}` - 删除用户

## 数据模型

```python
# 用户创建请求
{
    "name": "张三",
    "email": "zhangsan@example.com",
    "age": 25
}

# 用户响应
{
    "id": 1,
    "name": "张三",
    "email": "zhangsan@example.com",
    "age": 25,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

## 运行方式

```bash
# 安装依赖
uv pip install -r requirements.txt

# 运行应用
python main.py
```

## 测试 API

```bash
# 创建用户
curl -X POST "http://localhost:8000/api/v1/users" \
     -H "Content-Type: application/json" \
     -d '{"name": "张三", "email": "zhangsan@example.com", "age": 25}'

# 获取用户列表
curl "http://localhost:8000/api/v1/users"

# 获取指定用户
curl "http://localhost:8000/api/v1/users/1"

# 更新用户
curl -X PUT "http://localhost:8000/api/v1/users/1" \
     -H "Content-Type: application/json" \
     -d '{"name": "李四", "email": "lisi@example.com", "age": 30}'

# 删除用户
curl -X DELETE "http://localhost:8000/api/v1/users/1"
```

## 学习要点

1. **分层架构**: 控制器、服务、模型的分层设计
2. **依赖注入**: 使用 injector 管理依赖关系
3. **数据验证**: Pydantic 模型验证
4. **异常处理**: 自定义异常和全局异常处理
5. **API 设计**: RESTful API 设计原则
6. **文档生成**: FastAPI 自动生成 API 文档
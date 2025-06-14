# APIResponse 类型约束说明

## 概述

`APIResponse` 和 `APIResponseModel` 的泛型参数 `T` 现在具有类型约束，只允许以下三种类型：

1. **JSON 格式的类型** - 符合 [JSON 规范](https://www.json.org/json-en.html) 的基本类型
2. **继承自 BaseModel 的类型** - Pydantic BaseModel 的子类实例
3. **List[BaseModel] 的类型** - BaseModel 实例的列表

## 支持的类型

### 1. JSON 基本类型

根据 JSON 规范，支持以下基本类型：

```python
from src.fastapi_keystone.core.response import APIResponse

# 字符串
response = APIResponse.success(data="Hello World")

# 数字 (整数和浮点数)
response = APIResponse.success(data=42)
response = APIResponse.success(data=3.14)

# 布尔值
response = APIResponse.success(data=True)

# null (None)
response = APIResponse.success(data=None)

# 对象 (字典)
response = APIResponse.success(data={"key": "value", "count": 10})

# 数组 (列表)
response = APIResponse.success(data=[1, 2, 3, "hello", True])
```

### 2. BaseModel 类型

支持任何继承自 Pydantic BaseModel 的类：

```python
from pydantic import BaseModel
from src.fastapi_keystone.core.response import APIResponse, APIResponseModel

class User(BaseModel):
    id: int
    name: str
    email: str

# 使用 APIResponse
user = User(id=1, name="Alice", email="alice@example.com")
response = APIResponse.success(data=user)

# 使用 APIResponseModel
model = APIResponseModel[User](
    code=200, 
    message="success", 
    data=user
)
```

### 3. BaseModel 列表类型

支持 BaseModel 实例的列表：

```python
from typing import List
from pydantic import BaseModel
from src.fastapi_keystone.core.response import APIResponse, APIResponseModel

class Product(BaseModel):
    id: int
    title: str
    price: float

# BaseModel 列表
products = [
    Product(id=1, title="Laptop", price=999.99),
    Product(id=2, title="Mouse", price=29.99),
]

# 使用 APIResponse
response = APIResponse.success(data=products)

# 使用 APIResponseModel
model = APIResponseModel[List[Product]](
    code=200,
    message="success", 
    data=products
)
```

## 自动序列化

`APIResponse` 会自动处理 BaseModel 对象的序列化：

- **BaseModel 对象** → 自动调用 `model_dump()` 转换为字典
- **BaseModel 列表** → 自动将列表中的每个 BaseModel 对象转换为字典
- **JSON 类型** → 直接使用，无需转换

## 类型安全

使用 TypeVar 约束确保类型安全：

```python
from typing import TypeVar, Union, List, Dict, Any
from pydantic import BaseModel

# 类型约束定义
JSONPrimitive = Union[str, int, float, bool, None]
JSONValue = Union[
    JSONPrimitive,
    Dict[str, Any],  # JSON object
    List[Any],       # JSON array
]

T = TypeVar('T', bound=Union[
    JSONValue,           # JSON 格式的类型
    BaseModel,          # 继承自 BaseModel 的类型
    List[BaseModel],    # BaseModel 实例的列表
])
```

## 限制说明

1. **不支持嵌套 BaseModel 解析** - 暂时不支持 JSON 格式中嵌套 BaseModel 的自动解析
2. **列表类型限制** - 只支持 `List[BaseModel]`，不支持其他复杂的泛型组合
3. **JSON 兼容性** - 所有数据最终都必须能够序列化为 JSON 格式

## 使用示例

### FastAPI 路由中的使用

```python
from fastapi import FastAPI
from pydantic import BaseModel
from src.fastapi_keystone.core.response import APIResponse

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str

class User(BaseModel):
    id: int
    name: str
    email: str

@app.post("/users", response_class=APIResponse)
async def create_user(user_data: UserCreate):
    # 创建用户逻辑
    user = User(id=1, name=user_data.name, email=user_data.email)
    return APIResponse.success(data=user)

@app.get("/users", response_class=APIResponse)
async def list_users():
    users = [
        User(id=1, name="Alice", email="alice@example.com"),
        User(id=2, name="Bob", email="bob@example.com"),
    ]
    return APIResponse.success(data=users)
```

### 响应格式

所有响应都遵循统一的格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 实际数据内容
  }
}
```

这种类型约束确保了 API 响应的一致性和类型安全性，同时保持了足够的灵活性来处理各种数据类型。 
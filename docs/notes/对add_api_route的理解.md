下面详细介绍 FastAPI 中 `APIRouter.add_api_route` 的**全部参数含义**、**实际用法**，并重点解释 `dependencies` 的作用及其与中间件的区别。

---

## 1. `add_api_route` 方法简介

`add_api_route` 是 FastAPI `APIRouter`（以及 `FastAPI` 实例）用于**手动注册路由**的底层方法。  
它允许你以更细粒度的方式自定义路由的所有细节，等价于 `@router.get`、`@router.post` 等装饰器的底层实现。

**常见用法：**
```python
from fastapi import APIRouter

router = APIRouter()

def my_endpoint():
    return {"msg": "hello"}

router.add_api_route(
    path="/hello",
    endpoint=my_endpoint,
    methods=["GET"],
    response_model=dict,
)
```

---

## 2. 全部参数详解

（以 FastAPI 0.115.x 为例，部分参数可能随版本略有变化）

| 参数名                | 类型                | 说明                                                                                   |
|----------------------|---------------------|----------------------------------------------------------------------------------------|
| path                 | str                 | 路由路径，如 `/items/{item_id}`                                                        |
| endpoint             | Callable            | 视图函数/处理函数，接收请求参数并返回响应                                              |
| methods              | List[str]           | 支持的 HTTP 方法，如 `["GET", "POST"]`                                                 |
| response_model       | type                | 响应数据的 Pydantic 模型，用于自动校验和文档生成                                        |
| status_code          | int                 | 默认响应状态码                                                                         |
| tags                 | List[str]           | 路由标签，用于 OpenAPI 文档分组                                                        |
| dependencies         | Sequence[Depends]   | 依赖项列表，**用于依赖注入**，可实现参数校验、权限控制、通用逻辑等                      |
| summary              | str                 | 路由摘要，显示在 OpenAPI 文档                                                          |
| description          | str                 | 路由详细描述，显示在 OpenAPI 文档                                                      |
| response_description | str                 | 响应描述，显示在 OpenAPI 文档                                                          |
| responses            | dict                | 自定义响应描述和示例                                                                   |
| deprecated           | bool                | 是否标记为已废弃                                                                       |
| operation_id         | str                 | OpenAPI operationId，唯一标识                                                          |
| response_model_include | set                | 指定响应模型包含的字段                                                                 |
| response_model_exclude | set                | 指定响应模型排除的字段                                                                 |
| response_model_by_alias | bool              | 是否使用模型别名                                                                       |
| response_class       | Response            | 自定义响应类型（如 JSONResponse、HTMLResponse 等）                                      |
| name                 | str                 | 路由名称                                                                               |
| openapi_extra        | dict                | 额外的 OpenAPI 元数据                                                                  |
| callbacks            | List[APIRoute]      | 支持 OpenAPI callbacks                                                                 |
| generate_unique_id_function | Callable      | 自定义 operationId 生成函数                                                            |
| ...                  | ...                 | 还有一些高级参数，详见官方文档                                                         |

**官方文档**：[APIRouter.add_api_route 源码与参数](https://fastapi.tiangolo.com/advanced/using-request-directly/#add_api_route)

---

## 3. `dependencies` 参数详解

### 作用

- `dependencies` 是一个依赖项（`Depends` 实例）列表。
- 用于**依赖注入**，可以在请求处理前自动执行一组函数/校验/逻辑。
- 常用于：**认证、权限校验、参数预处理、通用逻辑（如数据库连接、日志、限流等）**。

### 用法示例

```python
from fastapi import Depends, APIRouter, HTTPException

def verify_token(token: str = Depends(get_token_from_header)):
    if token != "expected":
        raise HTTPException(status_code=401, detail="Invalid token")

router = APIRouter()
router.add_api_route(
    path="/secure",
    endpoint=secure_endpoint,
    methods=["GET"],
    dependencies=[Depends(verify_token)]
)
```
- 这样，每次访问 `/secure` 路由时，都会先执行 `verify_token`，不通过则直接返回 401。

### 特点

- `dependencies` 里的依赖**不会把返回值传递给 endpoint**，只用于副作用（如校验、抛异常、记录日志等）。
- 如果你需要把依赖的返回值传递给 endpoint，请在 endpoint 的参数列表中用 Depends。

---

## 4. `dependencies` 能否用作中间件？

- **依赖（dependencies）和中间件（middleware）有本质区别：**

| 对比项         | dependencies（依赖）                         | middleware（中间件）                   |
|----------------|---------------------------------------------|----------------------------------------|
| 作用范围       | 路由级别、全局级别（可细粒度控制）           | 全局应用于所有请求                     |
| 执行时机       | 路由参数解析后、endpoint 执行前              | 请求进入应用时（endpoint 之前/之后）   |
| 能否访问响应体 | 不能（只能在请求前做事）                     | 可以（可对请求和响应做处理）           |
| 用途           | 参数校验、权限、依赖注入、前置逻辑           | 日志、CORS、GZip、全局异常、追踪等     |
| 返回值         | 不传递给 endpoint（除非 endpoint 参数依赖）   | 可修改请求和响应                       |

- **dependencies 适合做**：认证、权限、参数校验、数据库 session、通用前置逻辑。
- **middleware 适合做**：全局日志、请求/响应修改、性能监控、全局异常处理等。

**结论**：  
- `dependencies` 不能完全替代中间件，但可以实现部分“前置处理”功能，且粒度更细。
- 如果你只需要在请求前做校验、注入、权限等，推荐用 `dependencies`。
- 如果需要处理请求和响应、全局拦截，推荐用 `middleware`。

---

## 5. 实际开发建议

- **认证/权限**：用 `dependencies`，可按路由、分组、全局灵活控制。
- **日志、CORS、GZip、全局异常**：用 `middleware`。
- **参数校验/通用依赖**：用 `dependencies`。

---

## 6. 参考文档

- [FastAPI 官方文档：Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI 官方文档：Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [APIRouter.add_api_route 源码](https://github.com/tiangolo/fastapi/blob/master/fastapi/routing.py)

---

如需具体用法示例或更复杂的依赖/中间件设计，欢迎继续提问！
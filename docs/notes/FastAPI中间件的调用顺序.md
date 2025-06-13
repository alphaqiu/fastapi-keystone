在 FastAPI（基于 Starlette）中，**中间件的执行顺序非常重要**，因为它决定了请求和响应处理流程中的逻辑先后顺序。

---

## 🧭 中间件的执行顺序规则

FastAPI 的中间件是 **按添加顺序“外层包裹”式执行**的。你可以把它想象成一层层洋葱：

- 请求进入时：从最外层中间件 → 依次向内执行。
- 到达路由函数后返回响应时：从最内层中间件 → 依次向外执行。

### 🔁 类似结构如下（洋葱模型）：

```
Middleware A (outer)
  Middleware B (middle)
    Middleware C (inner)
      Route handler
    ← 返回响应
  ← 返回响应
← 返回响应
```

---

## ✅ 示例说明

我们来看一个具体的例子：

```python
from fastapi import FastAPI
from fastapi.middleware import Middleware

class MiddlewareA:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        print("A - Before request")
        await self.app(scope, receive, send)
        print("A - After request")

class MiddlewareB:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        print("B - Before request")
        await self.app(scope, receive, send)
        print("B - After request")

app = FastAPI(middleware=[
    Middleware(MiddlewareA),
    Middleware(MiddlewareB),
])
```

### 📤 输出结果（GET /）：

```
A - Before request
B - Before request
[处理请求]
B - After request
A - After request
```

---

## 🧠 总结执行顺序要点：

| 阶段 | 执行顺序 |
|------|----------|
| 请求阶段（before `await self.app()`） | 按添加顺序执行（先 A，再 B） |
| 响应阶段（after `await self.app()`） | 按逆序执行（先 B，再 A） |

也就是说：

- 中间件 **越早添加，越在外层**
- 请求时先执行外层中间件的前置逻辑
- 响应时先执行内层中间件的后置逻辑

---

## 💡 实际应用中的注意事项

1. **认证中间件**通常应该放在前面（靠外层），确保非法请求尽早被拦截。
2. **日志或计时中间件**可以放在外层或内层，取决于你是否想包含其他中间件的耗时。
3. 如果你使用了多个第三方中间件，注意它们的顺序可能会影响行为（如 CORS、GZip、Session 等）。

---

## 🛠️ 如何控制中间件顺序？

有两种方式添加中间件：

### ✅ 方法一：通过构造器传入中间件列表（推荐）

```python
app = FastAPI(middleware=[
    Middleware(MiddlewareA),
    Middleware(MiddlewareB),
])
```

> ✅ 可以精确控制中间件的顺序。

---

### ✅ 方法二：使用 `add_middleware()` 多次添加

```python
app.add_middleware(MiddlewareA)
app.add_middleware(MiddlewareB)
```

> ⚠️ 注意：`add_middleware()` 是追加的方式，所以调用顺序决定执行顺序。


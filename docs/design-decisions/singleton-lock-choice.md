# 单例模式中选择 threading.Lock 的设计决策

## 🤔 问题背景

在实现 FastAPI Keystone 的单例模式时，我们面临一个重要的技术选择：使用 `threading.Lock` 还是 `asyncio.Lock` 来确保线程安全？

## 🎯 设计目标

1. **通用兼容性**：支持同步和异步环境
2. **简单易用**：不增加不必要的复杂性
3. **高性能**：适合单例创建的使用场景
4. **可靠性**：经过实战验证的技术方案

## ⚖️ 技术对比

### threading.Lock vs asyncio.Lock

| 特性 | threading.Lock | asyncio.Lock |
|------|---------------|--------------|
| 使用环境 | 同步 + 异步 | 仅异步 |
| 语法要求 | 简单 `with` | 需要 `async with` |
| 依赖关系 | 标准库，无额外依赖 | 需要事件循环 |
| 性能开销 | 低 | 稍高（异步调度） |
| 学习成本 | 低 | 中等 |
| 适用场景 | 通用 | 异步密集型 |

## 🔍 具体原因分析

### 1. **兼容性需求**

AppInjector 需要在多种场景中使用：

```python
# 场景1: 应用启动（同步）
def create_app():
    app = FastAPI()
    injector = AppInjector([DatabaseModule()])  # 必须支持同步
    return app

# 场景2: 依赖注入（可能同步或异步）
def get_injector() -> AppInjector:
    return AppInjector([AppModule()])  # 需要兼容性

# 场景3: 异步请求处理
async def api_handler(injector: AppInjector = Depends(get_injector)):
    service = injector.get_instance(UserService)  # 实例获取通常是同步的
    return await service.get_users()
```

**如果使用 asyncio.Lock 的问题：**
```python
# ❌ 这样会导致语法错误
def create_app():
    injector = await AppInjector([DatabaseModule()])  # SyntaxError! 同步函数不能用await

# ❌ 强制使用异步会让API变得复杂
async def get_injector() -> AppInjector:
    return await AppInjector([AppModule()])  # 不必要的异步化
```

### 2. **使用场景特征**

单例模式的典型使用特点：

- **低频操作**：通常在应用启动时创建一次
- **短暂锁定**：锁持有时间极短（仅实例创建期间）
- **非IO密集**：不涉及文件、网络等异步IO操作
- **混合环境**：需要在同步和异步代码中都能使用

这些特征使得 `threading.Lock` 更合适：

```python
# threading.Lock 适合的场景
with self._lock:  # 快速获取锁
    if cls not in instances:
        instances[cls] = cls(*args, **kwargs)  # 快速创建实例
# 立即释放锁，不阻塞其他操作
```

### 3. **性能考虑**

```python
# 性能测试结果（从示例中）
"""
单线程创建100个实例用时: 0.0000秒
5线程并发创建500个实例用时: 0.0004秒
所有实例都相同: True
"""
```

`threading.Lock` 在单例场景中表现出色：
- **微秒级锁定**：创建实例的时间极短
- **低开销**：不需要异步调度器
- **高并发**：支持多线程并发访问

### 4. **代码简洁性**

```python
# threading.Lock 版本 - 简洁直观
def singleton(cls):
    instances = {}
    lock = threading.Lock()
    
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance

# asyncio.Lock 版本 - 复杂且限制多
def async_singleton(cls):
    instances = {}
    lock = asyncio.Lock()
    
    async def get_instance(*args, **kwargs):  # 必须是异步函数
        if cls not in instances:
            async with lock:  # 必须用 async with
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance  # 返回的是异步函数，使用时必须 await
```

## 🏗️ 架构优势

### 统一的编程模型
```python
# 使用 threading.Lock，API 保持一致
injector = AppInjector([Module()])  # 同步和异步环境都可以这样用
service = injector.get_instance(Service)  # 实例获取也是同步的

# 如果使用 asyncio.Lock，API 会分裂
injector = await AppInjector.create([Module()])  # 异步创建
service = await injector.get_instance(Service)  # 异步获取，增加复杂性
```

### 更好的错误处理
```python
# threading.Lock - 错误处理简单
try:
    injector = AppInjector([Module()])
except Exception as e:
    logger.error(f"Failed to create injector: {e}")

# asyncio.Lock - 错误处理复杂
try:
    injector = await AppInjector.create([Module()])
except Exception as e:
    logger.error(f"Failed to create injector: {e}")
# 还需要处理异步上下文错误
```

## 🔬 技术深度分析

### 并发模型差异

**threading.Lock**：
- 基于操作系统线程
- 抢占式调度
- 适合 CPU 密集和混合场景
- 与 FastAPI 的线程池集成良好

**asyncio.Lock**：
- 基于协程调度
- 协作式调度  
- 适合 IO 密集场景
- 需要整个调用链都是异步的

### 内存和性能开销

```python
# threading.Lock 开销分析
threading.Lock()  # 系统级锁，开销极小
with lock:        # 直接系统调用，快速
    pass          # 操作完成，立即释放

# asyncio.Lock 开销分析  
asyncio.Lock()    # 需要事件循环支持
async with lock:  # 需要异步调度器介入
    await ...     # 可能涉及协程切换
```

## 📊 实际测试数据

基于 `examples/advanced/lock-comparison/main.py` 的测试结果：

| 测试场景 | threading.Lock | asyncio.Lock |
|---------|---------------|--------------|
| 同步环境使用 | ✅ 完美支持 | ❌ 无法使用 |
| 异步环境使用 | ✅ 完美支持 | ✅ 支持 |
| 混合环境 | ✅ 无缝切换 | ❌ 需要API分离 |
| 100次创建耗时 | ~0.0000秒 | ~0.0001秒 |
| 500次并发耗时 | ~0.0004秒 | 不适用 |

## 🎯 最终决策

**选择 `threading.Lock` 的原因总结：**

1. **✅ 通用兼容性**：同步异步环境都可用
2. **✅ API 简洁性**：不需要 await 语法
3. **✅ 性能优秀**：微秒级锁定，低开销
4. **✅ 学习成本低**：使用简单，易于理解
5. **✅ 生态兼容**：与 FastAPI 生态完美集成
6. **✅ 维护简单**：代码路径少，bug 风险低

**asyncio.Lock 的局限性：**

1. **❌ 环境限制**：只能在异步上下文使用
2. **❌ API 复杂**：强制异步化简单操作
3. **❌ 性能开销**：异步调度器介入
4. **❌ 学习门槛**：需要深度理解异步编程
5. **❌ 生态割裂**：与同步代码无法兼容

## 💡 设计哲学

> **"选择最适合的工具，而不是最新的工具"**

在单例模式中，我们的目标是：
- 确保唯一性（✅ 两种锁都能做到）
- 线程安全（✅ 两种锁都能做到）  
- 使用简单（✅ threading.Lock 更胜一筹）
- 性能优秀（✅ threading.Lock 更适合）
- 通用兼容（✅ threading.Lock 独有优势）

因此，`threading.Lock` 是单例模式的最佳选择。

## 🔄 何时考虑 asyncio.Lock

如果你的使用场景满足以下条件，可以考虑 `asyncio.Lock`：

1. **纯异步环境**：整个应用都是异步的
2. **IO 密集操作**：单例创建涉及异步 IO
3. **长时间锁定**：需要在锁内执行异步操作
4. **协程优化**：需要避免阻塞事件循环

```python
# 适合 asyncio.Lock 的场景示例
class AsyncDatabaseSingleton:
    async def __new__(cls):
        async with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                await cls._instance._async_init()  # 异步初始化
        return cls._instance
    
    async def _async_init(self):
        # 建立异步数据库连接
        self.connection = await asyncpg.connect(DATABASE_URL)
```

但对于 FastAPI Keystone 的 AppInjector，这些条件都不满足，所以 `threading.Lock` 是正确选择。

## 📚 参考资料

- [Python threading.Lock 文档](https://docs.python.org/3/library/threading.html#lock-objects)
- [Python asyncio.Lock 文档](https://docs.python.org/3/library/asyncio-sync.html#asyncio.Lock)
- [FastAPI 并发模型](https://fastapi.tiangolo.com/async/)
- [Single-threaded vs Multi-threaded in Python](https://realpython.com/python-concurrency/) 
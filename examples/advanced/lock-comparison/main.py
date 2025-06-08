"""
Lock 对比示例

展示 threading.Lock 和 asyncio.Lock 在单例模式中的差异
"""

import asyncio
import threading
import time


class ThreadingSingleton:
    """使用 threading.Lock 的单例"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    print(
                        f"[Threading] 创建实例在线程 {threading.current_thread().name}"
                    )
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, name: str = "default"):
        if not self._initialized:
            self.name = name
            self.created_at = time.time()
            self._initialized = True
            print(f"[Threading] 初始化实例: {name}")


class AsyncioSingleton:
    """使用 asyncio.Lock 的单例"""

    _instance = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls, name: str = "default"):
        """异步获取单例实例"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    print(f"[Asyncio] 创建实例")
                    cls._instance = cls.__new__(cls)
                    cls._instance.name = name
                    cls._instance.created_at = time.time()
                    cls._instance._initialized = True
                    print(f"[Asyncio] 初始化实例: {name}")
        return cls._instance


def test_threading_lock_compatibility():
    """测试 threading.Lock 的兼容性"""
    print("=== Threading.Lock 兼容性测试 ===")

    # 同步环境中使用
    print("\n1. 同步环境:")
    sync_instance1 = ThreadingSingleton("sync1")
    sync_instance2 = ThreadingSingleton("sync2")
    print(f"同步实例是否相同: {sync_instance1 is sync_instance2}")
    print(f"实例名称: {sync_instance1.name}")

    # 异步环境中使用
    async def async_test():
        print("\n2. 异步环境:")
        async_instance1 = ThreadingSingleton("async1")
        async_instance2 = ThreadingSingleton("async2")
        print(f"异步实例是否相同: {async_instance1 is async_instance2}")
        print(f"与同步实例是否相同: {async_instance1 is sync_instance1}")
        print(f"实例名称: {async_instance1.name}")

    asyncio.run(async_test())


async def test_asyncio_lock_limitations():
    """测试 asyncio.Lock 的限制"""
    print("\n=== Asyncio.Lock 限制测试 ===")

    # 异步环境中使用（正常）
    print("\n1. 异步环境:")
    async_instance1 = await AsyncioSingleton.get_instance("async1")
    async_instance2 = await AsyncioSingleton.get_instance("async2")
    print(f"异步实例是否相同: {async_instance1 is async_instance2}")
    print(f"实例名称: {async_instance1.name}")

    # 同步环境中的问题
    print("\n2. 同步环境限制:")
    print("❌ 无法在同步函数中直接使用 asyncio.Lock")
    print("❌ 必须通过 asyncio.run() 或在异步上下文中调用")

    # 演示错误用法（注释掉避免实际错误）
    print("\n错误示例（如果取消注释会报错）:")
    print("# def sync_function():")
    print(
        "#     instance = await AsyncioSingleton.get_instance('sync')  # SyntaxError!"
    )
    print("#     return instance")


def test_threading_lock_performance():
    """测试 threading.Lock 的性能"""
    print("\n=== 性能测试 ===")

    def create_instances():
        instances = []
        for i in range(100):
            instance = ThreadingSingleton(f"test{i}")
            instances.append(instance)
        return instances

    # 单线程性能
    start_time = time.time()
    instances = create_instances()
    single_thread_time = time.time() - start_time

    print(f"单线程创建100个实例用时: {single_thread_time:.4f}秒")
    print(f"所有实例都相同: {all(inst is instances[0] for inst in instances)}")

    # 多线程性能
    results = []

    def thread_worker():
        local_instances = create_instances()
        results.extend(local_instances)

    start_time = time.time()
    threads = []
    for i in range(5):
        thread = threading.Thread(target=thread_worker)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    multi_thread_time = time.time() - start_time

    print(f"5线程并发创建500个实例用时: {multi_thread_time:.4f}秒")
    print(f"所有实例都相同: {all(inst is results[0] for inst in results)}")


def test_real_world_scenario():
    """真实场景测试"""
    print("\n=== 真实场景测试 ===")

    # 模拟 FastAPI 应用启动
    def create_fastapi_app():
        """模拟 FastAPI 应用创建（同步）"""
        print("创建 FastAPI 应用...")
        injector = ThreadingSingleton("app_injector")
        print(f"依赖注入器创建: {injector.name}")
        return injector

    # 模拟异步请求处理
    async def handle_request():
        """模拟异步请求处理"""
        print("处理异步请求...")
        injector = ThreadingSingleton("request_injector")
        print(f"在请求中获取注入器: {injector.name}")
        return injector

    # 执行测试
    app_injector = create_fastapi_app()
    request_injector = asyncio.run(handle_request())

    print(f"应用注入器与请求注入器是否相同: {app_injector is request_injector}")


def demonstrate_why_threading_lock():
    """演示为什么选择 threading.Lock"""
    print("\n=== 为什么选择 threading.Lock ===")

    reasons = [
        "1. 兼容性: 可在同步和异步环境中使用",
        "2. 简单性: 不需要 await 关键字",
        "3. 性能: 对于单例创建场景足够高效",
        "4. 普适性: 不依赖特定的异步框架",
        "5. 稳定性: 成熟的线程同步机制",
    ]

    for reason in reasons:
        print(f"✅ {reason}")

    print("\nasynco.Lock 的限制:")
    limitations = [
        "1. 只能在异步上下文中使用",
        "2. 需要 await 语法",
        "3. 依赖事件循环",
        "4. 增加代码复杂性",
        "5. 不适合混合同步/异步场景",
    ]

    for limitation in limitations:
        print(f"❌ {limitation}")


if __name__ == "__main__":
    test_threading_lock_compatibility()
    asyncio.run(test_asyncio_lock_limitations())
    test_threading_lock_performance()
    test_real_world_scenario()
    demonstrate_why_threading_lock()

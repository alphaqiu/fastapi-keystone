"""
测试依赖注入器模块

测试 AppInjector 类的单例模式和依赖注入功能
"""

import threading
import time

from injector import Module, provider
from injector import singleton as injector_singleton

from fastapi_keystone.common.singleton import reset_singleton
from fastapi_keystone.core.di import AppInjector, get_app_injector


class MockService:
    """测试服务类"""

    def __init__(self, name: str = "test"):
        self.name = name
        self.initialized_at = time.time()

    def get_name(self) -> str:
        return self.name


class AnotherService:
    """另一个测试服务类"""

    def __init__(self, test_service: MockService):
        self.test_service = test_service
        self.initialized_at = time.time()

    def get_test_name(self) -> str:
        return self.test_service.get_name()


class TestModule(Module):
    """测试依赖注入模块"""

    @provider
    @injector_singleton
    def provide_test_service(self) -> MockService:
        return MockService("singleton_test")

    @provider
    @injector_singleton
    def provide_another_service(self, test_service: MockService) -> AnotherService:
        return AnotherService(test_service)


class EmptyModule(Module):
    """空的测试模块"""

    pass


class TestAppInjector:
    """测试 AppInjector 类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 重置单例状态，确保测试隔离
        reset_singleton(AppInjector)

    def test_singleton_behavior(self):
        """测试单例行为"""
        # 创建两个实例
        injector1 = AppInjector([TestModule()])
        injector2 = AppInjector([TestModule()])

        # 验证是同一个实例
        assert injector1 is injector2
        assert id(injector1) == id(injector2)

    def test_get_app_injector(self):
        """测试获取应用程序依赖注入器"""
        injector1 = AppInjector([TestModule()])
        injector: AppInjector = get_app_injector()
        assert id(injector) == id(injector1)
        svc = injector.get_instance(MockService)
        assert svc.name == "singleton_test"

    def test_singleton_with_different_modules(self):
        """测试不同模块配置的单例行为"""
        # 第一次创建
        injector1 = AppInjector([TestModule()])

        # 第二次创建时传入不同的模块，但应该返回同一个实例
        injector2 = AppInjector([TestModule(), EmptyModule()])

        # 仍然是同一个实例（单例模式保证）
        assert injector1 is injector2

    def test_get_instance(self):
        """测试获取实例功能"""
        injector = AppInjector([TestModule()])

        # 获取服务实例
        test_service = injector.get_instance(MockService)
        another_service = injector.get_instance(AnotherService)

        # 验证实例类型
        assert isinstance(test_service, MockService)
        assert isinstance(another_service, AnotherService)

        # 验证依赖注入正常工作
        assert another_service.test_service is test_service
        assert another_service.get_test_name() == "singleton_test"

    def test_get_instance_singleton_behavior(self):
        """测试依赖注入的单例行为"""
        injector = AppInjector([TestModule()])

        # 多次获取同一个服务
        service1 = injector.get_instance(MockService)
        service2 = injector.get_instance(MockService)

        # 验证是同一个实例（由 injector 的 @singleton 保证）
        assert service1 is service2
        assert service1.initialized_at == service2.initialized_at

    def test_get_injector(self):
        """测试获取底层注入器"""
        injector = AppInjector([TestModule()])

        # 获取底层注入器
        raw_injector = injector.get_injector()

        # 验证类型
        from injector import Injector

        assert isinstance(raw_injector, Injector)

        # 验证功能
        test_service = raw_injector.get(MockService)
        assert isinstance(test_service, MockService)
        assert test_service.name == "singleton_test"

    def test_thread_safety(self):
        """测试线程安全性"""
        results = []

        def create_injector():
            injector = AppInjector([TestModule()])
            results.append(injector)

        # 创建多个线程同时创建注入器
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_injector)
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有结果都是同一个实例
        assert len(results) == 10
        first_injector = results[0]
        for injector in results[1:]:
            assert injector is first_injector

    def test_empty_modules(self):
        """测试空模块列表"""
        injector = AppInjector([])

        # 验证可以正常创建
        assert injector is not None

        # 获取底层注入器
        raw_injector = injector.get_injector()
        assert raw_injector is not None

    def test_module_registration(self):
        """测试模块注册"""

        class CustomService:
            def __init__(self):
                self.value = "custom"

        class CustomModule(Module):
            @provider
            def provide_custom_service(self) -> CustomService:
                return CustomService()

        injector = AppInjector([CustomModule()])

        # 获取自定义服务
        custom_service = injector.get_instance(CustomService)
        assert isinstance(custom_service, CustomService)
        assert custom_service.value == "custom"

    def test_reset_singleton(self):
        """测试重置单例功能"""
        # 创建第一个注入器
        injector1 = AppInjector([TestModule()])
        first_id = id(injector1)

        # 重置单例
        reset_singleton(AppInjector)

        # 创建第二个注入器
        injector2 = AppInjector([TestModule()])
        second_id = id(injector2)

        # 验证是不同的实例
        assert first_id != second_id
        assert injector1 is not injector2

    def test_complex_dependency_chain(self):
        """测试复杂的依赖链"""
        from injector import inject

        class ServiceA:
            def __init__(self):
                self.name = "A"

        class ServiceB:
            @inject
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
                self.name = "B"

        class ServiceC:
            @inject
            def __init__(self, service_a: ServiceA, service_b: ServiceB):
                self.service_a = service_a
                self.service_b = service_b
                self.name = "C"

        class ComplexModule(Module):
            @provider
            @injector_singleton
            def provide_service_a(self) -> ServiceA:
                return ServiceA()

            @provider
            @injector_singleton
            def provide_service_b(self, service_a: ServiceA) -> ServiceB:
                return ServiceB(service_a)

            @provider
            @injector_singleton
            def provide_service_c(
                self, service_a: ServiceA, service_b: ServiceB
            ) -> ServiceC:
                return ServiceC(service_a, service_b)

        # 重置单例
        reset_singleton(AppInjector)

        injector = AppInjector([ComplexModule()])

        # 获取服务
        service_c = injector.get_instance(ServiceC)

        # 验证依赖链
        assert service_c.name == "C"
        assert service_c.service_a.name == "A"
        assert service_c.service_b.name == "B"
        assert (
            service_c.service_b.service_a is service_c.service_a
        )  # 共享同一个 ServiceA 实例

    def test_documentation_examples(self):
        """测试文档中的示例代码"""
        # 重置单例
        reset_singleton(AppInjector)

        # 无论创建多少次，都是同一个实例
        injector1 = AppInjector([TestModule()])
        injector2 = AppInjector([TestModule()])

        assert injector1 is injector2  # True

        # 获取服务实例
        user_service = injector1.get_instance(MockService)

        # 或者直接使用底层注入器
        raw_injector = injector1.get_injector()
        user_service2 = raw_injector.get(MockService)

        # 验证是同一个实例
        assert user_service is user_service2

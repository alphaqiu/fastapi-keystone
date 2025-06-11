"""测试服务器核心模块"""

from typing import Any
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from injector import Injector
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from fastapi_keystone.core.server import Server


class TestServer:
    """Server 类测试"""

    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        config = Mock()
        config.server = Mock()
        config.server.title = "Test App"
        config.server.description = "Test Description"
        config.server.version = "1.0.0"
        config.server.host = "localhost"
        config.server.port = 8000
        config.server.reload = False
        config.server.workers = 1
        return config

    @pytest.fixture
    def mock_manager(self, mock_config):
        manager = Mock()
        manager.get_instance.return_value = mock_config
        return manager

    @pytest.fixture
    def server(self, mock_manager):
        """创建服务器实例"""
        return Server(mock_manager)

    # ===== 初始化测试 =====

    def test_server_initialization(self, mock_manager, mock_config):
        """测试服务器初始化"""
        server = Server(mock_manager)

        assert server.config == mock_config
        assert server._on_startup == []
        assert server._on_shutdown == []
        assert server._middlewares == []

    # ===== 生命周期回调测试 =====

    def test_on_startup_registration(self, server):
        """测试启动回调注册"""

        async def startup_func(app, config):
            pass

        result = server.on_startup(startup_func)

        assert result == server  # 支持链式调用
        assert len(server._on_startup) == 1
        assert server._on_startup[0] == startup_func

    def test_on_shutdown_registration(self, server):
        """测试关闭回调注册"""

        async def shutdown_func(app, config):
            pass

        result = server.on_shutdown(shutdown_func)

        assert result == server  # 支持链式调用
        assert len(server._on_shutdown) == 1
        assert server._on_shutdown[0] == shutdown_func

    def test_on_startup_with_none(self, server):
        """测试启动回调注册None值"""
        result = server.on_startup(None)

        assert result == server
        assert len(server._on_startup) == 0

    def test_on_shutdown_with_none(self, server):
        """测试关闭回调注册None值"""
        result = server.on_shutdown(None)

        assert result == server
        assert len(server._on_shutdown) == 0

    def test_multiple_startup_callbacks(self, server):
        """测试多个启动回调"""

        async def startup1(app, config):
            pass

        async def startup2(app, config):
            pass

        server.on_startup(startup1).on_startup(startup2)

        assert len(server._on_startup) == 2
        assert server._on_startup[0] == startup1
        assert server._on_startup[1] == startup2

    # ===== 中间件测试 =====

    def test_add_middleware(self, server):
        """测试添加中间件"""

        class TestMiddleware(BaseHTTPMiddleware):
            def __init__(self, app: ASGIApp, **kwargs: Any):
                super().__init__(app, **kwargs)

        kwargs = {"param1": "value1"}

        result = server.add_middleware(TestMiddleware, **kwargs)

        assert result == server  # 支持链式调用
        assert len(server._middlewares) == 1
        assert server._middlewares[0] == (TestMiddleware, kwargs)

    def test_add_multiple_middlewares(self, server):
        """测试添加多个中间件"""

        class Middleware1(BaseHTTPMiddleware):
            pass

        class Middleware2(BaseHTTPMiddleware):
            pass

        server.add_middleware(Middleware1).add_middleware(Middleware2)

        assert len(server._middlewares) == 2

    # ===== setup_api 测试 =====

    @patch("fastapi_keystone.core.server.register_controllers")
    @patch("fastapi_keystone.core.server.logger")
    def test_setup_api_basic(self, mock_logger, mock_register, server):
        """测试基本API设置"""
        controllers = [Mock(), Mock()]

        with patch("fastapi_keystone.core.server.FastAPI") as mock_fastapi:
            mock_app = Mock(spec=FastAPI)
            mock_fastapi.return_value = mock_app

            app = server.setup_api(controllers)

            # 验证FastAPI实例化
            mock_fastapi.assert_called_once()
            call_kwargs = mock_fastapi.call_args[1]
            assert call_kwargs["title"] == server.config.server.title
            assert call_kwargs["description"] == server.config.server.description
            assert call_kwargs["version"] == server.config.server.version

            # 验证中间件添加
            assert mock_app.add_middleware.call_count >= 1  # 至少CORS中间件

            # 验证异常处理器添加
            assert mock_app.add_exception_handler.call_count >= 4

            # 验证控制器注册
            mock_register.assert_called_once_with(mock_app, server.manager, controllers)

            assert app == mock_app

    def test_enable_tenant_middleware(self, server):
        with patch("fastapi_keystone.core.server.FastAPI") as mock_fastapi:
            mock_app = Mock(spec=FastAPI)
            mock_fastapi.return_value = mock_app

            server.enable_tenant_middleware()
            server.setup_api([])

            # 验证 TenantMiddleware 被添加且 config 参数正确
            found = False
            for call in mock_app.add_middleware.call_args_list:
                if call[0][0].__name__ == "TenantMiddleware":
                    assert "config" in call[1]
                    found = True
            assert found

    @patch("fastapi_keystone.core.server.register_controllers")
    def test_setup_api_with_custom_middlewares(self, mock_register, server):
        """测试带自定义中间件的API设置"""

        class CustomMiddleware(BaseHTTPMiddleware):
            pass

        server.add_middleware(CustomMiddleware, param="value")

        controllers = []

        with patch("fastapi_keystone.core.server.FastAPI") as mock_fastapi:
            mock_app = Mock(spec=FastAPI)
            mock_fastapi.return_value = mock_app

            server.setup_api(controllers)

            # 验证自定义中间件被添加
            middleware_calls = mock_app.add_middleware.call_args_list
            # 应该有CORS中间件 + 自定义中间件
            assert len(middleware_calls) >= 2

    @patch("fastapi_keystone.core.server.register_controllers")
    def test_setup_api_with_kwargs(self, mock_register, mock_manager, mock_config):
        """测试带kwargs的API设置"""
        custom_kwargs = {"docs_url": "/custom-docs", "openapi_url": "/custom-openapi"}
        server = Server(mock_manager)

        controllers = []

        with patch("fastapi_keystone.core.server.FastAPI") as mock_fastapi:
            mock_app = Mock(spec=FastAPI)
            mock_fastapi.return_value = mock_app

            server.setup_api(controllers, **custom_kwargs)

            # 验证kwargs被传递给FastAPI
            call_kwargs = mock_fastapi.call_args[1]
            assert call_kwargs["docs_url"] == "/custom-docs"
            assert call_kwargs["openapi_url"] == "/custom-openapi"

    # ===== 生命周期集成测试 =====

    @pytest.mark.asyncio
    async def test_lifespan_startup_and_shutdown(self, server, mock_config):
        """测试生命周期管理"""
        startup_called = []
        shutdown_called = []
        async def startup_func(app, config):
            startup_called.append((app, config))
        async def shutdown_func(app, config):
            shutdown_called.append((app, config))
        server.on_startup(startup_func).on_shutdown(shutdown_func)
        mock_app = Mock(spec=FastAPI)
        with patch("fastapi_keystone.core.server.FastAPI") as mock_fastapi:
            mock_fastapi.return_value = mock_app
            server.setup_api([])
            lifespan_func = mock_fastapi.call_args[1]["lifespan"]
            async with lifespan_func(mock_app):
                assert len(startup_called) == 1
                assert startup_called[0] == (mock_app, mock_config)
            assert len(shutdown_called) == 1
            assert shutdown_called[0] == (mock_app, mock_config)

    @pytest.mark.asyncio
    async def test_startup_callback_exception_handling(self, server, mock_config):
        """测试启动回调异常处理"""
        async def failing_startup(app, config):
            raise ValueError("Startup failed")
        server.on_startup(failing_startup)
        mock_app = Mock(spec=FastAPI)
        with patch("fastapi_keystone.core.server.FastAPI") as mock_fastapi:
            mock_fastapi.return_value = mock_app
            server.setup_api([])
            lifespan_func = mock_fastapi.call_args[1]["lifespan"]
            with pytest.raises(ValueError, match="Startup failed"):
                async with lifespan_func(mock_app):
                    pass

    # ===== run 方法测试 =====

    # @patch("fastapi_keystone.core.server.uvicorn")
    # def test_run_method(self, mock_uvicorn, server):
    #     """测试run方法"""
    #     mock_app = Mock(spec=FastAPI)

    #     server.run(mock_app)

    #     mock_uvicorn.run.assert_called_once_with(
    #         mock_app,
    #         host=server.config.server.host,
    #         port=server.config.server.port,
    #         reload=server.config.server.reload,
    #         workers=server.config.server.workers,
    #     )

    # @patch("fastapi_keystone.core.server.uvicorn")
    # @patch("fastapi_keystone.core.server.logger")
    # def test_run_method_logging(self, mock_logger, mock_uvicorn, server):
    #     """测试run方法日志记录"""
    #     mock_app = Mock(spec=FastAPI)

    #     server.run(mock_app)

    #     # 验证日志记录
    #     mock_logger.info.assert_called_with(
    #         f"Running server on {server.config.server.host}:{server.config.server.port}"
    #     )

    # ===== 链式调用测试 =====

    def test_method_chaining(self, server):
        """测试方法链式调用"""

        async def startup_func(app, config):
            pass

        async def shutdown_func(app, config):
            pass

        class TestMiddleware(BaseHTTPMiddleware):
            pass

        # 测试链式调用
        result = (
            server.on_startup(startup_func)
            .on_shutdown(shutdown_func)
            .add_middleware(TestMiddleware)
        )

        assert result == server
        assert len(server._on_startup) == 1
        assert len(server._on_shutdown) == 1
        assert len(server._middlewares) == 1

    # ===== 错误处理测试 =====

    # ===== 集成测试 =====

    # @patch("fastapi_keystone.core.routing.register_controllers")
    # @patch("fastapi_keystone.core.server.uvicorn")
    # def test_full_server_setup_and_run(self, mock_uvicorn, mock_register, server):
    #     """测试完整的服务器设置和运行流程"""

    #     # 设置回调和中间件
    #     async def startup_func(app, config):
    #         pass

    #     class TestMiddleware(BaseHTTPMiddleware):
    #         pass

    #     controllers = [Mock(), Mock()]
    #     mock_injector = Mock(spec=Injector)

    #     # 配置服务器
    #     server.on_startup(startup_func).add_middleware(TestMiddleware)

    #     with patch("fastapi_keystone.core.server.FastAPI") as mock_fastapi:
    #         mock_app = Mock(spec=FastAPI)
    #         mock_fastapi.return_value = mock_app

    #         # 设置API
    #         app = server.setup_api(mock_injector, controllers)

    #         # 运行服务器
    #         server.run(app)

    #         # 验证所有步骤
    #         mock_fastapi.assert_called_once()
    #         mock_register.assert_called_once_with(mock_app, mock_injector, controllers)
    #         mock_uvicorn.run.assert_called_once()

    # ===== 边界情况测试 =====

    def test_empty_controllers_list(self, server):
        """测试空控制器列表"""
        with patch(
            "fastapi_keystone.core.server.register_controllers"
        ) as mock_register:
            with patch("fastapi_keystone.core.server.FastAPI") as mock_fastapi:
                mock_app = Mock(spec=FastAPI)
                mock_fastapi.return_value = mock_app

                server.setup_api([])

                mock_register.assert_called_once_with(mock_app, server.manager, [])

    def test_no_callbacks_registered(self, server):
        """测试未注册回调的情况"""
        with patch("fastapi_keystone.core.server.FastAPI") as mock_fastapi:
            mock_app = Mock(spec=FastAPI)
            mock_fastapi.return_value = mock_app

            app = server.setup_api([])

            # 应该仍然可以正常设置
            assert app == mock_app
            assert len(server._on_startup) == 0
            assert len(server._on_shutdown) == 0

    def test_no_middlewares_added(self, server):
        """测试未添加中间件的情况"""
        with patch("fastapi_keystone.core.server.FastAPI") as mock_fastapi:
            mock_app = Mock(spec=FastAPI)
            mock_fastapi.return_value = mock_app

            server.setup_api([])

            # 应该至少添加CORS中间件
            assert mock_app.add_middleware.call_count >= 1

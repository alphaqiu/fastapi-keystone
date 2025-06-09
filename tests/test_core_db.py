from contextlib import asynccontextmanager
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fastapi_keystone.core.db import (
    TENANT_DATABASES,
    TENANT_ENGINES,
    TENANT_SESSION_FACTORIES,
    close_db_connections,
    get_db_session,
    get_tenant_db_url,
    get_tenant_session_factory,
    get_tx_session,
    init_tenants,
    tenant_id_context,
)


class TestInitTenants:
    """测试租户初始化功能"""

    def test_init_tenants_success(self, capsys):
        """测试成功初始化租户配置"""
        tenant_configs = {
            "tenant1": "sqlite+aiosqlite:///tenant1.db",
            "tenant2": "sqlite+aiosqlite:///tenant2.db",
        }

        init_tenants(tenant_configs)

        # 检查 TENANT_DATABASES 是否被正确设置（因为init_tenants使用global赋值）
        from fastapi_keystone.core.db import TENANT_DATABASES

        assert TENANT_DATABASES == tenant_configs
        captured = capsys.readouterr()
        assert "Initialized with 2 tenants." in captured.out

    def test_init_tenants_empty(self, capsys):
        """测试初始化空租户配置"""
        init_tenants({})

        assert TENANT_DATABASES == {}
        captured = capsys.readouterr()
        assert "Initialized with 0 tenants." in captured.out


class TestGetTenantDbUrl:
    """测试获取租户数据库URL功能"""

    def setup_method(self):
        """每个测试前的设置"""
        init_tenants(
            {
                "tenant1": "sqlite+aiosqlite:///tenant1.db",
                "tenant2": "postgresql+asyncpg://user:pass@localhost/tenant2",
            }
        )

    def test_get_existing_tenant_url(self):
        """测试获取已存在租户的URL"""
        url = get_tenant_db_url("tenant1")
        assert url == "sqlite+aiosqlite:///tenant1.db"

        url = get_tenant_db_url("tenant2")
        assert url == "postgresql+asyncpg://user:pass@localhost/tenant2"

    def test_get_nonexistent_tenant_url(self):
        """测试获取不存在租户的URL时抛出异常"""
        with pytest.raises(
            ValueError, match="Tenant 'nonexistent' configuration not found."
        ):
            get_tenant_db_url("nonexistent")


class TestGetTenantSessionFactory:
    """测试获取租户会话工厂功能"""

    def setup_method(self):
        """每个测试前的设置"""
        # 清理缓存
        TENANT_ENGINES.clear()
        TENANT_SESSION_FACTORIES.clear()
        init_tenants(
            {
                "tenant1": "sqlite+aiosqlite:///:memory:",
            }
        )

    def teardown_method(self):
        """每个测试后的清理"""
        TENANT_ENGINES.clear()
        TENANT_SESSION_FACTORIES.clear()

    @patch("fastapi_keystone.core.db.create_async_engine")
    @patch("fastapi_keystone.core.db.async_sessionmaker")
    def test_create_new_session_factory(self, mock_sessionmaker, mock_engine, capsys):
        """测试创建新的会话工厂"""
        mock_engine_instance = MagicMock()
        mock_sessionmaker_instance = MagicMock()

        mock_engine.return_value = mock_engine_instance
        mock_sessionmaker.return_value = mock_sessionmaker_instance

        factory = get_tenant_session_factory("tenant1")

        # 验证创建了引擎和会话工厂
        mock_engine.assert_called_once_with("sqlite+aiosqlite:///:memory:", echo=True)
        mock_sessionmaker.assert_called_once_with(
            bind=mock_engine_instance, class_=AsyncSession, expire_on_commit=False
        )

        # 验证缓存
        assert TENANT_ENGINES["tenant1"] == mock_engine_instance
        assert TENANT_SESSION_FACTORIES["tenant1"] == mock_sessionmaker_instance
        assert factory == mock_sessionmaker_instance

        # 验证日志
        captured = capsys.readouterr()
        assert "Created session factory for tenant 'tenant1'." in captured.out

    @patch("fastapi_keystone.core.db.create_async_engine")
    @patch("fastapi_keystone.core.db.async_sessionmaker")
    def test_get_cached_session_factory(self, mock_sessionmaker, mock_engine, capsys):
        """测试获取已缓存的会话工厂"""
        # 第一次调用
        factory1 = get_tenant_session_factory("tenant1")

        # 第二次调用
        factory2 = get_tenant_session_factory("tenant1")

        # 应该返回相同的实例
        assert factory1 == factory2

        # 引擎只应该创建一次
        assert mock_engine.call_count == 1
        assert mock_sessionmaker.call_count == 1

        # 日志只应该打印一次
        captured = capsys.readouterr()
        assert captured.out.count("Created session factory for tenant 'tenant1'.") == 1

    def test_get_session_factory_nonexistent_tenant(self):
        """测试获取不存在租户的会话工厂"""
        with pytest.raises(
            ValueError, match="Tenant 'nonexistent' configuration not found."
        ):
            get_tenant_session_factory("nonexistent")


class TestGetTxSession:
    """测试事务会话功能"""

    def setup_method(self):
        """每个测试前的设置"""
        TENANT_ENGINES.clear()
        TENANT_SESSION_FACTORIES.clear()
        init_tenants(
            {
                "tenant1": "sqlite+aiosqlite:///:memory:",
            }
        )

    def teardown_method(self):
        """每个测试后的清理"""
        TENANT_ENGINES.clear()
        TENANT_SESSION_FACTORIES.clear()

    @pytest.mark.asyncio
    async def test_get_tx_session_no_tenant_context(self):
        """测试没有租户上下文时抛出异常"""
        with pytest.raises(
            RuntimeError, match="Tenant ID not found in request context."
        ):
            async with get_tx_session():
                pass

    @pytest.mark.asyncio
    @patch("fastapi_keystone.core.db.get_tenant_session_factory")
    async def test_get_tx_session_success(self, mock_get_factory):
        """测试成功获取事务会话"""
        # 设置租户上下文
        tenant_id_context.set("tenant1")

        # 创建模拟会话
        mock_session = AsyncMock(spec=AsyncSession)
        mock_begin = AsyncMock()
        mock_session.begin.return_value = mock_begin
        mock_begin.__aenter__ = AsyncMock(return_value=mock_begin)
        mock_begin.__aexit__ = AsyncMock(return_value=None)

        # 创建模拟会话工厂 - 需要正确配置异步上下文管理器
        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_get_factory.return_value = mock_factory

        # 测试使用会话
        async with get_tx_session() as session:
            assert session == mock_session

        # 验证调用
        mock_get_factory.assert_called_once_with("tenant1")
        mock_factory.assert_called_once()
        mock_session.begin.assert_called_once()


class TestGetDbSession:
    """测试普通数据库会话功能"""

    def setup_method(self):
        """每个测试前的设置"""
        TENANT_ENGINES.clear()
        TENANT_SESSION_FACTORIES.clear()
        init_tenants(
            {
                "tenant1": "sqlite+aiosqlite:///:memory:",
            }
        )

    def teardown_method(self):
        """每个测试后的清理"""
        TENANT_ENGINES.clear()
        TENANT_SESSION_FACTORIES.clear()

    @pytest.mark.asyncio
    async def test_get_db_session_no_tenant_context(self):
        """测试没有租户上下文时抛出异常"""
        with pytest.raises(
            RuntimeError, match="Tenant ID not found in request context."
        ):
            async with get_db_session():
                pass

    @pytest.mark.asyncio
    @patch("fastapi_keystone.core.db.get_tenant_session_factory")
    async def test_get_db_session_success(self, mock_get_factory):
        """测试成功获取数据库会话"""
        # 设置租户上下文
        tenant_id_context.set("tenant1")

        # 创建模拟会话
        mock_session = AsyncMock(spec=AsyncSession)

        # 创建模拟会话工厂 - 需要正确配置异步上下文管理器
        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_get_factory.return_value = mock_factory

        # 测试使用会话
        async with get_db_session() as session:
            assert session == mock_session

        # 验证调用
        mock_get_factory.assert_called_once_with("tenant1")
        mock_factory.assert_called_once()


class TestCloseDbConnections:
    """测试关闭数据库连接功能"""

    def setup_method(self):
        """每个测试前的设置"""
        TENANT_ENGINES.clear()
        TENANT_SESSION_FACTORIES.clear()

    def teardown_method(self):
        """每个测试后的清理"""
        TENANT_ENGINES.clear()
        TENANT_SESSION_FACTORIES.clear()

    @pytest.mark.asyncio
    async def test_close_db_connections_empty(self, capsys):
        """测试关闭空的数据库连接"""
        await close_db_connections()

        captured = capsys.readouterr()
        assert "All tenant database connections closed." in captured.out

    @pytest.mark.asyncio
    async def test_close_db_connections_with_engines(self, capsys):
        """测试关闭有引擎的数据库连接"""
        # 创建模拟引擎
        mock_engine1 = AsyncMock()
        mock_engine2 = AsyncMock()

        TENANT_ENGINES["tenant1"] = mock_engine1
        TENANT_ENGINES["tenant2"] = mock_engine2

        await close_db_connections()

        # 验证每个引擎都被处理
        mock_engine1.dispose.assert_called_once()
        mock_engine2.dispose.assert_called_once()

        captured = capsys.readouterr()
        assert "All tenant database connections closed." in captured.out


class TestTenantContextIntegration:
    """测试租户上下文集成功能"""

    def setup_method(self):
        """每个测试前的设置"""
        TENANT_ENGINES.clear()
        TENANT_SESSION_FACTORIES.clear()
        init_tenants(
            {
                "tenant1": "sqlite+aiosqlite:///:memory:",
                "tenant2": "sqlite+aiosqlite:///:memory:",
            }
        )

    def teardown_method(self):
        """每个测试后的清理"""
        TENANT_ENGINES.clear()
        TENANT_SESSION_FACTORIES.clear()

    @pytest.mark.asyncio
    @patch("fastapi_keystone.core.db.get_tenant_session_factory")
    async def test_different_tenants_get_different_sessions(self, mock_get_factory):
        """测试不同租户获取不同的会话工厂"""
        # 修改 mock_factory 为 MagicMock 来正确处理异步上下文
        mock_factory1 = MagicMock()
        mock_factory2 = MagicMock()

        def side_effect(tenant_id):
            if tenant_id == "tenant1":
                return mock_factory1
            elif tenant_id == "tenant2":
                return mock_factory2

        mock_get_factory.side_effect = side_effect

        # 模拟会话
        mock_session1 = AsyncMock(spec=AsyncSession)
        mock_session2 = AsyncMock(spec=AsyncSession)

        mock_factory1.return_value.__aenter__ = AsyncMock(return_value=mock_session1)
        mock_factory1.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_factory2.return_value.__aenter__ = AsyncMock(return_value=mock_session2)
        mock_factory2.return_value.__aexit__ = AsyncMock(return_value=None)

        # 测试租户1
        tenant_id_context.set("tenant1")
        async with get_db_session() as session1:
            assert session1 == mock_session1

        # 测试租户2
        tenant_id_context.set("tenant2")
        async with get_db_session() as session2:
            assert session2 == mock_session2

        # 验证调用了正确的工厂
        assert mock_get_factory.call_count == 2
        mock_get_factory.assert_any_call("tenant1")
        mock_get_factory.assert_any_call("tenant2")

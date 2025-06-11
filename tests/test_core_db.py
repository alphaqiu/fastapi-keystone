from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_keystone.core.db import Database


@pytest.fixture
def mock_config():
    # 构造一个模拟的 Config 和 DatabaseConfig
    mock_db_config = MagicMock()
    mock_db_config.keys.return_value = ["default"]
    mock_db_config.__getitem__.return_value = MagicMock(
        enable=True,
        dsn=MagicMock(return_value="sqlite+aiosqlite:///:memory:"),
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_timeout=10,
        extra={},
    )
    mock_config = MagicMock()
    mock_config.databases = mock_db_config
    return mock_config

@pytest.mark.asyncio
@patch("fastapi_keystone.core.db.async_sessionmaker")
@patch("fastapi_keystone.core.db.create_async_engine")
async def test_get_db_session_success(mock_create_engine, mock_sessionmaker, mock_config):
    db = Database(mock_config)
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_session = AsyncMock(spec=AsyncSession)
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session
    mock_factory.return_value.__aexit__.return_value = None
    mock_sessionmaker.return_value = mock_factory

    async with db.get_db_session("default") as session:
        assert session == mock_session
    mock_create_engine.assert_called_once()
    mock_sessionmaker.assert_called_once()
    mock_factory.assert_called_once()

@pytest.mark.asyncio
@patch("fastapi_keystone.core.db.async_sessionmaker")
@patch("fastapi_keystone.core.db.create_async_engine")
async def test_get_tx_session_commit(mock_create_engine, mock_sessionmaker, mock_config):
    db = Database(mock_config)
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_begin = AsyncMock()
    mock_session.begin.return_value = mock_begin
    mock_begin.__aenter__.return_value = mock_begin
    mock_begin.__aexit__.return_value = None
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session
    mock_factory.return_value.__aexit__.return_value = None
    mock_sessionmaker.return_value = mock_factory

    async with db.get_tx_session("default") as session:
        assert session == mock_session
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_not_awaited()

@pytest.mark.asyncio
@patch("fastapi_keystone.core.db.async_sessionmaker")
@patch("fastapi_keystone.core.db.create_async_engine")
async def test_get_tx_session_rollback_on_exception(mock_create_engine, mock_sessionmaker, mock_config):
    db = Database(mock_config)
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_begin = AsyncMock()
    mock_session.begin.return_value = mock_begin
    mock_begin.__aenter__.return_value = mock_begin
    mock_begin.__aexit__.return_value = None
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session
    mock_factory.return_value.__aexit__.return_value = None
    mock_sessionmaker.return_value = mock_factory

    class CustomError(Exception):
        pass

    with pytest.raises(CustomError):
        async with db.get_tx_session("default") as session:
            assert session == mock_session
            raise CustomError()
    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_awaited_once()

@pytest.mark.asyncio
@patch("fastapi_keystone.core.db.async_sessionmaker")
@patch("fastapi_keystone.core.db.create_async_engine")
async def test_get_db_session_no_tenant(mock_create_engine, mock_sessionmaker, mock_config):
    db = Database(mock_config)
    # 不传 tenant_id，ContextVar 也未设置，应抛异常
    with pytest.raises(RuntimeError):
        async with db.get_db_session():
            pass

@pytest.mark.asyncio
@patch("fastapi_keystone.core.db.async_sessionmaker")
@patch("fastapi_keystone.core.db.create_async_engine")
async def test_close_db_connections(mock_create_engine, mock_sessionmaker, mock_config):
    db = Database(mock_config)
    mock_engine1 = AsyncMock()
    mock_engine2 = AsyncMock()
    db.tenant_engines["t1"] = mock_engine1
    db.tenant_engines["t2"] = mock_engine2
    await db.close_db_connections()
    mock_engine1.dispose.assert_awaited_once()
    mock_engine2.dispose.assert_awaited_once()

from __future__ import annotations

from contextlib import asynccontextmanager
from contextvars import ContextVar
from logging import getLogger
from threading import Lock
from typing import Any, AsyncGenerator, Dict, Optional

from injector import Module, provider, singleton
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from fastapi_keystone.config import Config

logger = getLogger(__name__)

# 使用 ContextVar 来存储当前请求的租户ID，确保在异步环境中上下文安全
tenant_id_context: ContextVar[str] = ContextVar("tenant_id_context")


class Base(DeclarativeBase):
    """
    Declarative base class for all ORM models.
    """

    pass
    # 所有数据库表模型都继承自 Base


class DatabaseModule(Module):
    """
    Injector module for providing Database dependency.
    """

    @provider
    def provide_database(self, config: Config) -> "Database":
        """
        Provide a Database instance for dependency injection.

        Args:
            config (Config): The application configuration.

        Returns:
            Database: The database manager instance.
        """
        return Database(config)


@singleton
class Database:
    """
    Multi-tenant async database manager.

    Manages SQLAlchemy async engines and sessions for each tenant.

    Attributes:
        tenant_engines (Dict[str, Any]): Cached SQLAlchemy engines per tenant.
        tenant_session_factories (Dict[str, async_sessionmaker[AsyncSession]]): Cached session factories per tenant.
        tenant_configs (Dict[str, Any]): Tenant database config mapping.
    """

    def __init__(self, config: Config):
        """
        Initialize the Database manager.

        Args:
            config (Config): The application configuration.
        """
        self.lock = Lock()
        # 缓存每个租户的数据库引擎，避免重复创建
        self.tenant_engines: Dict[str, Any] = {}
        self.tenant_session_factories: Dict[str, async_sessionmaker[AsyncSession]] = {}

        # 存储租户数据库配置信息 {tenant_id: db_url}
        db_config = config.databases
        self.tenant_configs = {
            tenant_name: db_config[tenant_name]
            for tenant_name in db_config.keys()
            if getattr(db_config[tenant_name], "enabled", False)
        }

    def get_tenant_session_factory(
        self, tenant_id: str = "default"
    ) -> async_sessionmaker[AsyncSession]:
        """
        Get or create a session factory for the given tenant.

        Args:
            tenant_id (str): The tenant identifier.

        Returns:
            async_sessionmaker[AsyncSession]: The session factory for the tenant.
        """
        with self.lock:
            if tenant_id in self.tenant_session_factories:
                return self.tenant_session_factories[tenant_id]

            config = self.tenant_configs.get(tenant_id)
            if not config:
                raise ValueError(f"Tenant '{tenant_id}' configuration not found.")

            engine = create_async_engine(
                url=config.dsn(),
                echo=config.echo,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_timeout=config.pool_timeout,
                pool_pre_ping=True,
                pool_use_lifo=True,
                **config.extra,
            )
            self.tenant_engines[tenant_id] = engine
            self.tenant_session_factories[tenant_id] = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self.tenant_session_factories[tenant_id]

    @asynccontextmanager
    async def get_tx_session(
        self, tenant_id: Optional[str] = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a transactional session for the given tenant.

        Args:
            tenant_id (Optional[str]): The tenant identifier. If None, uses context var.

        Yields:
            AsyncSession: The transactional session.
        """
        if tenant_id is None:
            try:
                tenant_id = tenant_id_context.get()
            except LookupError:
                raise RuntimeError("Tenant ID not found in request context.")

        session_factory = self.get_tenant_session_factory(tenant_id)
        async with session_factory() as session:
            async with session.begin():
                try:
                    # 将 session 交给调用方
                    yield session
                    # 如果调用方代码块正常结束，提交事务
                    await session.commit()
                except Exception as e:
                    # 如果调用方代码块出现任何异常，回滚事务
                    await session.rollback()
                    # 将异常重新抛出，以便上层代码能感知到
                    raise e

    @asynccontextmanager
    async def get_db_session(
        self, tenant_id: Optional[str] = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a plain session for the given tenant (no auto transaction).

        Args:
            tenant_id (Optional[str]): The tenant identifier. If None, uses context var.

        Yields:
            AsyncSession: The session.
        """
        if tenant_id is None:
            try:
                tenant_id = tenant_id_context.get()
            except LookupError:
                raise RuntimeError("Tenant ID not found in request context.")

        session_factory = self.get_tenant_session_factory(tenant_id)
        async with session_factory() as session:
            yield session
            # async with 会自动调用 session.close()，无需显式调用

    async def close_db_connections(self):
        """
        Close all tenant database connections (dispose engines).
        """
        for engine in self.tenant_engines.values():
            await engine.dispose()
        logger.info("All tenant database connections closed.")

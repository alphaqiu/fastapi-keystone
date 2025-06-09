from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, AsyncGenerator, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 使用 ContextVar 来存储当前请求的租户ID，确保在异步环境中上下文安全
tenant_id_context: ContextVar[str] = ContextVar("tenant_id_context")

# 缓存每个租户的数据库引擎，避免重复创建
TENANT_ENGINES: Dict[str, Any] = {}
TENANT_SESSION_FACTORIES: Dict[str, async_sessionmaker[AsyncSession]] = {}

# 存储租户数据库配置信息 {tenant_id: db_url}
TENANT_DATABASES: Dict[str, str] = {}


def init_tenants(tenant_configs: Dict[str, str]):
    """在应用启动时初始化租户数据库配置"""
    global TENANT_DATABASES
    TENANT_DATABASES = tenant_configs
    print(f"Initialized with {len(TENANT_DATABASES)} tenants.")


def get_tenant_db_url(tenant_id: str) -> str:
    """获取指定租户的数据库URL"""
    db_url = TENANT_DATABASES.get(tenant_id)
    if not db_url:
        raise ValueError(f"Tenant '{tenant_id}' configuration not found.")
    return db_url


def get_tenant_session_factory(tenant_id: str) -> async_sessionmaker[AsyncSession]:
    """按需为租户创建并缓存数据库会话工厂"""
    if tenant_id not in TENANT_SESSION_FACTORIES:
        db_url = get_tenant_db_url(tenant_id)
        engine = create_async_engine(db_url, echo=True)
        TENANT_ENGINES[tenant_id] = engine
        TENANT_SESSION_FACTORIES[tenant_id] = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
        print(f"Created session factory for tenant '{tenant_id}'.")
    return TENANT_SESSION_FACTORIES[tenant_id]


@asynccontextmanager
async def get_tx_session(
    tenant_id: Optional[str] = tenant_id_context.get(),
) -> AsyncGenerator[AsyncSession, None]:
    """
    依赖注入函数，用于获取当前租户的数据库会话

    自动事务管理：
    - 正常执行完成时自动commit
    - 发生异常时自动rollback
    """
    # try:
    #     tenant_id = tenant_id_context.get()
    # except LookupError:
    #     raise RuntimeError("Tenant ID not found in request context.")
    if tenant_id is None or tenant_id.strip() == "":
        tenant_id = "default"

    session_factory = get_tenant_session_factory(tenant_id)
    async with session_factory() as session:
        async with session.begin():
            yield session
            # session.begin() 会自动管理commit/rollback，无需手动处理


@asynccontextmanager
async def get_db_session(
    tenant_id: Optional[str] = tenant_id_context.get(),
) -> AsyncGenerator[AsyncSession, None]:
    """依赖注入函数，用于获取当前租户的数据库会话"""
    if tenant_id is None or tenant_id.strip() == "":
        tenant_id = "default"

    session_factory = get_tenant_session_factory(tenant_id)
    async with session_factory() as session:
        yield session
        # async with 会自动调用 session.close()，无需显式调用


async def close_db_connections():
    """在应用关闭时，关闭所有租户的数据库连接"""
    for engine in TENANT_ENGINES.values():
        await engine.dispose()
    print("All tenant database connections closed.")

from logging import getLogger
from typing import (
    Annotated,
    Any,
    AsyncGenerator,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Union,
)

from sqlalchemy.engine.row import RowMapping
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select, func, select
from typing_extensions import Doc

from fastapi_keystone.core.exceptions import DatabaseConnectionError, DatabaseError
from fastapi_keystone.core.request import PageRequest

logger = getLogger(__name__)


class HasSession(Protocol):
    async def get_db_session(
        self, tenant_id: Optional[str] = None
    ) -> AsyncGenerator[AsyncSession, None]: ...


class PageQueryMixin:
    """
    Mixin for paginated query support.

    Requires the main class to implement get_db_session.
    """

    async def page_query(
        self: HasSession,
        stmt: Annotated[
            Select[Tuple[Any, ...]],
            Doc("The paginated SQLAlchemy select statement."),
        ],
        *,
        total_stmt: Annotated[
            Optional[Select[Tuple[Any, ...]]],
            Doc("The statement for total count. If None, use stmt as count query."),
        ] = None,
        page_request: Annotated[
            Optional[PageRequest],
            Doc("Pagination request, including page number and page size."),
        ] = None,
        order_by: Annotated[
            Optional[List[Any]],
            Doc("Order by fields. If total_stmt is None, order is applied to stmt."),
        ] = None,
        use_custom_columns: Annotated[
            bool,
            Doc("If True, return ORM objects; else return RowMapping."),
        ] = False,
        tenant_id: str = "default",
    ) -> Tuple[Sequence[Union[Any, RowMapping]], int]:
        """
        Perform a paginated query.

        Args:
            stmt (Select): The paginated SQLAlchemy select statement.
            total_stmt (Optional[Select]): The statement for total count. If None, use stmt as count query.
            page_request (Optional[PageRequest]): Pagination request, including page number and page size.
            order_by (Optional[List[Any]]): Order by fields. If total_stmt is None, order is applied to stmt.
            use_custom_columns (bool): If True, return ORM objects; else return RowMapping.
            tenant_id (str): Tenant identifier.

        Returns:
            Tuple[Sequence[Union[Any, RowMapping]], int]: Query result and total count.

        Example:
            >>> items, total = await obj.page_query(stmt, page_request=PageRequest(page=1, size=10))
        """
        limit: Optional[int] = None
        offset: Optional[int] = None
        if page_request:
            limit = page_request.size
            offset = (page_request.page - 1) * limit
        if limit is None or limit <= 0:
            limit = 10
        if offset is None or offset < 0:
            offset = 0

        async with self.get_db_session(tenant_id) as session:  # type: ignore
            # 获取总记录数
            query_stmt = stmt
            if total_stmt is not None:
                query_stmt = total_stmt
            count_stmt = select(func.count()).select_from(query_stmt.subquery())
            logger.debug(
                f"Count SQL: {count_stmt.compile(compile_kwargs={'literal_binds': True})}"
            )
            total: int = 0
            try:
                result_total = await session.scalar(count_stmt)
                if result_total is None or result_total < 0:
                    total = 0
                else:
                    total = result_total
            except OperationalError as e:
                logger.error(f"数据库连接错误: {e}")
                raise DatabaseConnectionError(f"数据库连接错误: {e}")
            except SQLAlchemyError as e:
                logger.error(f"数据库操作错误: {e}")
                raise DatabaseError(f"数据库操作错误: {e}")
            except Exception as e:
                logger.error(f"获取总记录数失败: {e}")
                raise DatabaseError(f"获取总记录数失败: {e}") from e

            # 添加排序
            if order_by:
                for field in order_by:
                    stmt = stmt.order_by(field)
            stmt = stmt.offset(offset).limit(limit)
            logger.debug(
                f"Paging SQL: {stmt.compile(compile_kwargs={'literal_binds': True})}"
            )
            try:
                result = await session.execute(stmt)
                if use_custom_columns:
                    items = result.scalars().all()
                else:
                    items = result.mappings().all()
                return items, total

            except OperationalError as e:
                logger.error(f"数据库连接错误: {e}")
                raise DatabaseConnectionError(f"数据库连接错误: {e}")
            except SQLAlchemyError as e:
                logger.error(f"数据库操作错误: {e}")
                raise DatabaseError(f"数据库操作错误: {e}")
            except Exception as e:
                logger.error(f"查询失败: {e}")
                raise DatabaseError(f"查询失败: {e}") from e
        return [], 0

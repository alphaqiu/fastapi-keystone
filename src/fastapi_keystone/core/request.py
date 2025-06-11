from fastapi import Query
from pydantic import BaseModel, ConfigDict


class PageRequest(BaseModel):
    """
    分页请求模型
    """

    page: int = Query(1, title="页码", description="页码")
    size: int = Query(10, title="每页数量", ge=1, description="每页数量")

    model_config = ConfigDict(
        from_attributes=True, json_schema_extra={"example": {"page": 1, "size": 10}}
    )

import asyncio
from logging import getLogger
from typing import List, Optional

from fastapi import Depends, FastAPI, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from fastapi_keystone.config import Config
from fastapi_keystone.core.app import AppManager
from fastapi_keystone.core.middlewares import request_context
from fastapi_keystone.core.routing import group, router

logger = getLogger(__name__)

# 保存所有客户端连接的队列
clients: List[asyncio.Queue] = []


async def event_generator():
    queue = asyncio.Queue()
    clients.append(queue)
    try:
        while True:
            data = await queue.get()
            yield f"data: {data}\n\n"
    except asyncio.CancelledError:
        clients.remove(queue)
        raise


async def broadcast_message(message: str):
    for queue in clients:
        await queue.put(message)


async def send_chat_messages():
    while True:
        await asyncio.sleep(1)  # 每秒发送一条模拟消息
        message = "新聊天消息：这是一条测试消息"
        await broadcast_message(message)


async def do_init_on_startup(app: FastAPI, config: Config):
    asyncio.create_task(send_chat_messages())
    logger.info("Starting server, init on startup callbacks")


async def do_init_on_shutdown(app: FastAPI, config: Config):
    logger.info("Stopping server, init on shutdown callbacks")


async def custom_middleware(request: Request) -> Optional[str]:
    logger.info(f"Request: {request}")
    custom_header = request.headers.get("X-Custom-Header")
    if custom_header:
        logger.info(f"Custom header: {custom_header}")
    else:
        logger.info("No custom header")
    return custom_header


class DemoModel(BaseModel):
    name: str
    age: int


@group("/api/v1")
class DemoController:
    def __init__(self):
        pass

    @router.get("/hello", dependencies=[Depends(custom_middleware)])
    async def get_hello(
        self,
        name: str = Query(default="World", title="姓名", description="姓名"),
    ) -> DemoModel:
        return DemoModel(name=name, age=18)

    @router.get("/hello/sse")
    async def sse(self, request: Request):
        logger.info("SSE connection established")
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @router.get("/hello2")
    async def get_hello2(
        self,
        name: str = Query(default="World", title="姓名", description="姓名"),
    ):
        ctx = request_context.get()
        req_id = ctx.get("x_request_id")
        tenant_id = ctx.get("tenant_id")
        val = ctx.get("value")
        logger.info(f"Request ID: {req_id=}")
        logger.info(f"Tenant ID: {tenant_id=}")
        logger.info(f"Value: {val=}")
        return {"message": f"Hello from fastapi-keystone-demo! {name}"}


# 添加一个独立的控制器处理静态文件请求
class StaticController:
    def __init__(self):
        pass

    @router.get("/sw.js")
    async def service_worker(self):
        """处理 Service Worker 请求，返回空的 JS 内容"""
        return Response(
            content="// Empty service worker",
            media_type="application/javascript",
            status_code=200,
        )

    @router.get("/favicon.ico")
    async def favicon(self):
        """处理 favicon 请求，避免 404"""
        return Response(status_code=204)


def main(stand_alone: bool = False) -> Optional[FastAPI]:
    manager = AppManager(config_path="config.json", modules=[])
    server = manager.setup_server(controllers=[DemoController, StaticController])
    app = (
        server.on_startup(do_init_on_startup)
        .on_shutdown(do_init_on_shutdown)
        .enable_etag(max_content_length=1024 * 1024)
        .enable_simple_trace(trace_logger=logger)
        .enable_tenant()
        .setup_api(controllers=[DemoController, StaticController])
    )
    if stand_alone:
        server.run(app)
    return app


if __name__ == "__main__":
    main(True)
else:
    app = main(False)

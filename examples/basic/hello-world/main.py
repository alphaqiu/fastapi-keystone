from typing import Optional

from fastapi import Depends, FastAPI, Query, Request, Response

from fastapi_keystone.config import Config
from fastapi_keystone.core import AppManager
from fastapi_keystone.core.routing import group, router


async def do_init_on_startup(app: FastAPI, config: Config):
    print("Starting server, init on startup callbacks")


async def do_init_on_shutdown(app: FastAPI, config: Config):
    print("Stopping server, init on shutdown callbacks")


async def custom_middleware(request: Request) -> Optional[str]:
    print(f"Request: {request}")
    custom_header = request.headers.get("X-Custom-Header")
    if custom_header:
        print(f"Custom header: {custom_header}")
    else:
        print("No custom header")
    return custom_header


@group("/api/v1")
class DemoController:
    def __init__(self):
        pass

    @router.get("/hello", dependencies=[Depends(custom_middleware)])
    def get_hello(
        self,
        name: str = Query(default="World", title="姓名", description="姓名"),
    ):
        return {"message": f"Hello from fastapi-keystone-demo! {name}"}

    @router.get("/hello2")
    def get_hello2(
        self,
        name: str = Query(default="World", title="姓名", description="姓名"),
    ):
        return {"message": f"Hello from fastapi-keystone-demo! {name}"}


# 添加一个独立的控制器处理静态文件请求
class StaticController:
    def __init__(self):
        pass

    @router.get("/sw.js")
    def service_worker(self):
        """处理 Service Worker 请求，返回空的 JS 内容"""
        return Response(
            content="// Empty service worker",
            media_type="application/javascript",
            status_code=200,
        )

    @router.get("/favicon.ico")
    def favicon(self):
        """处理 favicon 请求，避免 404"""
        return Response(status_code=204)


def main(stand_alone: bool = False) -> Optional[FastAPI]:
    manager = AppManager(config_path="config.json", modules=[])
    server = manager.get_server()
    app = (
        server.on_startup(do_init_on_startup)
        .on_shutdown(do_init_on_shutdown)
        .setup_api(controllers=[DemoController, StaticController])
    )
    if stand_alone:
        server.run(app)
    return app


if __name__ == "__main__":
    main(True)
else:
    app = main(False)

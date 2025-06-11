"""
FastAPI Keystone Hello World 示例

这是最简单的 FastAPI Keystone 应用，展示：
1. 基础路由定义
2. 标准化API响应
3. 最小配置启动
"""

from fastapi import Query
from injector import Injector

from fastapi_keystone.config import ConfigModule
from fastapi_keystone.core.app import AppManager, get_app_injector
from fastapi_keystone.core.response import APIResponse
from fastapi_keystone.core.routing import group, router
from fastapi_keystone.core.server import Server


@group("/api/v1")
class IndexController:
    @router.get("/")
    async def root(self) -> APIResponse[dict]:
        return APIResponse.success(
            {
                "message": "欢迎使用 FastAPI Keystone!",
                "framework": "FastAPI Keystone",
                "version": "0.0.2",
            }
        )

    @router.get("/hello/{name}")
    async def hello(
        self, name: str = Query(..., description="用户姓名")
    ) -> APIResponse[dict]:
        return APIResponse.success(
            {"message": f"Hello, {name}!", "timestamp": "2024-01-01T00:00:00Z"}
        )

    @router.get("/health")
    async def health_check(self) -> APIResponse[dict]:
        return APIResponse.success(
            {"status": "healthy", "service": "fastapi-keystone-hello-world"}
        )


def main():
    """应用主入口"""
    # 创建配置（使用默认配置）
    injector = AppManager([ConfigModule("config.json")])
    # 创建服务器
    server = injector.get_instance(Server)

    async def on_startup(app, config):
        print("🚀 启动 FastAPI Keystone Hello World 应用...")

    async def on_shutdown(app, config):
        print("🛑 停止 FastAPI Keystone Hello World 应用...")

    app = (
        server.on_startup(on_startup)
        .on_shutdown(on_shutdown)
        .enable_tenant_middleware()
        .setup_api(injector, [IndexController])
    )

    # 启动服务器
    print("🚀 启动 FastAPI Keystone Hello World 应用...")
    print("📖 API 文档: http://localhost:8000/docs")
    print("🔍 交互式文档: http://localhost:8000/redoc")
    server.run(app)


if __name__ == "__main__":
    main()

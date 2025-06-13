from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from fastapi_keystone.core.middlewares import TenantMiddleware, request_context


@pytest.fixture
def app_factory():
    def _app(tenant_enabled=True):
        app = FastAPI()
        config = MagicMock()
        config.server.tenant_enabled = tenant_enabled
        app.add_middleware(TenantMiddleware, config=config)

        @app.get("/")
        async def root(): # type: ignore[reportUnusedFunction]
            return {"tenant_id": request_context.get().get("tenant_id", None)}
        return app
    return _app

@pytest.mark.asyncio
async def test_tenant_id_from_header(app_factory):
    app = app_factory(tenant_enabled=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/", headers={"X-Tenant-ID": "foo"})
        assert resp.status_code == 200
        assert resp.json()["tenant_id"] == "foo"

@pytest.mark.asyncio
async def test_missing_tenant_id_header(app_factory):
    app = app_factory(tenant_enabled=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 400
        assert resp.text == "X-Tenant-ID header is required"

@pytest.mark.asyncio
async def test_tenant_mode_disabled(app_factory):
    app = app_factory(tenant_enabled=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json()["tenant_id"] == "default"

@pytest.mark.asyncio
async def test_non_http_scope():
    # 直接调用 __call__，scope type 非 http
    config = MagicMock()
    config.server.tenant_enabled = True
    called = {}
    async def dummy_app(scope, receive, send):
        called["called"] = True
    middleware = TenantMiddleware(dummy_app, config)
    scope = {"type": "websocket"}
    async def dummy_receive():
        return {"type": "websocket.connect"}
    async def dummy_send(msg):
        pass
    await middleware(scope, dummy_receive, dummy_send)
    assert called["called"] 
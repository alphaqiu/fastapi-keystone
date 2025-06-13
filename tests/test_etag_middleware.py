
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from src.fastapi_keystone.core.middlewares import EtagMiddleware, request_context


@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(EtagMiddleware)

    @app.get("/json")
    async def get_json(): # type: ignore
        return {"msg": "hello"}

    @app.get("/text")
    async def get_text(): # type: ignore
        return "plain text"

    return app

def test_etag_set_and_match(app):
    token = request_context.set({"etag_enabled": True})
    client = TestClient(app)
    # 第一次请求，获取 ETag
    resp = client.get("/json")
    assert resp.status_code == 200
    etag = resp.headers.get("etag")
    assert etag is not None

    # 第二次带 If-None-Match
    resp2 = client.get("/json", headers={"If-None-Match": etag})
    assert resp2.status_code == 304
    request_context.reset(token)

def test_etag_not_match(app):
    token = request_context.set({"etag_enabled": True})
    client = TestClient(app)
    # 带错误的 If-None-Match
    resp = client.get("/json", headers={"If-None-Match": "wrong"})
    assert resp.status_code == 200
    assert resp.headers.get("etag") is not None
    request_context.reset(token)
def test_non_json_response(app):
    client = TestClient(app)
    resp = client.get("/text")
    assert resp.status_code == 200
    # 不应有 etag
    assert "etag" not in resp.headers
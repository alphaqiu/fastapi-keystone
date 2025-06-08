from typing import Literal

from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from injector import Injector

from fastapi_keystone.core.routing import group, register_controllers, router

app = FastAPI()


def custom_dependency(request: Request) -> Literal["test"]:
    return "test"


@group("/api")
class CustomController:
    def __init__(self):
        pass

    @router.get("/test", dependencies=[Depends(custom_dependency)])
    def test(self):
        return {"message": "Hello, World!"}

    @router.get("/test2")
    def test2(self):
        return {"message": "Hello, World!2"}


def test_routing():
    injector = Injector()
    register_controllers(app, injector, [CustomController])
    client = TestClient(app)
    response = client.get("/api/test")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}
    response = client.get("/api/test2")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!2"}

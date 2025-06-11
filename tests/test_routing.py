from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from fastapi_keystone.core.app import AppManager
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
    app = FastAPI()
    example_config_path = Path(__file__).parent.parent / "config.example.json"
    manager = AppManager(config_path=str(example_config_path), modules=[])
    register_controllers(app, manager, [CustomController])
    client = TestClient(app)
    response = client.get("/api/test")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}
    response = client.get("/api/test2")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!2"}

from pathlib import Path

import pytest
from injector import Injector
from rich import print

from config import Config, ConfigModule, load_config


@pytest.mark.asyncio
async def test_load_config():
    # __file__ = ./fastapi-keystone/tests/test_config.py
    # Path(__file__).parent = ./fastapi-keystone/tests
    # Path(__file__).parent.parent = ./fastapi-keystone
    example_config_path = Path(__file__).parent.parent / "config.example.json"
    print(example_config_path)
    config: Config = await load_config(str(example_config_path))
    assert config is not None
    assert config.server.host == "0.0.0.0"
    assert config.server.port == 8080
    assert config.server.run_mode == "dev"
    assert len(config.databases.keys()) > 1

    print(config)

def test_config_module():
    example_config_path = Path(__file__).parent.parent / "config.example.json"
    print(example_config_path)
    injector = Injector([ConfigModule(config_path=str(example_config_path))])
    config: Config = injector.get(Config)
    assert config is not None
    assert config.server.host == "0.0.0.0"
    assert config.server.port == 8080
    assert config.server.run_mode == "dev"
    assert len(config.databases.keys()) > 1
    config2: Config = injector.get(Config)
    assert id(config) == id(config2)

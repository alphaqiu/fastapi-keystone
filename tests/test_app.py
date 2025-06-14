from pathlib import Path

import pytest

from fastapi_keystone.core.app import create_app_manager


@pytest.mark.asyncio
async def test_app_manager():
    example_config_path = Path(__file__).parent.parent / "config.example.json"
    app_manager = create_app_manager(config_path=str(example_config_path))
    assert app_manager is not None
    server = app_manager.setup_server(controllers=[])
    assert server is not None
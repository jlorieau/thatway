import pytest

from thatway import Config
from thatway.manager import settings as s


@pytest.fixture(autouse=True)
def config():
    """Retrieve and reset the config object"""
    Config._instance = None
    config = Config()
    return config


@pytest.fixture
def settings():
    """Retrieve and reset the settings object"""
    s.clear()
    yield s

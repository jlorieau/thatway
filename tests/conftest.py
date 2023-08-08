import pytest

from thatway import Config


@pytest.fixture(autouse=True)
def config():
    """Retrieve and reset the config object"""
    Config._instance = None
    config = Config()
    return config

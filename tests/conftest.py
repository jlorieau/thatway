from typing import Iterator

import pytest

from thatway.manager import SettingsManager, clear
from thatway.manager import settings as s


@pytest.fixture
def settings() -> Iterator[SettingsManager]:
    """Retrieve and reset the settings object"""
    clear(s)
    yield s

from typing import Iterator

import pytest

from thatway.manager import SettingsNamespace
from thatway.manager import settings as s


@pytest.fixture
def settings() -> Iterator[SettingsNamespace]:
    """Retrieve and reset the settings object"""
    s.clear()
    yield s

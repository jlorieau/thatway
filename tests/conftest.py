import re
from typing import Callable, Iterator

import pytest

from thatway.manager import SettingsManager, clear
from thatway.manager import settings as s


@pytest.fixture
def match_strings() -> Callable[[str, str], bool]:
    """Match two strings, including stripping of newlines"""
    regex1 = re.compile(r"(  )+")  # Remove blocks of 2-spaces

    def _match_strings(s1: str, s2: str) -> bool:
        subbed1 = regex1.sub("", s1).strip()  # remove space at the ends
        subbed2 = regex1.sub("", s2).strip()

        return subbed1 == subbed2

    _match_strings.__doc__ = match_strings.__doc__
    return _match_strings


@pytest.fixture
def settings() -> Iterator[SettingsManager]:
    """Retrieve and reset the settings object"""
    clear(s)
    yield s

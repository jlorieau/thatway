import re
from doctest import DocTestRunner
from typing import Callable, Iterator

import pytest

from thatway import Setting, SettingsManager, clear


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
    manager = SettingsManager()
    clear(manager)
    yield manager


@pytest.fixture
def settings_set1(settings: SettingsManager) -> Iterator[SettingsManager]:
    """Retrieve a settings object configure with data (set 1)"""

    class TestClass:
        attribute = Setting(3, "My attribute")
        attribute2 = Setting("string", "A string")

    settings.database_ip = Setting("128.0.0.1", "IP address of database")

    yield settings


# Modify the doctest runner to strip backticks from the end of the doctest string.
# This is needed to remove code blocks with doctests in Markdown files.

orig_run = DocTestRunner.run


def run(self, test, *args, **kwargs):
    for example in test.examples:
        # Remove ```
        example.want = example.want.replace("```\n", "")
        example.exc_msg = example.exc_msg and example.exc_msg.replace("```\n", "")

    return orig_run(self, test, *args, **kwargs)


DocTestRunner.run = run

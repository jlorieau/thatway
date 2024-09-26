"""Tests for the SettingsManager"""

from pathlib import Path
from typing import Callable

import pytest

from thatway.manager import SettingsManager, load_toml, save_toml
from thatway.setting import Setting


def test_settings_manager_load_toml(settings: SettingsManager, tmp_path: Path) -> None:
    """Test the :func:`save_toml` function"""

    # Create seetings
    class TestClass:
        attribute = Setting(3, "My attribute")
        attribute2 = Setting("string", "A string")

    settings.database_ip = Setting("128.0.0.1", "IP address of database")

    # Write TOML file
    tmp_toml = tmp_path / "test.toml"
    tmp_toml.write_text(
        """
    database_ip = "0.0.0.1" # IP address of database
    [test_manager.TestClass]
    attribute = 13 # My attribute
    attribute2 = "new string" # A string
    """
    )

    # Load and check settings
    load_toml(tmp_toml, settings)

    assert settings.database_ip.default == "0.0.0.1"
    assert settings.test_manager.TestClass.attribute.default == 13
    assert settings.test_manager.TestClass.attribute2.default == "new string"


def test_settings_manager_save_toml(
    settings: SettingsManager, tmp_path: Path, match_strings: Callable[[str, str], bool]
) -> None:
    """Test the :func:`save_toml` function"""
    tmp_toml = tmp_path / "test.toml"
    tmp_toml.touch()

    # Create some settings
    class TestClass:
        attribute = Setting(3, "My attribute")
        attribute2 = Setting("string", "A string")

    settings.database_ip = Setting("128.0.0.1", "IP address of database")
    settings.missing = "Not inserted"  # not a setting

    # Save to toml format
    save_toml(tmp_toml, settings)

    # Check the saved file
    key = """
    database_ip = "128.0.0.1" # IP address of database
    [test_manager.TestClass]
    attribute = 3 # My attribute
    attribute2 = "string" # A string
    """
    toml = tmp_toml.read_text()

    assert match_strings(toml, key)

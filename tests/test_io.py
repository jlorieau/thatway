"""
Test SettingsManager io functions.
"""

from pathlib import Path
from typing import Callable

import pytest

from thatway import Setting, SettingException, SettingsManager, load, pprint, save


def test_settings_manager_pprint(
    settings_set1: SettingsManager,
    match_strings: Callable[[str, str], bool],
    capsys: pytest.CaptureFixture,
) -> None:
    """Test the pretty-print functionality"""
    pprint(settings_set1)

    stdout = capsys.readouterr().out
    key = """
    database_ip = "128.0.0.1" # IP address of database
    [conftest.TestClass]
    attribute = 3 # My attribute
    attribute2 = "string" # A string
    """

    assert match_strings(stdout, key)


def test_settings_manager_load_toml(settings: SettingsManager, tmp_path: Path) -> None:
    """Test the SettingsManager load_toml method."""

    # Create settings
    class TestClass:
        attribute = Setting(3, "My attribute")
        attribute2 = Setting("string", "A string")

    settings.database_ip = Setting("128.0.0.1", "IP address of database")

    # Retrieve constants
    module_name = TestClass.__module__

    # Write TOML file
    tmp_toml = tmp_path / "test.toml"
    tmp_toml.write_text(
        f"""
    database_ip = "0.0.0.1" # IP address of database
    [{module_name}.TestClass]
    attribute = 13 # My attribute
    attribute2 = "new string" # A string
    """
    )

    # Load and check settings
    load(tmp_toml, settings)

    module_settings = getattr(settings, module_name)

    assert settings.database_ip.value == "0.0.0.1"
    assert module_settings.TestClass.attribute.value == 13
    assert module_settings.TestClass.attribute2.value == "new string"


def test_settings_manager_load_toml_missing(
    settings: SettingsManager, tmp_path: Path
) -> None:
    """Test the SettingsManager load_toml method with a missing setting."""

    # Create settings
    # Write TOML file
    tmp_toml = tmp_path / "test.toml"
    tmp_toml.write_text('database_ip = "0.0.0.1" # IP address of database')

    # Loading setting will raise an exception because the setting doesn't exist
    with pytest.raises(SettingException):
        load(tmp_toml, settings)


def test_settings_manager_save_toml(
    settings: SettingsManager, tmp_path: Path, match_strings: Callable[[str, str], bool]
) -> None:
    """Test the SettingsManager save_toml function"""
    tmp_toml = tmp_path / "test.toml"
    tmp_toml.touch()

    # Create some settings
    class TestClass:
        attribute = Setting(3, "My attribute")
        attribute2 = Setting("string", "A string")

    settings.database_ip = Setting("128.0.0.1", "IP address of database")

    # Save to toml format
    save(tmp_toml, settings)

    # Check the saved file
    module_name = TestClass.__module__
    key = f"""
    database_ip = "128.0.0.1" # IP address of database
    [{module_name}.TestClass]
    attribute = 3 # My attribute
    attribute2 = "string" # A string
    """
    toml = tmp_toml.read_text()

    assert match_strings(toml, key)

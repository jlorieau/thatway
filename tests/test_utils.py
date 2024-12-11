"""Tests for utility functions"""

from thatway import Setting, SettingsManager, clear, locate


def test_settings_manager_clear(settings: SettingsManager) -> None:
    """Test the SettingsManager clear function"""
    # Add some settings, managers and non-settings

    settings.sub.value1 = Setting(5, "A setting")
    settings.value2 = Setting(5, "Another setting")

    assert len(settings) == 2

    # Clear and check that the settings manager is reset
    clear(settings)

    assert len(settings) == 0
    assert not isinstance(settings.sub.value1, Setting)
    assert not isinstance(settings.value2, Setting)


def test_settings_manager_locate(settings_set1: SettingsManager) -> None:
    """Test the SettingsManager location function"""
    locations = locate(settings_set1)

    assert len(locations) == 1
    filename = list(locations.keys())[0]
    assert filename.endswith("conftest.py")
    assert len(locations[filename]) == 3  # There are 3 settings in settings_set1

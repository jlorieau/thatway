"""Tests for utility functions"""

from thatway import Setting, SettingsManager, clear


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

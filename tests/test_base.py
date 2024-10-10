"""Tests for Setting and SettingsManager classes"""

import pytest

from thatway import ConditionFailure, Setting, SettingsManager
from thatway.conditions import is_positive


def test_setting_delete(settings: SettingsManager) -> None:
    """Test the :cls:`Setting` :meth:`__delete` method"""

    # 1. Try a setting owned by a class
    class Test:
        s = Setting("t", desc="A string")

        def __init__(self) -> None:
            self.s = "new string"

    test = Test()

    # The modified value is returned before delete
    assert test.s == "new string"

    # The default value is returned after a delete
    del test.s
    assert test.s == "t"

    # Deleting again raises an exception
    with pytest.raises(AttributeError):
        del test.s

    assert test.s == "t"


def test_setting_insert(settings: SettingsManager) -> None:
    """Test the :cls:`Setting` :meth:`_insert` method."""

    # 1. Try a setting owned by a class
    class Test:
        s = Setting("t", desc="A string")

        def __init__(self) -> None:
            self.s = "new string"

    # Retrieve the setting from the "settings" namespace
    module = Test.__module__
    module_settings = getattr(settings, module)  # Module exists
    assert module_settings.Test.s.value == "t"

    # 2. Try a class instance
    test = Test()

    assert test.s == "new string"
    assert module_settings.Test.s.value == "t"


def test_setting_validate_cls_creation(settings: SettingsManager) -> None:
    """Test the :cls:`Setting` :meth:`validate` method for class creation"""

    with pytest.raises(ConditionFailure):

        class Test:
            s = Setting(-3, "An int", is_positive)


def test_setting_validate_instantiation(settings: SettingsManager) -> None:
    """Test the :cls:`Setting` :meth:`validate` method for class instantiation"""

    class Test:
        s = Setting(3, "An int", is_positive)

        def __init__(self) -> None:
            self.s = -3

    with pytest.raises(ConditionFailure):
        Test()


def test_setting_validate_change(settings: SettingsManager) -> None:
    """Test the :cls:`Setting` :meth:`validate` method for class and instance setting
    change"""

    class Test:
        s = Setting(3, "An int", is_positive)

    # Changing the default to an invalid value doesn't work
    with pytest.raises(ConditionFailure):
        Test.s.value = -3

    # Change to an invalid value doesn't work
    test = Test()
    with pytest.raises(ConditionFailure):
        test.s = -3


def test_settings_manager_hierarchy(settings_set1: SettingsManager) -> None:
    """Test the proper construction of the settings manager hierarchy"""
    settings = settings_set1

    assert isinstance(settings, SettingsManager)
    assert isinstance(settings.conftest, SettingsManager)
    assert isinstance(settings.conftest.TestClass, SettingsManager)
    assert isinstance(settings.conftest.TestClass.attribute, Setting)
    assert isinstance(settings.conftest.TestClass.attribute2, Setting)
    assert isinstance(settings.database_ip, Setting)


def test_settings_manager_hiearchy_parent(settings_set1: SettingsManager) -> None:
    """Test the proper setting of the SettingsHierarchy parent property"""
    settings = settings_set1

    assert settings.parent is None
    assert settings.conftest.parent == settings
    assert settings.conftest.TestClass.parent == settings.conftest  # type: ignore
    assert settings.conftest.TestClass.attribute.parent == settings.conftest.TestClass  # type: ignore
    assert settings.conftest.TestClass.attribute2.parent == settings.conftest.TestClass  # type: ignore
    assert settings.database_ip.parent == settings


def test_settings_manager_hierarchy_name(settings_set1: SettingsManager) -> None:
    """Test the SettingsHierarchy name property"""
    settings = settings_set1

    assert settings.conftest.TestClass.name == "TestClass"  # type: ignore
    assert settings.conftest.TestClass.attribute.name == "attribute"  # type: ignore
    assert settings.conftest.TestClass.attribute2.name == "attribute2"  # type: ignore
    assert settings.database_ip.name == "database_ip"

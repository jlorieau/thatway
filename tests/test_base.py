"""Tests for Setting and SettingsManager classes"""

import pytest

from thatway import ConditionFailure, Setting, SettingException, SettingsManager
from thatway.conditions import is_positive


def test_setting_get(settings: SettingsManager) -> None:
    """Test the accession order for a setting"""

    # Create a class and an instance
    class TestClass:

        setting = Setting(1, "default setting")

        def __init__(self) -> None:
            self.setting = 3

    test = TestClass()

    # Change the global settings value
    module_settings = getattr(settings, TestClass.__module__)
    module_settings.TestClass.setting.value = 2  # type: ignore

    # 1. Accessing from the class gives the descriptor
    assert isinstance(TestClass.setting, Setting)

    # 2. The instance value should be returned
    assert test.setting == 3

    # 3. If the instance value is not available, return the settings manager's value
    del test.setting
    assert test.setting == 2

    # 4. If the global setting is not available, return the descriptor's default
    del module_settings.TestClass.setting
    assert test.setting == 1


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


def test_settings_manager_new(settings: SettingsManager) -> None:
    """Test the SettingsManager __new__ method and singleton behavior"""
    assert id(SettingsManager()) == id(settings)  # same object
    assert id(SettingsManager(base=False)) != id(settings)  # different object


def test_settings_manager_iter(settings_set1: SettingsManager) -> None:
    """Test the SettingsManager __iter__ and __len__ methods"""
    settings = settings_set1

    assert len(settings) == 2
    assert settings.conftest in settings  # type: ignore
    assert settings.database_ip in settings  # type: ignore

    conftest = settings.conftest

    assert len(conftest) == 1  # type: ignore
    assert conftest.TestClass in conftest  # type: ignore

    TestClass = conftest.TestClass  # type: ignore

    assert len(TestClass) == 2  # type: ignore
    assert TestClass.attribute in TestClass
    assert TestClass.attribute2 in TestClass


def test_settings_manager_set(settings: SettingsManager) -> None:
    """Test the SettingsManager __set__ method"""

    # Setting a new setting is allowed
    class TestClass:
        attribute = Setting(5, "a setting")

    module_name = TestClass.__module__
    module_settings = getattr(settings, module_name)
    assert module_settings.TestClass.attribute.value == 5

    # 1. Setting a new setting on a class is not allowed
    with pytest.raises(SettingException):

        class TestClass:  # type: ignore
            attribute = Setting("new value", "a new value")

    # 2. Setting a new setting on the setting manager is not allowed
    with pytest.raises(SettingException):
        module_settings.TestClass.attribute = Setting("new value", "a new valuel")

    # 3. Changing a sub-manager to a setting is not allowed
    with pytest.raises(SettingException):
        module_settings.TestClass = Setting("new value", "a new valuel")


def test_settings_manager_get(settings: SettingsManager) -> None:
    """Test the SettingsManager __getattribute__ method."""
    # Retrieve any attribute returns an empty setting
    sub_manager = settings.sub
    assert isinstance(sub_manager, SettingsManager)
    assert len(sub_manager) == 0

    # This sub-manager can be replaced as long as it's empty
    settings.sub = Setting(5, "A setting")

    # Replacing a sub-manager with a setting is not allowed
    sub_manager2 = settings.sub2
    sub_manager2.setting = Setting(5, "A setting")  # type: ignore

    with pytest.raises(SettingException):
        settings.sub2 = Setting("new", "a new setting")


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

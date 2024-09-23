"""Tests for Setting"""

import pytest

from thatway.conditions import ConditionFailure, is_positive
from thatway.manager import SettingsNamespace
from thatway.setting import Setting


def test_setting_delete(settings: SettingsNamespace) -> None:
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


def test_setting_insert(settings: SettingsNamespace) -> None:
    """Test the :cls:`Setting` :meth:`_insert` method."""

    # 1. Try a setting owned by a class
    class Test:
        s = Setting("t", desc="A string")

        def __init__(self) -> None:
            self.s = "new string"

    module = Test.__module__
    module_settings = getattr(settings, module)  # Module exists
    assert module_settings.Test.s.default == "t"
    assert not hasattr(module_settings.Test.s, "value")

    # 2. Try a class instance
    test = Test()

    assert test.s == "new string"
    assert module_settings.Test.s.default == "t"
    assert not hasattr(module_settings.Test.s, "value")


def test_setting_validate_cls_creation(settings: SettingsNamespace) -> None:
    """Test the :cls:`Setting` :meth:`validate` method for class creation"""

    with pytest.raises(ConditionFailure):

        class Test:
            s = Setting(-3, "An int", is_positive)


def test_setting_validate_instantiation(settings: SettingsNamespace) -> None:
    """Test the :cls:`Setting` :meth:`validate` method for class instantiation"""

    class Test:
        s = Setting(3, "An int", is_positive)

        def __init__(self) -> None:
            self.s = -3

    with pytest.raises(ConditionFailure):
        Test()


def test_setting_validate_change(settings: SettingsNamespace) -> None:
    """Test the :cls:`Setting` :meth:`validate` method for class and instance setting
    change"""

    class Test:
        s = Setting(3, "An int", is_positive)

    # Changing the default to an invalid value doesn't work
    with pytest.raises(ConditionFailure):
        Test.s.default = -3

    # Change to an invalid value doesn't work
    test = Test()
    with pytest.raises(ConditionFailure):
        test.s = -3

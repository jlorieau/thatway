from thatway import Config, Parameter, ConfigException

import pytest


def test_cls_attribute():
    """Test the setting of a class attribute"""

    class Obj:
        a = Parameter(value=3)

    obj = Obj()

    assert Obj.a == 3
    assert obj.a == 3

    # Check the config object
    config = Config()
    assert isinstance(config.__dict__["Obj"].__dict__["a"], Parameter)
    assert config.Obj.a == 3


def test_cls_attribute_mutation():
    """Test the mutating of a class attribute"""

    class Obj:
        a = Parameter(value=3)

    obj = Obj()

    with pytest.raises(ConfigException):
        obj.a = 5  # Can't edit directly

    config = Config
    with pytest.raises(ConfigException):
        config.Obj.a = 5  # Can't edit the config value directly


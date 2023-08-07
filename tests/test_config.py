from thatway import Config, Parameter, ConfigException

import pytest


@pytest.fixture
def config():
    """Retrieve and reset the config object"""
    Config._instance = None
    config = Config()
    return config


def test_cls_attribute(config):
    """Test the setting of a class attribute"""

    class Obj:
        a = Parameter(value=3)

    obj = Obj()

    assert Obj.a == 3
    assert obj.a == 3

    # Check the config object
    assert isinstance(config.__dict__["Obj"].__dict__["a"], Parameter)
    assert config.Obj.a == 3


def test_cls_attribute_mutation(config):
    """Test the mutating of a class attribute"""

    class Obj:
        a = Parameter(value=3)

    obj = Obj()

    # Can't edit directly
    with pytest.raises(ConfigException):
        obj.a = 5

    # NB: This statement check's the attribute's value, and it registers the attribute
    # in the config--needed for the next test
    assert obj.a == 3

    # Can't edit the config value directly
    with pytest.raises(ConfigException):
        config.Obj.a = 5

    assert config.Obj.a == 3


def test_direct_access(config):
    """Test direct access to config"""
    # Try at the root level
    config.a = "direct access"
    assert config.a == "direct access"
    assert "a" in config.__dict__["a"]

    # Try at a nested level
    config.nested.b = "sub level"
    assert config.nested.b == "sub level"
    assert "b" in config.__dict__["nested"].__dict__


def test_direct_access_mutation(config):
    """Test the mutating of a directly accessed config value"""
    config.a = "direct access"
    config.nested.b = "sub level"

    # Modifying raises an exception
    with pytest.raises(ConfigException):
        config.a = "new value"

    assert config.a == "direct access"

    with pytest.raises(ConfigException):
        config.nested.b = "new value"

    assert config.nested.b == "sub level"

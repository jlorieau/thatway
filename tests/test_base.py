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
    config.a = Parameter("direct access")
    assert config.a == "direct access"
    assert "a" in config.__dict__

    # Try at a nested level
    config.nested.b = Parameter("sub level")
    assert config.nested.b == "sub level"
    assert "b" in config.__dict__["nested"].__dict__

    # Directly setting values without a Parameter is not allowed
    with pytest.raises(ConfigException):
        config.c = 3


def test_direct_access_mutation(config):
    """Test the mutating of a directly accessed config value"""
    config.a = Parameter("direct access")
    config.nested.b = Parameter("sub level")

    # Modifying raises an exception
    with pytest.raises(ConfigException):
        config.a = Parameter("new value")

    assert config.a == "direct access"

    with pytest.raises(ConfigException):
        config.nested.b = Parameter("new value")

    assert config.nested.b == "sub level"


def test_config_update(config):
    """Test the config.update method"""
    config.a = Parameter(1)
    config.nested.b = Parameter(2)

    # Updating allows overwrites
    config.update({'a': 3, 'nested': {'b': 4}})

    assert config.a == 3
    assert config.nested.b == 4




def test_config_update_type_matching(config):
    """Test the config.update method with mismatched types"""
    config.a = Parameter(1)
    config.nested.b = Parameter(2)

    with pytest.raises(ConfigException):
        config.update({'a': 'new value', 'nested': {'b': "new nested b"}})

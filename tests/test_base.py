from thatway import Config, Setting, ConfigException

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
        a = Setting(value=3)

    obj = Obj()

    assert Obj.a == 3
    assert obj.a == 3

    assert config.Obj.a == 3

    # Check the setting object
    param_obj = config.__dict__["Obj"].__dict__["a"]
    assert isinstance(param_obj, Setting)


def test_cls_attribute_mutation(config):
    """Test the mutating of a class attribute"""

    class Obj:
        a = Setting(value=3)

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
    config.a = Setting("direct access")
    assert config.a == "direct access"
    assert "a" in config.__dict__

    # Try at a nested level
    config.nested.b = Setting("sub level")
    assert config.nested.b == "sub level"
    assert "b" in config.__dict__["nested"].__dict__

    # Directly setting values without a Setting is not allowed
    with pytest.raises(ConfigException):
        config.c = 3

    # Check the setting object
    param_obj = config.__dict__["a"]
    assert isinstance(param_obj, Setting)


def test_direct_access_mutation(config):
    """Test the mutating of a directly accessed config value"""
    config.a = Setting("direct access")
    config.nested.b = Setting("sub level")

    # Modifying raises an exception
    with pytest.raises(ConfigException):
        config.a = Setting("new value")

    assert config.a == "direct access"

    with pytest.raises(ConfigException):
        config.nested.b = Setting("new value")

    assert config.nested.b == "sub level"


def test_config_update(config):
    """Test the config.update method"""
    config.a = Setting(1)
    config.nested.b = Setting(2)

    # Updating allows overwrites
    config.update({"a": 3, "nested": {"b": 4}})

    assert config.a == 3
    assert config.nested.b == 4


def test_config_update_type_matching(config):
    """Test the config.update method with mismatched types"""
    config.a = Setting(1)
    config.nested.b = Setting(2, allowed_types=(int, str))

    # Can't change the value of 'a'
    with pytest.raises(ValueError):
        config.update({"a": "new value"})

    # Can change the value of 'nested.b' to a int or string
    config.update({"nested": {"b": "my new string"}})
    assert config.nested.b == "my new string"


def test_setting_overwrite(config):
    """Test that settings cannot be overwritten in the config"""

    # 1. direct access
    config.a = Setting(1)

    with pytest.raises(ConfigException):
        config.a = Setting(2)

    assert config.a == 1

    # 2. instance attribute
    class Obj:
        b = Setting(3)

    obj = Obj()

    with pytest.raises(ConfigException):
        obj.b = 4

    assert obj.b == 3

    # 3. class attribute. These can be overwritten because the descriptor can
    # be replaced.
    # see: https://docs.python.org/3/reference/datamodel.html#object.__set__
    Obj.b = 4
    assert Obj.b == 4
    assert isinstance(Obj.__dict__["b"], int)  # not a setting anymore

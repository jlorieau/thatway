from thatway import Setting, ConfigException

import pytest


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


def test_overwrite(config):
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


def test_config_update_missing(config):
    """Test the config.update method for a missing setting, which shouldn't be
    inserted"""
    with pytest.raises(KeyError):
        config.update({"new_value": "2"})


def test_config_dump(config):
    """Test the config.dump method for converting into a dict tree"""

    # Set up the config
    class Obj:
        a = Setting(1)

    config.b = Setting("name")
    config.nested.c = Setting(True)

    # Dump and test the contents
    d = config.dump()

    assert isinstance(d, dict)
    assert d.keys() == {"Obj", "b", "nested"}

    assert isinstance(d["Obj"], dict)
    assert d["Obj"].keys() == {"a"}
    assert d["Obj"]["a"] == 1

    assert d["b"] == "name"

    assert isinstance(d["nested"], dict)
    assert d["nested"].keys() == {"c"}
    assert isinstance(d["nested"]["c"], bool)
    assert d["nested"]["c"]


@pytest.mark.parametrize("mode", ("string", "file"))
def test_config_loads_yaml(config, mode, tmp_path):
    """Test the config.loads_yaml and config.load_yaml methods for loading yaml
    strings"""
    # Set up a config
    config.a = Setting(1)

    # Load and replace the value
    config.loads_yaml("a: 2")

    # Test loading of new value
    yaml_string = "a: 2"
    if mode == "string":
        config.loads_yaml(yaml_string)
    elif mode == "file":
        tmp_file = tmp_path / "settings.yaml"
        tmp_file.write_text(yaml_string)
        config.load_yaml(tmp_file)

    assert config.a == 2


def test_config_dumps_yaml(config):
    """Test the config.dumps_yaml method for generating yaml strings"""

    # Setup a config
    class Obj:
        a = Setting(1)

    config.b = Setting("name", desc="The 'b' setting")
    config.nested.c = Setting(True)

    # Retrieve and compare the yaml string
    yaml = config.dumps_yaml()
    assert yaml == "Obj:\n  a: 1\nb: name  # The 'b' setting\nnested:\n  c: true\n"

    # The string can be loaded back without exception
    config.loads_yaml(yaml)


@pytest.mark.parametrize("mode", ("string", "file"))
def test_config_loads_toml(config, mode, tmp_path):
    """Test the config.loads_toml and config.load_toml methods for loading
    toml strings"""

    # Setup a config
    class Obj:
        a = Setting(1)

    # Test loading of new value
    toml_string = "[Obj]\na = 2"
    if mode == "string":
        config.loads_toml(toml_string)
    elif mode == "file":
        tmp_file = tmp_path / "settings.toml"
        tmp_file.write_text(toml_string)
        config.load_toml(tmp_file)

    assert Obj.a == 2

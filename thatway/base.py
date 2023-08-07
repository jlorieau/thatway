"""An instance-wide configuration"""
import typing as t
from threading import Lock
import re
import logging


__all__ = ("ConfigException", "Config", "Parameter", "config")

logger = logging.getLogger(__name__)


#: The regex to validate parameter key
key_regex = re.compile(r"^[_A-Za-z][_A-Za-z0-9.]*$")


def validate(key):
    """Ensure that the given key/name is valid"""
    if not key_regex.match(key):
        raise ConfigException(
            f"The Parameter name '{key}' is not valid. "
            f"Must match the pattern: '{key_regex.pattern}'"
        )


class ConfigException(Exception):
    """An exception raised in validating or modifying the config"""


class ConfigMeta(type):
    """A metaclass to set up the creation of Config object singleton"""

    def __call__(cls, root: bool = True, **kwargs):
        # noinspection PyArgumentList
        obj = cls.__new__(cls, root=root)
        obj.__init__(**kwargs)
        return obj


class Config(metaclass=ConfigMeta):
    """A thread-safe Config manager to get and set configuration parameters.

    Notes
    -----
    The base class is deliberately modified dynamically with descriptors. This
    is because the Config was designed to be configured on the fly.
    """

    #: Different names for subsections in a dict which could contain config settings
    section_aliases = ("config", "Config")

    #: The root singleton instance
    _instance: t.Optional["Config"] = None

    #: The thread lock
    _thread_lock: Lock = Lock()

    def __new__(cls, root: bool = True):
        # Create the singleton instance if it hasn't been created
        if cls._instance is None:
            # Lock the thread
            with cls._thread_lock:
                # Prevent another thread from creating the instance in the
                # interim
                if cls._instance is None:
                    cls._instance = super().__new__(cls)

        if not root:
            # If this is not the root Config--i.e. a sub config--return a
            # new Config object instead of the root singleton
            obj = super().__new__(cls)
            return obj
        else:
            # Otherwise return the singleton
            return cls._instance

    def __init__(self, **kwargs):
        # Set the specified parameters
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getattribute__(self, key):
        """Get attributes Config with support for attribute nesting"""
        try:
            # The returned value should be a parameter or a Config object
            value = super().__getattribute__(key)
            return value.value if isinstance(value, Parameter) else value
            # return super().__getattribute__(key)
        except AttributeError:
            # Create a dict by default for a missing attribute
            # This allows nested attribute access
            self.__dict__[key] = Config(root=False)
            return super().__getattribute__(key)

    def __setattr__(self, key, value):
        if key in ('_instance',):
            # Special keys that can have their values replaced
            super().__setattr__(key, value)
        elif key not in self.__dict__ and isinstance(value, Parameter):
            # New entries are allowed as long as they're parameters
            self.__dict__[key] = value
        elif not isinstance(value, Parameter):
            raise ConfigException(f"Only Parameters can be inserted in the Config")
        elif key in self.__dict__:
            # If it already exists, don't allow a rewrite
            raise ConfigException(f"Entry '{key}' already in the Config--use a "
                                  f"load method to change its value.")
        else:
            raise ConfigException(f"Unable to chance Config")


# Config singleton instance
# config = Config()

# dummy placeholder object
missing = object()


class Parameter:
    """A descriptor for a Config parameter.
    """

    __slots__ = ("name", "value", "_config")

    #: The name of the parameter in the Config
    name: str

    #: The value for the parameter
    value: t.Any

    #: The delimiter used for splitting keys
    delim: str = "."

    def __init__(self, value):
        # Set the default, if specified
        setattr(self, 'value', value)

    def __set_name__(self, owner, name):
        cls_name = owner.__name__
        name = f"{cls_name}.{name}"
        validate(name)
        self.name = name

    # def __repr__(self):
    #     value = getattr(self._config, self.key)
    #     return f"Param({self.key}={value})"

    def __get__(self, instance, owner):
        """Get the parameter value

        Notes
        -----
        - This method also inserts the parameter in the config. This means that the
          parameter is only registered on the config when it is accessed/used. Unused
          parameters are not registered in the config
        """
        # If this parameter doesn't exist in the config, insert it
        keys = self.name.split(self.delim)
        sub_config = Config()
        for key in keys[:-1]:
            sub_config = getattr(sub_config, key)
        if keys[-1] not in sub_config.__dict__:
            sub_config.__dict__[keys[-1]] = self

        return self.value

    def __set__(self, instance, value):
        raise ConfigException(f"Can't set Parameter attribute with "
                              f"value '{value}'--use the Config.load methods.")

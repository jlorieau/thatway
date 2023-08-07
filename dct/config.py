"""An instance-wide configuration"""
import typing as t
from threading import Lock
import re
import logging


__all__ = ("ConfigException", "Config", "Parameter")

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
    """A metaclass to set up the creation of Config objects and singleton"""

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

    #: The root singleton instance
    _instance: t.Optional["Config"] = None

    #: The thread lock
    _lock: Lock = Lock()

    #: Different names for subsections in a dict which could contain config settings
    section_aliases = ("config", "Config")

    def __new__(cls, root: bool = True):
        # Create the singleton instance if it hasn't been created
        if cls._instance is None:
            # Lock the thread
            with cls._lock:
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

        # # Place the parameter in the config
        # keys = self.name.split(self.delim)
        # nested_config = self._config
        #
        # for key in keys[:-1]:
        #     nested_config = getattr(nested_config, key)
        #
        # # Add this parameter to the config
        # nested_config.__dict__[keys[-1]] = self

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

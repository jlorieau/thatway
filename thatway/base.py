"""An instance-wide configuration"""
import typing as t
from threading import Lock
from collections.abc import Mapping
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
                                  f"Config.update or load method to change its value.")
        else:
            raise ConfigException(f"Unable to chance Config")

    def __contains__(self, item):
        return item in self.__dict__

    def update(self, updates: Mapping) -> None:
        """Recursively update config with values from a dict.

        Parameters
        ----------
        updates
            The dict with values to recursively update

        Raises
        ------
        ConfigException
            Raised when the updates include a change that would replace a
            sub-config (subsection) that includes parameters with a single
            parameter.
        KeyError
            If a key as specified that doesn't exist in this config
        ValueError
            If the update dict contains a  value that has a different
            type then the corresponding parameter's value
        """
        for k, v in updates.items():
            try:
                current_value = self.__dict__[k]
            except KeyError:
                raise KeyError(f"Tried assigning parameter with name '{k}' which does "
                               f"not exist in the Config")

            if isinstance(v, Mapping):
                # Use the corresponding update function. ex: dict.update
                current_value.update(v)
            elif isinstance(v, Config):
                # If it's a sub-config object, use its corresponding update
                # (this method)
                current_value.update(v.__dict__)
            elif isinstance(current_value, Config) and len(current_value.__dict__) > 0:
                # In this case, the update value 'v' is a simple value but the
                # current_value is a sub-config with items in it. Overwriting
                # This sub-config is not allowed
                raise ConfigException(
                    f"Cannot replace config section '{k}' with a parameter '{v}'"
                )
            elif isinstance(current_value, Parameter):
                # Get the parameter value's type and allowed types
                value_type = type(current_value.value)
                allowed_types = current_value.allowed_types
                types = [] if allowed_types is None else list(allowed_types)
                types += [value_type]

                # Replace the parameter's value, trying to coerce the type
                found_type = False
                for allowed_type in types:
                    try:
                        current_value.value = allowed_type(v)
                        found_type = True
                    except ValueError:
                        continue

                if not found_type:
                    raise ValueError(f"Could not convert '{v}' into any of the "
                                     f"following types: {types}")

            else:
                raise ConfigException("Parameter not in Config")


# dummy placeholder object
missing = object()


class Parameter:
    """A descriptor for a Config parameter.
    """

    __slots__ = ("name", "value", "desc", "allowed_types")

    #: The name of the parameter in the Config
    name: str

    #: The value for the parameter
    value: t.Any

    #: (optional) The description for this parameter
    desc: str

    #: (optional) A tuple of allowed types for the values
    allowed_types: t.Tuple[t.Any]

    #: The delimiter used for splitting keys
    delim: str = "."

    def __init__(self, value: t.Any, desc: str = "",
                 allowed_types: t.Optional[t.Tuple[t.Any, ...]] = None):
        self.value = value
        self.desc = desc
        self.allowed_types = allowed_types

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
                              f"value '{value}'--use the Config.update or load "
                              f"methods.")

"""An instance-wide configuration"""
import typing as t
from threading import Lock
from collections.abc import Mapping
import logging

import yaml
import tomllib

__all__ = ("ConfigException", "Config", "Setting")

logger = logging.getLogger(__name__)


class ConfigException(Exception):
    """An exception raised in validating or modifying the config"""


# dummy placeholder object
missing = object()


class Setting:
    """A descriptor for a Config setting."""

    __slots__ = ("value", "desc", "allowed_types")

    #: The value for the setting
    value: t.Any

    #: (optional) The description for this setting
    desc: str

    #: (optional) A tuple of allowed types for the values
    allowed_types: t.Tuple[t.Any]

    #: The delimiter used for splitting keys
    delim: str = "."

    def __init__(
        self,
        value: t.Any,
        desc: str = "",
        allowed_types: t.Optional[t.Tuple[t.Any, ...]] = None,
    ):
        self.value = value
        self.desc = desc
        self.allowed_types = allowed_types

    def __set_name__(self, owner, name):
        cls_name = owner.__name__
        location = f"{cls_name}.{name}"
        self._config_insert(location)

    def __repr__(self):
        return f"Param({self.value})"

    def __get__(self, instance, owner):
        """Get the setting value"""
        return self.value

    def __set__(self, instance, value):
        raise ConfigException(
            f"Can't set Setting attribute with "
            f"value '{value}'--use the Config.update or load "
            f"methods."
        )

    def _config_insert(self, location: str):
        """Insert this setting in the config at the given location.

        Settings
        ----------
        location
            The location of the setting. e.g. 'Obj.a'

        Raises
        ------
        ConfigException
            Raised if trying to insert this setting by something else already
            exists at that location in the config.
        """
        keys = location.split(self.delim)

        # Got through each key to get sub configs deeper in the nested tree
        sub_config = Config()
        for key in keys[:-1]:
            sub_config = getattr(sub_config, key)

        # The last key is where this setting should be inserted.
        last_key = keys[-1]
        if last_key not in sub_config.__dict__:
            # If it's not inserted already, place it in there.
            sub_config.__dict__[last_key] = self
        elif id(sub_config.__dict__[last_key]) != id(self):
            # Oops, another object's in that place! There's a setting collision
            other_value = sub_config.__dict__[last_key]
            raise ConfigException(
                f"Cannot insert '{self}' at '{location}'. The '{other_value}' "
                f"already exists there."
            )


class ConfigMeta(type):
    """A metaclass to set up the creation of Config object singleton"""

    def __call__(cls, root: bool = True, **kwargs):
        # noinspection PyArgumentList
        obj = cls.__new__(cls, root=root)
        obj.__init__(**kwargs)
        return obj


class Config(metaclass=ConfigMeta):
    """A thread-safe Config manager to get and set configuration settings.

    Notes
    -----
    The base class is deliberately modified dynamically with descriptors. This
    is because the Config was designed to be configured on the fly.
    """

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
        # Set the specified settings
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getattribute__(self, key):
        """Get attributes Config with support for attribute nesting"""
        try:
            # The returned value should be a setting or a Config object
            value = super().__getattribute__(key)
            return value.value if isinstance(value, Setting) else value
            # return super().__getattribute__(key)
        except AttributeError:
            # Create a dict by default for a missing attribute
            # This allows nested attribute access
            self.__dict__[key] = Config(root=False)
            return super().__getattribute__(key)

    def __setattr__(self, key, value):
        if key in ("_instance",):
            # Special keys that can have their values replaced
            super().__setattr__(key, value)
        elif key not in self.__dict__ and isinstance(value, Setting):
            # New entries are allowed as long as they are settings
            self.__dict__[key] = value
        elif not isinstance(value, Setting):
            raise ConfigException(f"Only Settings can be inserted in the Config")
        elif key in self.__dict__:
            # If it already exists, don't allow a rewrite
            raise ConfigException(
                f"Entry '{key}' already in the Config--use a "
                f"Config.update or load method to change its value."
            )
        else:
            raise ConfigException(f"Unable to chance Config")

    def __contains__(self, item):
        return item in self.__dict__

    def update(self, updates: Mapping) -> None:
        """Recursively update config with values from a dict.

        Settings
        ----------
        updates
            The dict with values to recursively update

        Raises
        ------
        ConfigException
            Raised when the updates include a change that would replace a
            sub-config (subsection) that includes settings with a single
            setting.
        KeyError
            If a key as specified that doesn't exist in this config
        ValueError
            If the update dict contains a  value that has a different
            type then the corresponding setting's value
        """
        for k, v in updates.items():
            try:
                current_value = self.__dict__[k]
            except KeyError:
                raise KeyError(
                    f"Tried assigning setting with name '{k}' which does "
                    f"not exist in the Config"
                )

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
                    f"Cannot replace config section '{k}' with a setting '{v}'"
                )
            elif isinstance(current_value, Setting):
                # Get the setting value's type and allowed types
                value_type = type(current_value.value)
                allowed_types = current_value.allowed_types
                types = [] if allowed_types is None else list(allowed_types)
                types += [value_type]

                # Replace the setting's value, trying to coerce the type
                found_type = False
                for allowed_type in types:
                    try:
                        current_value.value = allowed_type(v)
                        found_type = True
                    except ValueError:
                        continue

                if not found_type:
                    raise ValueError(
                        f"Could not convert '{v}' into any of the "
                        f"following types: {types}"
                    )

            else:
                raise ConfigException("Setting not in Config")

    def dump(self) -> dict:
        """Convert the config into a tree dict structure"""
        d = dict()
        for k, v in self.__dict__.items():
            if isinstance(v, Setting):
                d[k] = v.value
            elif isinstance(v, Config):
                d[k] = v.dump()  # This method
            else:
                raise ConfigException(f"Unknown config type for entry '{v}'")
        return d

    # yaml methods

    @staticmethod
    def _to_yaml(value) -> str:
        """Convert a value to a string formatted for yaml"""
        if isinstance(value, bool):
            return str(value).lower()
        else:
            return str(value)

    def loads_yaml(self, string: str) -> None:
        """Load settings from a yaml string into the config"""
        d = yaml.load(string, Loader=yaml.Loader)
        self.update(d)

    def load_yaml(self, filepath: str) -> None:
        """Load settings from a yaml file into the config"""
        with open(filepath, "r") as f:
            d = yaml.load(f, Loader=yaml.Loader)
        self.update(d)

    def dumps_yaml(self, level: int = 0, indent: int = 2) -> str:
        """Dump settings from the config into a yaml string

        Parameters
        ----------
        level
            The current level of the config for nested configs
        indent
            The number of spaces to indent each level

        Returns
        -------
        yaml
            A yaml-formatted string
        """
        string = ""
        for k, v in self.__dict__.items():
            spacer = " " * indent * level
            if isinstance(v, Setting):
                # Format the setting value and, optionally, its description
                comment = f"  # {v.desc}" if v.desc else ""
                value = self._to_yaml(v.value)
                string += f"{spacer}{k}: {value}{comment}\n"

            elif isinstance(v, Config):
                # Print the config as a new section then use the config's corresponding
                # dump method to get its values
                string += f"{spacer}{k}:\n"
                string += v.dumps_yaml(level=level + 1, indent=indent)  # this method
            else:
                # Only Config and Setting objects should be in here
                raise ConfigException(f"Unknown config type for entry '{v}'")
        return string

    # toml methods

    def loads_toml(self, string: str) -> None:
        """Load settings from a toml string into the config"""
        d = tomllib.loads(string)
        self.update(d)

    def load_toml(self, filepath: str) -> None:
        """Load settings from a toml file into the config"""
        with open(filepath, "rb") as f:
            d = tomllib.load(f)
        self.update(d)

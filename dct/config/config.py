"""An instance-wide configuration"""
import typing as t
from threading import Lock
from collections.abc import Mapping
import inspect
import re
import logging


__all__ = ("ConfigException", "Config", "Parameter")

logger = logging.getLogger(__name__)


#: The regex to validate parameter key
key_regex = re.compile(r"^[_A-Za-z][_A-Za-z0-9]*$")


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
        validate(key)
        try:
            # The returned value should be a parameter or a Config object
            value = super().__getattribute__(key)
            return value.value if isinstance(value, Parameter) else value
            # return super().__getattribute__(key)
        except AttributeError:
            print(f"Config.__getattribute(key): {key}  (missing)")
            # Create a dict by default for a missing attribute
            # This allows nested attribute access
            self.__dict__[key] = Config(root=False)
            return super().__getattribute__(key)

    def __setattr__(self, key, value):
        """Set attributes in the Config"""
        if not isinstance(value, Parameter):
            raise ConfigException("Cannot set config values directly--use Parameter")
        else:
            super().__setattr__(key, value)

    def __eq__(self, other):
        """Test whether this Config is equal to another"""
        if not type(self) == type(other):
            return False
        return self.__dict__ == other.__dict__

    def __len__(self):
        """The number of items in this Config"""
        return len(self.__dict__)

    def __repr__(self):
        return f"Config({', '.join(self.__dict__.keys())})"

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

        Notes
        -----
        - This function operates recursively to update sub-config (subsection)
          objects
        - This function does not allow a sub-config (subsection) to be replaced
          or truncated by a parameter. This will raise a ConfigException.
        - This function is not atomic. If a ConfigException is raised partway
          through the update, this config will only be partially updated.
        """
        for k, v in updates.items():
            current_value = getattr(self, k)  # get the current value or sub_config

            if isinstance(v, Mapping):
                # Use the corresponding update function. ex: dict
                current_value.update(v)
            elif isinstance(v, Config):
                current_value.update(v.__dict__)
            elif isinstance(current_value, Config) and len(current_value.__dict__) > 0:
                # In this case, the update value 'v' is a simple parameter but the
                # current_value is a sub-config with items in it. This is not allowed.
                raise ConfigException(
                    f"Cannot replace config section '{k}' with a parameter '{v}'"
                )
            else:
                logger.debug(f"Config.update(): set {k}={v}")
                setattr(self, k, v)

    @classmethod
    def load(cls, d: dict, root=True) -> "Config":
        """Load config with values from a dict.

        Parameters
        ----------
        d
            The dict with config values to load
        root
            Whether the root Config singleton is returned or a new sub config
            is returned.

        Returns
        -------
        config
            The root config instance with parameters loaded
        """
        config = cls(root=root)

        for k, v in d.items():
            # Only key strings are allowed for the Config
            assert isinstance(k, str), (
                f"Config keys must be strings. " f"Received: '{k}'"
            )

            if isinstance(v, dict):
                # Create a sub Config and load the sub dict
                sub_config = Config.load(v, root=False)
                setattr(config, k, sub_config)
            else:
                # Otherwise just store the value
                logger.debug(f"Config.load(): set {k}={v}")
                setattr(config, k, v)

        return config


# dummy placeholder object
missing = object()


class Parameter:
    """A descriptor for a Config parameter.

    Notes
    -----
    This is a descriptor. Its value can be accessed or modified from an
    instance. However, its value can only be access from the class itself. This
    is because the descriptor will be replaced if its corresponding class
    attribute is modified with a new value. Stated another way, the __set__
    method is not called from a class--only instances of a class.
    """

    __slots__ = ("key", "value", "_config")

    #: The key/name of the parameter in the Config
    key: str

    #: The value for the parameter
    value: t.Any

    #: The delimiter used for splitting keys
    delim: str = "."

    #: A reference to the Config() singleton
    _config: Config

    def __init__(self, key, default=missing):
        validate(key)
        self.key = key

        # Get the config object scoped for the calling package name
        config = Config()
        self._config = getattr(config, self._caller_package_name)

        # Set the default, if specified
        setattr(self, 'value', default)

        # Place the parameter in the config
        keys = self.key.split(self.delim)
        nested_config = self._config

        for key in keys[:-1]:
            nested_config = getattr(nested_config, key)
        nested_config.__dict__[keys[-1]] = self

    # def __repr__(self):
    #     value = getattr(self._config, self.key)
    #     return f"Param({self.key}={value})"

    def __get__(self, instance, objtype=None):
        return self.value

    def __set__(self, instance, value):
        # Convert strings with '.' into nested keys
        keys = self.key.split(self.delim)
        conf_obj = self._config
        for key in keys[:-1]:
            conf_obj = getattr(conf_obj, key)

        # Set the value directly in the Config's __dict__ since __setattr_ is locked
        self.value = value
        conf_obj.__dict__[keys[-1]] = self

    @property
    def _caller_module_name(self) -> str:
        """Get the name of the module calling this Parameter.
        """
        last_frame = inspect.stack()[-1]
        module = inspect.getmodule(last_frame[0])
        return module.__name__

    @property
    def _caller_package_name(self) -> str:
        """Get the name of the package calling this Parameter"""
        return self._caller_module_name.split('.')[0]

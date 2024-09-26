"""Classes for storing settings"""

from typing import Callable, Generic, TypeVar, cast, overload

from .conditions import SupportsRichComparison
from .exceptions import ConditionFailure, SettingException
from .manager.manager import SettingsManager, settings

__all__ = ("Setting",)


Instance = TypeVar("Instance")
Value = TypeVar("Value")


class Setting(Generic[Value]):

    #: The attribute name of this descriptor in a class
    name: str

    #: The setting description
    desc: str

    #: A listing of conditions (functions) for allowed values or a listing of allowed
    #: values
    conditions: tuple[Callable[[Value | SupportsRichComparison], bool], ...]

    #: Raise ConditionFailure exceptions when a condition isn't met
    raise_condition_exceptions: bool = True

    #: The default value for the setting
    _default: Value

    def __init__(
        self,
        default: Value,
        desc: str,
        *conditions: Callable[[Value | SupportsRichComparison], bool],
    ) -> None:
        self.desc = desc
        self.conditions = conditions
        self.default = cast(Value, default)

    def __repr__(self) -> str:
        return f"Setting({self.name}={self.default})"

    def __set_name__(self, cls: type[Instance], name: str) -> None:
        """Called during descriptor creation on class creation with the given
        attribute (name)
        """
        self.name = name

        # Insert this descriptor in the settings
        self._insert(*cls.__module__.split("."), cls.__name__, name)

    @overload
    def __get__(
        self, obj: None, objtype: None | type[Instance]
    ) -> "Setting[Value]": ...

    @overload
    def __get__(self, obj: Instance, objtype: type[Instance]) -> Value: ...

    def __get__(
        self, obj: Instance | None, objtype: type[Instance] | None = None
    ) -> "Setting[Value]" | Value:
        """Retrieve the setting or instance value.

        Parameters
        ----------
        obj
            If not None, the instance accessing the descriptor.
            If None, this function is being called by the class owning the descriptor.
        objtype
            The type of the class calling the descriptor

        Returns
        -------
        1. The Setting, when called on a class--i.e. obj is None.
        2. The value of the setting, if specified, or the default value, if called
           from an instance of the class owning the descriptor.
        """
        if obj is None:
            return self
        else:
            instance_settings = self._instance_settings(obj)
            return instance_settings.get(self.name, self.default)

    def __set__(self, obj: Instance, value: Value) -> None:
        # Validate the value
        self.validate(value)

        # Change the setting
        instance_settings = self._instance_settings(obj)
        instance_settings[self.name] = cast(Value, value)

    def __delete__(self, obj: Instance) -> None:
        instance_settings = self._instance_settings(obj)
        if self.name not in instance_settings:
            raise AttributeError(self.name)
        del instance_settings[self.name]

    @property
    def default(self) -> Value:
        return self._default

    @default.setter
    def default(self, value: Value) -> None:
        # Validate the value
        self.validate(value)
        self._default = value

    @staticmethod
    def _instance_settings(obj: Instance) -> dict:
        """Retrieve the settings for the descriptor's owner instance"""
        return obj.__dict__.setdefault("__settings", dict())

    def _insert(self, *keys: str) -> None:
        """Insert this setting at the given location.

        Settings
        ----------
        location
            The location of the setting. e.g. 'Obj.a'

        Raises
        ------
        SettingException
            Raised if trying to insert this setting by something else already
            exists at that location in the settings.
        """
        # Got through each key to access the corresponding namespace
        ns = settings
        for key in keys[:-1]:
            ns = ns.__dict__.setdefault(key, SettingsManager())

        # See if the setting already exists
        if hasattr(ns, keys[-1]):
            raise SettingException(f"Setting already exists at '{keys}'")

        # Insert the setting
        setattr(ns, keys[-1], self)

    def validate(self, value: Value) -> bool:
        """Validate the given value and return True (valid) or False (invalid)

        Parameters
        ----------
        value
            The value to validate

        Returns
        -------
        valid
            True, if all conditions passed. False (or raised exception) if not.

        Raises
        ------
        SettingException
            Raised if a function is not a function
        ConditionFailure
            Raised when a condition fails to validate
        """
        valid = True

        # Sort the callable and non-callable validators
        for c in self.conditions:
            if not callable(c):
                raise SettingException(
                    f"The following condition must be a function: {c}"
                )

            passed = c(value)

            if not passed and self.raise_condition_exceptions:
                # The condition function's docstring is used to annotate the exception
                raise ConditionFailure(c.__doc__)

            valid &= passed

        return valid

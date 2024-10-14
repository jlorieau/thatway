from __future__ import annotations

import copy
from threading import Lock
from types import SimpleNamespace
from typing import Any, Callable, ClassVar, Generic, Iterator, TypeVar, cast, overload
from weakref import ReferenceType, ref

from .conditions import SupportsRichComparison

__all__ = (
    "SettingException",
    "ConditionFailure",
    "Setting",
    "SettingsManager",
    "clear",
)

# Definitions and Base Classes

Value = TypeVar("Value")
Instance = TypeVar("Instance")


# Exceptions


class SettingException(Exception):
    """An exception raised from setting, changing or retrieving a setting"""


class ConditionFailure(SettingException):
    """An exception raised when a condition validation fails"""


# Class definitions


class HierarchyMixin:

    #: A weak reference to the parent settings manager that owns this object
    _parent: ReferenceType[SettingsManager]

    @property
    def parent(self) -> SettingsManager | None:
        weakref = self.__dict__.get("_parent", None)
        return weakref() if weakref is not None else None

    @parent.setter
    def parent(self, value: SettingsManager) -> None:
        assert isinstance(value, SettingsManager)
        self.__dict__["_parent"] = ref(value)

    @property
    def name(self) -> str:
        """The given name of this object from the parent"""
        parent = self.parent
        if parent is None:
            return ""

        # Find this object in the parent's dict
        for name, obj in parent.__dict__.items():
            if id(obj) == id(self):
                return name

        # Oops, name not found!
        raise AttributeError(f"Name for {self} not found.")

    @property
    def full_name(self) -> str:
        """The full name, including parents, grandparents, etc. These are separated by
        a '.'"""
        names: list[str] = [self.name]
        parent = self.parent

        while parent is not None:
            names.append(parent.name)

        return ".".join(names[::-1])


class Setting(Generic[Value], HierarchyMixin):
    """A validated setting"""

    #: The descriptor value for the setting. Accessed and set first.
    _value: Value

    #: The setting description
    desc: str

    #: A listing of conditions (functions) for allowed values or a listing of allowed
    #: values
    conditions: tuple[Callable[[Value | SupportsRichComparison], bool], ...]

    #: Setting attribute name for the instance of the class that owns this descriptor
    _setting_attribute: ClassVar[str] = "__instance_settings__"

    def __init__(
        self,
        value: Value,
        desc: str,
        *conditions: Callable[[Value | SupportsRichComparison], bool],
    ) -> None:
        """Construct a Setting instance.

        Parameters
        ----------
        default
            The default value to use for the setting. This may be overwritten when
            loading settings
        desc
            The string description of the setting.
        *conditions
            A listing of functions that take a setting value and checks whether it's
            valid for this setting
        """
        self.desc = desc
        self.conditions = conditions
        self.value = cast(Value, value)  # After the conditions are set to validate

    def __repr__(self) -> str:
        name = getattr(self, "name", "")
        value = getattr(self, "value", "")
        return f"Setting({name}={value})"

    def __set_name__(self, cls: type[Instance], name: str) -> None:
        """Called during descriptor creation on class creation with the given
        attribute (name)
        """
        # Construct or determine the location
        location = cls.__module__.split(".") + [cls.__name__, name]

        # Insert this descriptor in the settings
        self._insert(*location)

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
        (called from a class)
        Return the descriptor (self)

        (Called from an object/instance)
        1. The value set on the instance, if available.
        2. The setting value in the global settings manager.
        3. The class's default value of the setting.
        """
        # Call from the class
        if obj is None:
            return self

        # 1. Try getting the custom value from the instance
        instance_settings = self._instance_settings(obj)
        if self.name in instance_settings:
            return instance_settings[self.name]

        # 2. Try the global settings manager
        manager_setting = self._manager_setting()
        if manager_setting is not None:
            return manager_setting.value

        # 3. Return the default value
        return self.value

    def __set__(self, obj: Instance, value: Value) -> None:
        # Validate the value
        self.validate(value)

        # Change the setting
        instance_settings = Setting._instance_settings(obj)
        instance_settings[self.name] = cast(Value, value)

    def __delete__(self, obj: Instance) -> None:
        instance_settings = self._instance_settings(obj)
        if self.name not in instance_settings:
            raise AttributeError(self.name)
        del instance_settings[self.name]

    @property
    def value(self) -> Value:
        return self._value

    @value.setter
    def value(self, v: Value) -> None:
        self._value = v
        self.validate(v)

    @staticmethod
    def manager() -> SettingsManager:
        """Retrieve the global settings manager"""
        return SettingsManager()

    @classmethod
    def _instance_settings(cls, obj: Instance) -> dict:
        """Retrieve the settings for the descriptor's owner instance"""
        return obj.__dict__.setdefault(cls._setting_attribute, dict())

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
        manager = self.manager()
        for key in keys[:-1]:
            manager = getattr(manager, key)

        # Insert the setting
        setattr(manager, keys[-1], self)

        # Create a weakref to the newly-created settings manager setting
        manager_setting = getattr(manager, keys[-1])
        self._manager_setting = ref(manager_setting)

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

            if not passed:
                # The condition function's docstring is used to annotate the exception
                raise ConditionFailure(c.__doc__)

            valid &= passed

        return valid


class SettingsManager(HierarchyMixin, SimpleNamespace):
    """The settings namespace manager"""

    #: An internal listing of Setting and SettingsManager instances managed by this
    #: manager
    _settings: set[str]

    #: The settings manager singleton
    _instance: ClassVar[SettingsManager | None] = None

    #: The thread lock for the singleton
    _lock: ClassVar[Lock] = Lock()

    def __new__(cls, base: bool = True) -> SettingsManager:
        """Return a thread-safe SettingsManager singleton"""
        # If this is not the singleton base settings manager, create a new instance
        if not base:
            return super().__new__(cls)

        # Otherwise return the singleton
        if cls._instance is None:
            with cls._lock:
                # Another thread could have created the instance
                # before we acquired the lock. So check that the
                # instance is still nonexistent.
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __iter__(self) -> Iterator[Setting | SettingsManager]:
        """An iterator of the settings and (non-empty) managers owned by this settings
        manager."""
        return (
            i
            for i in self.__dict__.values()
            if isinstance(i, Setting) or isinstance(i, SettingsManager) and len(i) > 0
        )

    def __len__(self) -> int:
        """The number of settings and (non-empy) managers owned by this settings
        manager."""
        return len(list(self.__iter__()))

    def __setattr__(self, name: str, value: Any) -> None:
        """Set a setting in the settings manager namespace."""
        # See if this is a class attribute or instance attribute
        cls_attr = getattr(SettingsManager, name, None)
        obj_attr = getattr(self, name, None)

        # Calculate flags
        has_cls_property = isinstance(cls_attr, property)  # cls has this as a property
        has_obj_attr = obj_attr is not None  # instance has attribute
        is_setting = isinstance(obj_attr, Setting)  # attribute is setting
        is_submanager = isinstance(obj_attr, SettingsManager)  # attribute is submanager
        is_empty_submanager = (
            isinstance(obj_attr, SettingsManager) and len(obj_attr) == 0
        )

        # If it's a property, set it directly
        if has_cls_property:
            return super().__setattr__(name, value)

        # Only replace missing attributes or empty submanagers
        if not has_obj_attr or is_empty_submanager:
            cp = copy.copy(value)  # shallow copy
            cp.parent = self
            return super().__setattr__(name, cp)

        # At this stage, the attribute could not be set. Create a customized exception
        # message
        if is_setting:
            msg = f"Attribute '{name}' already exists as a Setting ({obj_attr})"
        elif is_submanager:
            msg = f"Attribute '{name}' is an existing setting sub-manager"
        else:
            msg = f"Could not set the setting '{name}'"

        raise SettingException(msg)

    def __getattribute__(self, name: str) -> Setting | SimpleNamespace:
        """Return the setting or a new sub-namespace of settings"""
        try:
            return super().__getattribute__(name)
        except AttributeError:
            # Create a new sub-manager
            manager = SettingsManager(base=False)
            manager.parent = self
            self.__dict__[name] = manager
            return super().__getattribute__(name)


#: Utility functions for settings


def clear(manager: SettingsManager | None = None) -> None:
    """Clear settings entries in the namespace"""
    manager = manager if manager is not None else SettingsManager()
    manager.__dict__.clear()

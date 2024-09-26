"""Namespace for uniquely storing settings"""

from types import SimpleNamespace
from typing import Any

__all__ = ("settings", "SettingsManager", "clear")


class SettingsManager(SimpleNamespace):
    """The settings namespace manager"""

    def __setattr__(self, name: str, value: Any) -> None:
        # If a setting descriptor is set to the namespace directly--i.e. it's not
        # owned by a class--then the settings manager namespace's name should be used
        # as a name. In this case, the setting descriptor's __set_name__ method was
        # not called
        if hasattr(value, "desc") and getattr(value, "name", None) is None:
            value.name = name

        return super().__setattr__(name, value)


#: The root settings namespace
settings: SettingsManager = SettingsManager()

#: Utility functions for settings


def clear(ns: SettingsManager | None = None) -> None:
    """Clear settings entries in the namespace"""
    ns = ns if ns is not None else settings
    ns.__dict__.clear()

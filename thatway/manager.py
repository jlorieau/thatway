"""Namespace for uniquely storing settings"""

from types import SimpleNamespace

__all__ = ("settings", "SettingsNamespace")


class SettingsNamespace(SimpleNamespace):
    """The settings namespace"""

    def clear(self) -> None:
        """Clear entries in the settings namespace"""
        self.__dict__.clear()


#: The root settings namespace
settings: SettingsNamespace = SettingsNamespace()

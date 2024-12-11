"""Utility functions for SettingsManager and Setting objects"""

import inspect

from .base import Setting, SettingsManager

__all__ = ("clear", "locate")


def clear(settings: SettingsManager | None = None) -> None:
    """Clear the settings and managers for the given SettingsManager.

    Parameters
    ----------
    settings
        The settings manager to clear (reset) the settings
    """
    settings = settings if settings is not None else SettingsManager()

    deletable_items = list(settings)
    deletable_attrs = [k for k, v in settings.__dict__.items() if v in deletable_items]

    for attr in deletable_attrs:
        delattr(settings, attr)


def locate(settings: SettingsManager | None = None) -> dict[str, dict[int, Setting]]:
    """Locate the instantiation location of settings in source files.

    Parameters
    ----------
    settings
        The settings manager object to analyze for locations

    Returns
    -------
    locations
        A dict with source code filepathss as keys with dicts as values of
        linenumbers/settings.
    """
    settings = settings if settings is not None else SettingsManager()

    # Organize the settings
    locations: dict[str, dict[int, Setting]] = dict()
    for item in settings:
        if isinstance(item, Setting):
            filename, lineno = getattr(item, "__location__", ("UNKNOWN", -1))
            locations.setdefault(filename, dict())[lineno] = item
        elif isinstance(item, SettingsManager):
            locations.update(locate(item))
        else:
            continue

    return locations

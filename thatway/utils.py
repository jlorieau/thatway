"""Utility functions for SettingsManager and Setting objects"""

import inspect

from .base import Setting, SettingsManager

__all__ = ("clear", "locate")


def clear(settings: SettingsManager | None = None) -> None:
    """Clear the settings and managers for the given SettingsManager"""
    settings = settings if settings is not None else SettingsManager()

    deletable_items = list(settings)
    deletable_attrs = [k for k, v in settings.__dict__.items() if v in deletable_items]

    for attr in deletable_attrs:
        delattr(settings, attr)


def locate(
    settings: SettingsManager | None = None, level: int = 0, pprint: bool = True
) -> dict[str, dict[int, Setting]]:
    """Reveal the module locations for different settings"""
    settings = settings if settings is not None else SettingsManager()

    # Organize the settings
    locations: dict[str, dict[int, Setting]] = dict()
    for item in settings:
        if isinstance(item, Setting):
            filename, lineno = getattr(item, "__location__", ("UNKNOWN", -1))
            locations.setdefault(filename, dict())[lineno] = item
        elif isinstance(item, SettingsManager):
            locations.update(locate(settings=item, level=level + 1))
        else:
            continue

    # Pretty-print, if desired
    if pprint and level == 0:
        for filename in sorted(locations.keys()):
            print(filename)

            for lineno in sorted(locations[filename].keys()):
                item = locations[filename][lineno]
                print(f"  {lineno}: {item}")

    return locations

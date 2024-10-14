"""Utility functions for SettingsManager and Setting objects"""

from .base import SettingsManager

__all__ = ("clear",)


def clear(settings: SettingsManager | None = None) -> None:
    """Clear the settings and managers for the given SettingsManager"""
    settings = settings if settings is not None else SettingsManager()

    deletable_items = list(settings)
    deletable_attrs = [k for k, v in settings.__dict__.items() if v in deletable_items]

    for attr in deletable_attrs:
        delattr(settings, attr)

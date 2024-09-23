"""Namespace for uniquely storing settings"""

from pathlib import Path
from types import SimpleNamespace
from typing import TextIO

import yaml

__all__ = ("settings", "SettingsManager", "clear")


class SettingsManager(SimpleNamespace):
    """The settings namespace manager"""


#: The root settings namespace
settings: SettingsManager = SettingsManager()

#: Utility functions for settings


def clear(ns: SettingsManager | None = None) -> None:
    """Clear settings entries in the namespace"""
    ns = ns if ns is not None else settings
    ns.__dict__.clear()


def load_yaml(fileobj: TextIO | Path, ns: SettingsManager | None = None) -> None:
    """Load settings from YAML"""
    ns = ns if ns is not None else settings
    d = yaml.load(fileobj)
    ns.__dict__.update(d)


def save_yaml(fileobj: TextIO | Path, ns: SettingsManager | None = None) -> None:
    """Save settings to YAML"""
    ns = ns if ns is not None else settings
    yaml.dump(ns.__dict__, fileobj)

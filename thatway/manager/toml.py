"""
Utilities for saving and loading TOML files.
"""

from pathlib import Path
from types import SimpleNamespace
from typing import TextIO

from tomlkit import TOMLDocument, document
from tomlkit import dump as _dump_toml
from tomlkit import load as _load_toml
from tomlkit import nl, table
from tomlkit.items import Item, Table

from ..exceptions import SettingException
from .manager import settings

__all__ = ("load_toml", "save_toml")


def update_namespace(ns: SimpleNamespace, component: TOMLDocument | Table) -> None:
    """Update settings namespace from a TOML document (or table)

    Parameters
    ----------

    Returns
    -------

    Raises
    ------
    """

    for k, v in component.items():
        setting = getattr(ns, k, None)

        if isinstance(setting, SimpleNamespace):
            # Parse the sub-namespace
            update_namespace(setting, v)

        elif setting is not None and hasattr(setting, "default"):
            # Get the type of the default
            type_default = type(setting.default)

            # Change the setting and force the type conversion
            setting.default = type_default(v)

        else:
            raise SettingException(f"Setting '{k}' could not be found in the settings.")


def load_toml(fileobj: TextIO | Path, ns: SimpleNamespace | None = None) -> None:
    """Load settings namespace from TOML"""
    ns = ns if ns is not None else settings

    if isinstance(fileobj, Path):
        with fileobj.open(mode="r") as f:
            document = _load_toml(f)
    else:
        document = _load_toml(fileobj)

    update_namespace(ns, document)


def build_toml(
    ns: SimpleNamespace, component: TOMLDocument | Table | None = None
) -> TOMLDocument | Table:
    """Create a TOML document (or table) from the given namespace"""
    # Create a TOML document, if needed
    component = component if component is not None else document()

    # Iterate over the items in the namespace
    for k, v in ns.__dict__.items():
        # Entries must have names (strings)
        if not isinstance(k, str):
            continue

        # If it's a namespace, create a new sub-table
        if isinstance(v, SimpleNamespace):
            component[k] = build_toml(ns=v, component=table())
            continue

        # If it's a setting, enter it directly
        if hasattr(v, "default"):
            component[k] = v.default
        else:
            continue

        # Add a comment for the description
        item = component[k]
        if hasattr(v, "desc") and isinstance(item, Item):
            item.comment(v.desc)

    return component


def save_toml(fileobj: TextIO | Path, ns: SimpleNamespace | None = None) -> None:
    """Save settings to TOML"""
    ns = ns if ns is not None else settings
    document = build_toml(ns=ns)

    if isinstance(fileobj, Path):
        with fileobj.open(mode="w") as f:
            _dump_toml(document, f)
    else:
        _dump_toml(document, fileobj)

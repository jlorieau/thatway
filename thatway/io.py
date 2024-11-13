"""
SettingsManager I/O methods
"""

from enum import Enum, auto
from io import IOBase, TextIOBase
from pathlib import Path
from typing import IO

from tomlkit import TOMLDocument, document
from tomlkit import dump as _dump_toml
from tomlkit import load as _load_toml
from tomlkit import table
from tomlkit.items import Item, Table

from .base import Setting, SettingException, SettingsManager

__all__ = ("load", "save")


class FileType(Enum):
    """Setting input/output filetyoes."""

    AUTO = auto()
    TOML = auto()


def load(
    filepath: Path,
    settings: SettingsManager | None = None,
    filetype: FileType = FileType.AUTO,
) -> None:
    """Load settings.

    Parameters
    ----------
    filepath
        The path to load settings from.
    settings
        The settings manager to save. The global settings manager is loaded, if None
        is specified.
    filetype
        The format (type) of data in the settings file. If "AUTO", then the type
        will be inferred from the filepath extension.
    """
    settings = settings if settings is not None else SettingsManager()

    # Determine the filetype
    if filetype is FileType.TOML or FileType.AUTO and filepath.suffix in (".toml",):
        with filepath.open(mode="r") as stream:
            load_toml(stream, settings=settings)
    else:
        raise NotImplementedError


def save(
    filepath: Path,
    settings: SettingsManager | None = None,
    filetype: FileType = FileType.AUTO,
) -> None:
    """Save settings.

    Parameters
    ----------
    filepath
        The path to save settings to.
    settings
        The settings manager to save. The global settings manager is loaded, if None
        is specified.
    filetype
        The format (type) of data in the settings file. If "AUTO", then the type
        will be inferred from the filepath extension.
    """
    settings = settings if settings is not None else SettingsManager()

    # Determine the filetype
    if filetype is FileType.TOML or FileType.AUTO and filepath.suffix in (".toml",):
        with filepath.open(mode="w") as stream:
            save_toml(stream, settings=settings)
    else:
        raise NotImplementedError


def load_toml(
    input: IO[str] | TOMLDocument | Table, settings: SettingsManager | None = None
) -> None:
    """Load settings namespace from TOML.

    Parameters
    ----------
    input
        The path or TOML object to load data from.
    settings
        The settings manager namespace to load settings into

    Exceptions
    ----------
    SettingExpection
        Raised when trying to set a setting that doesn't exist in the settings manager
        namespace.
    NotImplementedError
        An unknown input type was inserted
    """
    settings = settings if settings is not None else SettingsManager()

    if isinstance(input, IOBase):
        document = _load_toml(input)
        return load_toml(document, settings)

    elif isinstance(input, TOMLDocument | Table):

        for k, v in input.items():
            # Retrieve from the __dict__ directly because the __getattribute__
            # returns an empty sub-SettingsManager by default
            sub_setting = settings.__dict__.get(k, None)

            if isinstance(sub_setting, SettingsManager):
                # Parse the sub-namespace
                load_toml(v, sub_setting)

            elif isinstance(sub_setting, Setting):
                # Get the type of the default
                type_default = type(sub_setting.value)

                # Change the setting and force the type conversion
                sub_setting.value = type_default(v)

            else:
                raise SettingException(
                    f"Setting '{k}' could not be found in the settings."
                )

    else:
        raise NotImplementedError(f"Input type '{type(input)}' unsupported.")


def save_toml(
    output: IO[str] | TOMLDocument | Table, settings: SettingsManager | None = None
) -> None:
    """Save settings to TOML.

    Parameters
    ----------
    output
        The file-like object or path to load the TOML data from
    settings
        The settings manager namespace to read settings from
    """
    settings = settings if settings is not None else SettingsManager()

    if isinstance(output, IOBase):
        # Create the TOML document and save to the given path
        doc = document()

        # Update the document with the settings
        save_toml(doc, settings)

        # Open the file path, and write the given document
        _dump_toml(doc, output)

    elif isinstance(output, TOMLDocument | Table):

        # Iterate over the items in the namespace
        for k, v in settings.__dict__.items():
            if isinstance(v, SettingsManager):
                # If it's a SettingsManager, create a new sub-table
                tab = table()
                save_toml(tab, v)
                output[k] = tab

            elif isinstance(v, Setting):
                # If it's a setting, enter it directly
                output[k] = v.value

                # Add a comment for the description
                item = output[k]
                if hasattr(v, "desc") and isinstance(item, Item):
                    item.comment(v.desc)

            else:
                continue

    else:
        raise NotImplementedError

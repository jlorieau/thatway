"""
SettingsManager I/O methods
"""

from pathlib import Path

from tomlkit import TOMLDocument
from tomlkit import dump as _dump_toml
from tomlkit import load as _load_toml
from tomlkit.items import Table

from .base import Setting, SettingException, SettingsManager

__all__ = ("load_toml",)


def load_toml(
    input: Path | TOMLDocument | Table, settings: SettingsManager | None = None
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

    if isinstance(input, Path):

        with input.open(mode="r") as f:
            document = _load_toml(f)
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


# def build_toml(
#     ns: SimpleNamespace, component: TOMLDocument | Table | None = None
# ) -> TOMLDocument | Table:
#     """Create a TOML document (or table) from the given namespace.

#     Parameters
#     ----------
#     ns
#         The settings manager namespace to read settings from
#     component
#         The TOML document or table to create or modify with the settings from ns.

#     Returns
#     -------
#     document_or_table
#         The TOML document or table created or modified with the settings from ns.
#     """
#     # Create a TOML document, if needed
#     component = component if component is not None else document()

#     # Iterate over the items in the namespace
#     for k, v in ns.__dict__.items():
#         # Entries must have names (strings)
#         if not isinstance(k, str):
#             continue

#         # If it's a namespace, create a new sub-table
#         if isinstance(v, SimpleNamespace):
#             component[k] = build_toml(ns=v, component=table())
#             continue

#         # If it's a setting, enter it directly
#         if hasattr(v, "default"):
#             component[k] = v.default
#         else:
#             continue

#         # Add a comment for the description
#         item = component[k]
#         if hasattr(v, "desc") and isinstance(item, Item):
#             item.comment(v.desc)

#     return component


# def save_toml(input: TextIO | Path, ns: SimpleNamespace | None = None) -> None:
#     """Save settings to TOML.

#     Parameters
#     ----------
#     fileobj
#         The file-like object or path to load the TOML data from
#     ns
#         The settings manager namespace to read settings from
#     """
#     ns = ns if ns is not None else settings
#     document = build_toml(ns=ns)

#     if isinstance(fileobj, Path):
#         with fileobj.open(mode="w") as f:
#             _dump_toml(document, f)
#     else:
#         _dump_toml(document, fileobj)

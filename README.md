# ThatWay

[![PyPI version](https://img.shields.io/pypi/v/thatway.svg)](https://pypi.org/project/thatway/)
[![Black formatted](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


Many settings and configuration managers exist. Most, if not all, require settings to be placed in a centralized place in your project, introducing couplings between sub-modules and separating settings from the places they're used. 

Thatway was created to make it easy to pepper your python files with settings and have them automatically collected in one place. Settings can have optional descriptions and validated with arbitrary conditions, and settings can be updated from files.

Using Thatway is as easy as adding settings attributes to a class:

```python
>>> from thatway import Setting
>>>
>>> class FirstClass:
...     my_attribute = Setting(True)
...     max_instances = Setting(3, "Maximum number of instances")

```

## Quickstart


### 1. Create Settings

as class members

  ```python
  >>> from thatway import Setting    
  >>> class SecondClass:
  ...     my_attribute = Setting(True)
  ...     max_instances = Setting(3, "Maximum number of instances")

  ```

as independent settings

  ```python
  >>> from thatway import settings
  >>> settings.moduleB.msg = Setting("This is my message")

  ```

### 2. Enforce Conditions (optionally)

```python
>>> from thatway.conditions import is_positive, lesser_than, within, allowed
>>> class Display:
...     width = Setting(768, "Screen width", 
...                     is_positive,
...                     lesser_than(2045))
...     height = Setting(1024, "Screen height",
...                      is_positive, 
...                      within(1023, 4096))
...     dpi = Setting(144, "Screen dots-per-inch",
...                   allowed(90, 120, 144, 160)) 

```

Conditions are any callable that takes a value
and returns a bool to indicate whether the value is valid (True) or invalid (False).

Thatway comes with some simple conditions:

| Function            | Description                         |
|---------------------|-------------------------------------|
| `is_positive`       | Value is greater than zero.  `int`, `float` and `double` |
| `is_negative`       | Value is smaller than zero. `int`, `float` and `double` |
| `greater_than(low)` | Value is greater than `low` bound |
| `lesser_than(high)` | Value is smaller than `high` bound |
| `within(low, high)` | Value is greater than `low` bound and smaller than `high` bound. |
| `allowed(*values)`  | Value is one of the specified `*values` |

### 3. Load and Save Settings

Load and save settings in [TOML](https://toml.io/en/) format.

```python
>>> from thatway import load, FileType
>>> from tempfile import NamedTemporaryFile
>>> from pathlib import Path
...
>>> class ThirdClass:  # create some settings
...     attribute = Setting(1, "An attribute")
...
>>> ThirdClass().attribute
1
>>> with NamedTemporaryFile(mode='w') as tp:  # load these settings from a file
...     toml = """
...     [__main__.ThirdClass]
...     attribute = 2"""
...     _ = tp.write(toml)
...     tp.flush()
...     load(Path(tp.name), settings, FileType.TOML)
...
>>> ThirdClass().attribute
2

```

### 4. View settings

```python
>>> from thatway import clear
>>> clear(settings)  # reset the settings
>>> class Search:  # Create some new settings
...     text = Setting("type search here...", "Search text")
...     max_characters = Setting(1024, "Maximum allowed characters", is_positive)
>>> settings.database_ip = Setting("128.0.0.1", "IP address for the database connection")
>>> print(settings)
__main__
  Search
    Setting(text=type search here...)
    Setting(max_characters=1024)
Setting(database_ip=128.0.0.1)

```

## Rules

The following are design decisions on the behavior of thatway's configuration
manager.

### 1. Setting Precedence

Setting values come from 3 different sources, in order of decreasing precedence:

(1) The instance's value

```python
>>> class PrecedenceA:  # Create a default setting
...     attribute = Setting(3, "Precedence-testing attribute") 
>>> settings.__main__.PrecedenceA.attribute.value = 2  # Set a setting manager value
>>> instance = PrecedenceA()
>>> instance.attribute = 1  # Set an instance value
>>> instance.attribute
1

```

(2) The setting manager's value

```python
>>> class PrecedenceB:  # Create a default setting
...     attribute = Setting(3, "Precedence-testing attribute") 
>>> settings.__main__.PrecedenceB.attribute.value = 2  # Set a setting manager value
>>> instance = PrecedenceB()
>>> instance.attribute
2

```

(3) The default value set on creation of the setting.

```python
>>> class PrecedenceC:  # Create a default setting
...     attribute = Setting(3, "Precedence-testing attribute") 
>>> instance = PrecedenceC()
>>> instance.attribute
3

```

### 2. Settings Locking

Settings cannot be accidentally modified.

(1) Replacing a setting with a new setting is not possible:

```python
>>> from thatway import SettingException  
>>> settings.b = Setting(3)
>>> settings.b
Setting(b=3)
>>> settings.b = Setting(5)  # oops! Can't create a new setting
Traceback (most recent call last):
...
thatway.base.SettingException: Attribute 'b' already exists as a Setting (Setting(b=3))

```

(2) or replacing a setting with a non-setting.

```python
>>> settings.b = 5  # oops! Can't assign a non-setting.
Traceback (most recent call last):
...
AttributeError: Cannot insert value of type '<class 'int'>' in a SettingsManager.
```

but the value of the setting can be updated, as long as it's valid--i.e. it passes the validation conditions.

```python
>>> settings.b.value = 5
>>> settings.b
Setting(b=5)

```

### 3. Type Enforcement

Setting types are checked and maintained with either the setting's value type.

```python
>>> settings.c = Setting(5, "The value of c")
>>> settings.c.value = "A new type doesn't work!"
'my new c value'
>>> settings.c.value = 6
>>> settings.c
```

6. Missing Settings

    Trying to update a setting that doesn't exist is not possible. This behavior
    is designed to avoid trying to change a setting but using an incorrect setting
    name and location.

    ```python
    >>> from thatway import Setting
    >>> config.update({'e': 'unassigned'})  # 'f' doesn't exist in config
    Traceback (most recent call last):
    ...
    KeyError: "Tried assigning setting with name 'e' which does not exist in the Config"
    ```

7. Immutable Settings Values

    Setting values can only be immutable objects.

    ```python
    >>> from thatway import Setting
    >>> config.cli.color = Setting(True)
    >>> config.cli.default_filenames = Setting(('a.html', 'b.html'))
    >>> config.cli.value_list = Setting([1, 2])  # lists are mutable
    Traceback (most recent call last):
    ...
    thatway.base.ConfigException: Setting value '[1, 2]' must be immutable
    ```

Features
--------

1. Setting descriptions

    Settings can include descriptions.

    ```python
    >>> from thatway import Setting
    >>> config.e = Setting(4, desc="The 'e' attribute")
    ```

2. Yaml processing. Settings can be dumped in [yaml](https://yaml.org) with `config.dumps_yaml()`.

    ```yaml
    Obj:
      a: 1
    b: name  # The 'b' setting
    nested:
      c: true
    ```

    And [yaml](https://yaml.org) strings or files can be loaded with
    `config.loads_yaml(string)` and `config.load_yaml(filepath)`, respectively.

3. Toml processing

    Settings can be dumped in [toml](https://toml.io/en/) with `config.dumps_toml()`.

    ```toml
    [Obj]
      a = 1
    b = "name"  # The 'b' setting
    [nested]
      c = true
    ```

    And [toml](https://toml.io/en/) strings or files can be loaded with
    `config.loads_toml(string)` and `config.load_toml(filepath)`, respectively.

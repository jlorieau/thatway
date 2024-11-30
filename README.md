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

Create settings as class members, with or without a description...

```python
>>> from thatway import Setting    
>>> class SecondClass:
...     my_attribute = Setting(True)  # without description
...     max_instances = Setting(3, "Maximum number of instances")  # with description
```

or as independent settings not associated with a class,

```python
>>> database_ip = Setting("127.0.0.1")
```


or assign them to the settings manager direccly.

```python
>>> from thatway import settings
>>> settings.moduleB.msg = Setting("This is my message")
```

Then setting are collected in a global `settings` manager.

```python
>>> print(settings)
__main__
  FirstClass
    Setting(my_attribute=True)
    Setting(max_instances=3)
  SecondClass
    Setting(my_attribute=True)
    Setting(max_instances=3)
moduleB
  Setting(msg=This is my message)
```

### 2. Enforce Conditions (optionally)

Settings can have a series of conditions that must pass in order to replace the
value of the setting.

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
and returns a bool to indicate whether the value is valid (True) or invalid (False):
`Callable[[Any], bool]`

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

### 4. View and Locate Settings

Settings manager objects can be view as a nested tree.

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

The source code locations where individual settings can be revealed too.

```python
>>> from thatway import locate
>>> from pprint import pprint
>>> locations = locate(settings)
>>> pprint(locations)
{'<doctest README.md[19]>': {2: Setting(text=type search here...),
                             3: Setting(max_characters=1024)},
 '<doctest README.md[20]>': {1: Setting(database_ip=128.0.0.1)}}
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

Replacing a setting with a new setting is not possible,

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

or replacing a setting with a non-setting.

```python
>>> settings.b = 5  # oops! Can't assign a non-setting.
Traceback (most recent call last):
...
AttributeError: Cannot insert value of type '<class 'int'>' in a SettingsManager.
```

But the value of the setting can be updated, as long as it's valid--i.e. it passes 
the validation conditions.

```python
>>> settings.b.value = 5
>>> settings.b
Setting(b=5)
```

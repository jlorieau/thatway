ThatWay
=======
[![PyPI version](https://img.shields.io/pypi/v/thatway.svg)](https://pypi.org/project/thatway/)
[![Black formatted](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


Loads of settings and configuration managers exist, but none make it easy to pepper your python files with settings and have them collected in one place. Thatway was created for this purpose.

```python
>>> from thatway import Setting
>>>
>>> class FirstClass:
...     my_attribute = Setting(True)
...     max_instances = Setting(3, "Maximum number of instances")

```

Thatway is a decentralized yet simple settings (configuration) manager. Place your settings throughout your application--not in a centralized file or submodule--and thatway collects them and allows you to modify them through configurations files. Decentralized configuration reduces the complexity of submodules and the coupling between submodules.

Quickstart
----------

1. **Create settings**

   as class members

      ```python
      >>> from thatway import Setting    
      >>> class SecondClass:
      ...     my_attribute = Setting(True)
      ...     max_instances = Setting(3, "Maximum number of instances")

      ```

   as independent settings

      ```python
      >>> from thatway import settings, Setting
      >>>
      >>> settings.moduleB.msg = Setting("This is my message")

      ```

2. **Enforce conditions** (optionally)

   ```python
   >>> from thatway import Setting
   >>> from thatway.conditions import is_positive, lesser_than, within, allowed
   >>>
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

   | Function            | Description                         |
   |---------------------|-------------------------------------|
   | `is_positive`       | Value is greater than zero.  `int`, `float` and `double` |
   | `is_negative`       | Value is smaller than zero. `int`, `float` and `double` |
   | `greater_than(low)` | Value is greater than `low` bound |
   | `lesser_than(high)` | Value is smaller than `high` bound |
   | `within(low, high)` | Value is greater than `low` bound and smaller than `high` bound. |
   | `allowed(*values)`  | Value is one of the specified `*values` |

3. **Load and save settings**

   Load and save settings in [TOML](https://toml.io/en/) format.

    

    ```python
    >>> from thatway import Setting, settings, load, FileType
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

3. **View settings**

    ```python
    >>> from thatway import Setting, settings, clear
    >>> from thatway.conditions import is_positive
    ...
    >>> clear(settings)  # clear existing settings
    >>> class Search:
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

Rules
-----

The following are design decisions on the behavior of thatway's configuration
manager.

1. Configure directly


    Settings can be set directly on the config object.

    ```python
    >>> from thatway import settings, Setting
    >>> settings.a = Setting(3)
    >>> settings.a.value
    3
    >>> settings.nested.b = Setting("nested")
    >>> settings.nested.b.value
    'nested'

    ```

    Trying to set an entry in the config without a setting raises an exception.

    ```python
    >>> from thatway import settings
    >>> settings.new_value = 3
    Traceback (most recent call last):
    ...
    AttributeError: Cannot insert value of type '<class 'int'>' in a SettingsManager.

    ```

2. Configure object attributes

    Settings can be set as object attributes.

    ```python
    >>> from thatway import Setting
    >>> class Obj:
    ...     attribute = Setting("my value")
    >>> obj = Obj()
    >>> obj.attribute
    'my value'

    ```

3. Configuration locking

    Settings cannot be accidentally modified. Once they're set, they're set until
    the config's ``update`` or ``load`` methods are used.

    ```python
    >>> from thatway import Setting
    >>> settings.b = Setting(3)
    >>> settings.b
    3
    >>> settings.b = Setting(5)  # oops!
    Traceback (most recent call last):
    ...
    thatway.base.ConfigException: Entry 'b' already in the Config--use a Config.update or load method to change its value.
    >>> settings.b = 5  # oops!
    Traceback (most recent call last):
    ...
    thatway.base.ConfigException: Only Settings can be inserted in the Config
    >>> settings.update({'b': 5})
    >>> settings.b
    5
    ```

    The one exception is that settings defined on a class can be replaced on the
    class itself--not a class instance. This is because settings act as
    descriptors for classes.

4. Type Enforcement

    Setting types are checked and maintained with either the setting's value type,
    or the ``allowed_types`` optional argument.

    ```python
    >>> from thatway import Setting
    >>> config.c = Setting(5, allowed_types=(int, str))
    >>> config.update({'c': 'my new c value'})
    >>> config.c
    'my new c value'
    >>> config.d = Setting(6)
    >>> config.update({'d': 'my new d value'})
    Traceback (most recent call last):
    ...
    ValueError: Could not convert 'my new d value' into any of the following types: [<class 'int'>]
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

ThatWay
=======
Thatway is a simple, decentralized configuration manager.

Place your configuration settings throughout your application--not in a
centralized file or submodule--and thatway collects them and allows you to
modify them through configurations files. Decentralized configuration reduces
the complexity of submodules and the coupling between submodules.

Rules
-----

The following are design decisions on the behavior of thatway's configuration
manager.

1. Configure directly
~~~~~~~~~~~~~~~~~~~~~

Settings can be set directly on the config object.

.. code-block:: python

    >>> from thatway import config, Setting
    >>> config.a = Setting(3)
    >>> config.a
    3
    >>> config.nested.b = Setting("nested")
    >>> config.nested.b
    'nested'

2. Configure object attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Settings can be set as object attributes.

.. code-block:: python

    >>> from thatway import Setting
    >>> class Obj:
    ...     attribute = Setting("my value")
    >>> obj = Obj()
    >>> obj.attribute
    'my value'


3. Configuration locking
~~~~~~~~~~~~~~~~~~~~~~~~

Settings cannot be accidentally modified. Once they're set, they're set until
the config's ``update`` or ``load`` methods are used.

.. code-block:: python

    >>> from thatway import Setting
    >>> config.b = Setting(3)
    >>> config.b
    3
    >>> config.b = Setting(5)  # oops!
    Traceback (most recent call last):
    ...
    thatway.base.ConfigException: Entry 'b' already in the Config--use a Config.update or load method to change its value.
    >>> config.b = 5  # oops!
    Traceback (most recent call last):
    ...
    thatway.base.ConfigException: Only Settings can be inserted in the Config
    >>> config.update({'b': 5})
    >>> config.b
    5

The one exception is that settings defined on a class can be replaced on the
class itself--not a class instance. This is because settings act as
descriptors for classes.

4. Type Enforcement
~~~~~~~~~~~~~~~~~~~

Setting types are checked and maintained with either the setting's value type,
or the ``allowed_types`` optional argument.

.. code-block:: python

    >>> from thatway import Setting
    >>> config.d = Setting(5, allowed_types=(int, str))
    >>> config.update({'d': 'my new d value'})
    >>> config.d
    'my new d value'
    >>> config.e = Setting(6)
    >>> config.update({'e': 'my new e value'})
    Traceback (most recent call last):
    ...
    ValueError: Could not convert 'my new e value' into any of the following types: [<class 'int'>]

6. Missing Settings
~~~~~~~~~~~~~~~~~~~

Trying to update a setting that doesn't exist is not possible. This behavior
is designed to avoid trying to change a setting but using an incorrect setting
name and location.

.. code-block:: python

    >>> from thatway import Setting
    >>> config.update({'f': 'unassigned'})  # 'f' doesn't exist in config
    Traceback (most recent call last):
    ...
    KeyError: "Tried assigning setting with name 'f' which does not exist in the Config"

Features
--------

1. Setting descriptions
~~~~~~~~~~~~~~~~~~~~~~~~~

Settings can include descriptions.

.. code-block:: python

    >>> from thatway import Setting
    >>> config.c = Setting(4, desc="The 'c' attribute")

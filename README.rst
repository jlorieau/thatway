ThatWay
=======
.. image:: https://img.shields.io/pypi/v/thatway.svg
    :target: https://pypi.org/project/thatway/
    :alt: PyPI version

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Black formatted

Thatway is a simple, decentralized configuration manager.

Place your configuration settings throughout your application--not in a
centralized file or submodule--and thatway collects them and allows you to
modify them through configurations files. Decentralized configuration reduces
the complexity of submodules and the coupling between submodules.

Quickstart
----------

1. Create a package with settings.

`examples/mypkg/moduleA/file.py <examples/mypkg/moduleA/file.py>`_

.. code-block:: python

    from thatway import Setting


    class FirstClass:
        my_attribute = Setting(True, desc="Whether 'my_attribute' is an attribute")

        max_instances = Setting(3, desc="Maximum number of instances")

`examples/mypkg/moduleB/file.py <examples/mypkg/moduleB/file.py>`_

.. code-block:: python

    from thatway import config, Setting

    config.moduleB.msg = Setting("This is my message")

2. View settings:

.. code-block:: python

    import examples.mypkg
    from thatway import config
    print(config.dumps_yaml())
    FirstClass:
      my_attribute: true  # Whether 'my_attribute' is an antribue
      max_instances: 3  # Maximum number of instances
    moduleB:
      msg: This is my message

3. Load different settings:

`examples/mypkg/new_settings.yaml <examples/mypkg/new_settings.yaml>`_

.. code-block:: yaml

    FirstClass:
      my_attribute: false
      max_instances: 2

with python:

.. code-block:: python

    from pathlib import Path
    import examples.mypkg
    from thatway import config
    config.load_yaml(str(Path("examples") / "mypkg" / "new_settings.yaml"))
    print(config.dumps_yaml())
    FirstClass:
      my_attribute: false  # Whether 'my_attribute' is an antribue
      max_instances: 2  # Maximum number of instances
    moduleB:
      msg: This is my message

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

Trying to set an entry in the config without a setting raises an exception.

.. code-block:: python

    >>> from thatway import config
    >>> config.new_value = 3
    Traceback (most recent call last):
    ...
    thatway.base.ConfigException: Only Settings can be inserted in the Config

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
    >>> config.c = Setting(5, allowed_types=(int, str))
    >>> config.update({'c': 'my new c value'})
    >>> config.c
    'my new c value'
    >>> config.d = Setting(6)
    >>> config.update({'d': 'my new d value'})
    Traceback (most recent call last):
    ...
    ValueError: Could not convert 'my new d value' into any of the following types: [<class 'int'>]

6. Missing Settings
~~~~~~~~~~~~~~~~~~~

Trying to update a setting that doesn't exist is not possible. This behavior
is designed to avoid trying to change a setting but using an incorrect setting
name and location.

.. code-block:: python

    >>> from thatway import Setting
    >>> config.update({'e': 'unassigned'})  # 'f' doesn't exist in config
    Traceback (most recent call last):
    ...
    KeyError: "Tried assigning setting with name 'e' which does not exist in the Config"

7. Immutable Settings Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Setting values can only be immutable objects.

.. code-block::

    >>> from thatway import Setting
    >>> config.cli.color = Setting(True)
    >>> config.cli.default_filenames = Setting(('a.html', 'b.html'))
    >>> config.cli.value_list = Setting([1, 2])  # lists are mutable
    Traceback (most recent call last):
    ...
    thatway.base.ConfigException: Setting value '[1, 2]' must be immutable

Features
--------

1. Setting descriptions
~~~~~~~~~~~~~~~~~~~~~~~~~

Settings can include descriptions.

.. code-block:: python

    >>> from thatway import Setting
    >>> config.e = Setting(4, desc="The 'e' attribute")

2. Yaml processing
~~~~~~~~~~~~~~~~~~

Settings can be dumped in `yaml <https://yaml.org>`_.

``config.dumps_yaml()``

.. code-block:: yaml

    Obj:
      a: 1
    b: name  # The 'b' setting
    nested:
      c: true

And `yaml <https://yaml.org>`_ strings or files can be loaded with
``config.loads_yaml(string)`` and ``config.load_yaml(filepath)``, respectively.

3. Toml processing
~~~~~~~~~~~~~~~~~~

Settings can be dumped in `toml <https://toml.io/en/>`_.

``config.dumps_toml()``

.. code-block:: toml

    [Obj]
      a = 1
    b = "name"  # The 'b' setting
    [nested]
      c = true

And `toml <https://toml.io/en/>`_ strings or files can be loaded with
``config.loads_toml(string)`` and ``config.load_toml(filepath)``, respectively.

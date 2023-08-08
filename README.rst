ThatWay
=======
Thatway is a simple, decentralized configuration manager.

Place your configuration settings throughout your application, and thatway
collects them and allows you to modify them through configurations files.

Rules
-----

The following are design decisions on the behavior of thatway's configuration manager.

1. Configure directly
~~~~~~~~~~~~~~~~~~~~~

Parameters can be set directly on the config object.

.. code-block:: python

    >>> from thatway import config, Parameter
    >>> config.a = Parameter(3)
    >>> config.a
    3
    >>> config.nested.b = Parameter("nested")
    >>> config.nested.b
    'nested'

2. Configure object attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameters can be set as object attributes.

.. code-block:: python

    >>> from thatway import Parameter
    >>> class Obj:
    ...     attribute = Parameter("my value")
    >>> obj = Obj()
    >>> obj.attribute
    'my value'


3. Configuration locking
~~~~~~~~~~~~~~~~~~~~~~~~

Parameters cannot be accidentally modified. Once they're set, they're set until
the config is updated.

.. code-block:: python

    >>> from thatway import Parameter
    >>> config.b = Parameter(3)
    >>> config.b
    3
    >>> config.b = Parameter(5)  # oops!
    Traceback (most recent call last):
    ...
    thatway.base.ConfigException: Entry 'b' already in the Config--use a Config.update or load method to change its value.
    >>> config.update({'b': 5})
    >>> config.b
    5

4. Type Enforcement
~~~~~~~~~~~~~~~~~~~

Parameter types are checked and maintained with the parameter's value type, and
the ``allowed_types`` optional argument.

.. code-block:: python

    >>> from thatway import Parameter
    >>> config.d = Parameter(5, allowed_types=(int, str))
    >>> config.update({'d': 'my new d value'})
    >>> config.d
    'my new d value'
    >>> config.e = Parameter(6)
    >>> config.update({'e': 'my new e value'})
    Traceback (most recent call last):
    ...
    ValueError: Could not convert 'my new e value' into any of the following types: [<class 'int'>]

6. Missing Parameters
~~~~~~~~~~~~~~~~~~~~~

Trying to update a parameter that doesn't exist is not possible.

.. code-block:: python

    >>> from thatway import Parameter
    >>> config.update({'f': 'unassigned'})  # 'f' doesn't exist in config
    Traceback (most recent call last):
    ...
    KeyError: "Tried assigning parameter with name 'f' which does not exist in the Config"

Features
--------

1. Parameter descriptions
~~~~~~~~~~~~~~~~~~~~~~~~~

Parameters can include descriptions.

.. code-block:: python

    >>> from thatway import Parameter
    >>> config.c = Parameter(4, desc="The 'c' attribute")

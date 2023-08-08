ThatWay
=======
Decentralized Configuration

Rules
-----

1. Configure directly
~~~~~~~~~~~~~~~~~~~~~

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

.. code-block:: python

    >>> from thatway import Parameter
    >>> class Obj:
    ...     attribute = Parameter("my value")
    >>> obj = Obj()
    >>> obj.attribute
    'my value'


3. Configuration locking
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> from thatway import Parameter
    >>> config.b = Parameter(3)
    >>> config.b
    3
    >>> config.b = Parameter(5)  # oops!
    Traceback (most recent call last):
    ...
    thatway.base.ConfigException: Entry 'b' already in the Config--use a Config.update or load method to change its value.

Parameter descriptions
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> from thatway import Parameter
    >>> config.c = Parameter(4, desc="The 'c' attribute")

Type Enforcement
~~~~~~~~~~~~~~~~

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

Missing Parameters
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> from thatway import Parameter
    >>> config.update({'f': 'unassigned'})  # 'f' doesn't exist in config
    Traceback (most recent call last):
    ...
    KeyError: "Tried assigning parameter with name 'f' which does not exist in the Config"

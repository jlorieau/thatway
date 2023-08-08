ThatWay
=======
Decentralized Configuration

Methods
-------

Configure directly
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> from thatway import config, Parameter
    >>> config.a = Parameter(3)
    >>> config.a
    3
    >>> config.nested.b = Parameter("nested")
    >>> config.nested.b
    'nested'

Configure object attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> from thatway import Parameter
    >>> class Obj:
    ...     attribute = Parameter("my value")
    >>> obj = Obj()
    >>> obj.attribute
    'my value'


Configuration locking
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> from thatway import Parameter
    >>> config.b = Parameter(3)
    >>> config.b
    3
    >>> config.b = Parameter(5)  # oops!
    Traceback (most recent call last):
    ...
    thatway.base.ConfigException: Entry 'b' already in the Config--use a load method to change its value.

Parameter descriptions
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> from thatway import Parameter
    >>> config.c = Parameter(3, desc="The 'c' attribute")

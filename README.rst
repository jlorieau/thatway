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
    >>> assert config.a == 3
    >>> config.nested.b = Parameter("nested")
    >>> assert config.nested.b == "nested"

Configure object attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> from thatway import Parameter
    >>> class Obj:
    ...     attribute = Parameter("my value")
    >>> obj = Obj()
    >>> assert obj.attribute == "my value"

Configuration locking
~~~~~~~~~~~~~~~~~~~~~

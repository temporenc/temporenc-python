====================
Temporenc for Python
====================

This is a Python library implementing the `temporenc format
<https://github.com/wbolster/temporenc>`_.

.. warning::

   This is alpha quality software — do not use for now!

____


Implemented:

* (un)packing support for all *temporenc* types

* parse into a ``temporenc.Value``

* use the most compact serialization format if no explicit type specified

* parsing works for both strings and file-like objects: ``unpackb()`` and
  ``unpack()`` just like the msgpack API

* packing of instances from the stdlib's ``datetime`` module


TODO:

* conversion to classes from the stdlib's ``datetime`` module with something
  like a ``.to_native()`` method

* time zone handing for native ``datetime`` types

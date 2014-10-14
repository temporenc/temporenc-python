====================
Temporenc for Python
====================

This is a Python library implementing the `temporenc format
<https://github.com/wbolster/temporenc>`_.

.. warning::

   This is alpha quality software — do not use for now!

____


Notes:

* parsing should work for both strings and file-like objects

* packing support for all *temporenc* types

* use the most compact serialization format if no explicit type specified

* parse into a ``temporenc.Value`` (``namedtuple`` or simple object); conversion
  to/from classes from the stdlib's ``datetime`` module with something like a
  ``.to_native()`` method.

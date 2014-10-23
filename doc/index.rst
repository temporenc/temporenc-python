Python library for *temporenc*
==============================

This is a Python library implementing the `temporenc format
<https://github.com/wbolster/temporenc>`_ for dates and times.

.. warning::

   This is alpha quality software — do not use for now!



Installation
============


Use ``pip`` to install the library (e.g. into a ``virtualenv``):

.. code-block:: shell-session

    $ pip install temporenc


Usage
=====

.. py:currentmodule:: temporenc

TODO


API
===

The :py:func:`packb` and :py:func:`unpackb` functions operate on byte strings.

.. autofunction:: packb
.. autofunction:: unpackb

The :py:func:`pack` and :py:func:`unpack` functions operate on file-like
objects.

.. autofunction:: pack
.. autofunction:: unpack

Both :py:func:`unpackb` and :py:func:`unpack` return an instance of the
:py:class:`Moment` class.

.. autoclass:: Moment
   :members:

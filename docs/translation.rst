.. Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
.. SPDX-License-Identifier: BSD-4-Clause

.. include:: links.rst

.. _mini-tutorial: mini-tutorial.rst

.. _pegen: https://github.com/we-like-parsers/pegen
.. _PEG parser: https://peps.python.org/pep-0617/

Translation
-----------

Translation is one of the most common tasks in language processing.
Analysis often sumarizes the parsed input, and *walkers* are good for that.


|TatSu| doesn't impose a way to create translators, but it
exposes the facilities it uses to generate the `Python`_ source code for
parsers.


Print Translation
~~~~~~~~~~~~~~~~~

Translation in |TatSu| is based on subclasses of ``NodeWalker``. Print-based translation
relies on classes that inherit from ``IndentPrintMixin``, a strategy copied from
the new PEG_ parser in Python_ (see `PEP 617`_).

``IndentPrintMixin`` provides an ``indent()`` method, which is a context manager,
and should be used thus:

.. code:: python

    class MyTranslationWalker(NodeWalker, IndentPrintMixin):

        def walk_SomeNodeType(self, node: NodeType):
            self.print('some preamble')
            with self.indent():
                # continue walking the tree
                self.print('something else')


The ``self.print()`` method takes note of the current level of indentation, so
output will be indented by the `indent` passed to
the ``IndentPrintMixin`` constructor, or to the ``indent(amount: int)`` method.
The mixin keeps as stack of the indent ammounts so it can go back to where it
was after each ``with indent(amount=n):`` statement:


.. code:: python

    def walk_SomeNodeType(self, node: NodeType):
        with self.indent(amount=2):
            self.print(node.exp)

The printed code can be retrieved using the ``printed_text()`` method, but other
posibilities are available by assigning a stream-like object to
``self.output_stream`` in the ``__init__()`` method.

A good example of how to do code generation with a ``NodeWalker`` and
``IndentPrintMixin`` is |TatSu|'s own code generator, which can be found
in ``tatsu/ngcodegen/pythongen.py``, or the model generation found in
``tatsu/ngcodegen/objectomdel.py``.


.. _PEP 617: https://peps.python.org/pep-0617/

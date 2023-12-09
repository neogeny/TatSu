.. include:: links.rst

Translation
-----------

Translation is one of the most common tasks in language processing.
Analysis often sumarizes the parsed input, and *walkers* are good for that.


|TatSu| doesn't impose a way to create translators, but it
exposes the facilities it uses to generate the `Python`_ source code for
parsers.

Translation in |TatSu| is based on subclasses of ``Walker`` and on classes that
inherit from ``IndentPrintMixin``, a strategy copied from the new PEG_ parser
in Python_ (see `PEP 617`_).

``IndentPrintMixin`` provides an ``indent()`` method, which is a context manager,
and should be used thus:

.. code:: python

    class MyTranslationWalker(NodeWalker, IndentPrintMixin):

        def walk_SomeNode(self, node):
            self.print('some preamble')
            with self.indent():
                # continue walking the tree


The ``self.print()`` method takes note of the current level of indentation, so
output will be indented by the `indent` passed to
the ``IndentPrintMixin`` constructor, or to the ``indent(iamoun:int)`` method.
The mixin keeps as stack of the indent ammounts so it can go back to where it
was after each ``with indent(amount=n):`` statement:


.. code:: python

    def walk_SomeNode(self, node):
        with self.indent(amount=2):
            self.print(walk_expression(node.exp))

The printed code can be retrieved using the ``printed_text()`` method, but other
posibilities are available by assigning a text-like object to
``self.output_stream`` in the ``__init__()`` method.

A good example of how to do code generation with a ``NodeWalker`` is |TatSu|'s own
code generator, which can be found in ``tatsu/ngcodegen/python.py``, or the model
generation found in ``tatsu/ngcodegen/objectomdel.py``.


.. _PEP 617: https://peps.python.org/pep-0617/

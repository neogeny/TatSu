.. include:: links.rst

Print Translation
-----------------


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
            with self.indent():
                # ccontinue walking the tree


The ``self.print()`` method takes note of the current level of indentation, so
output will be indented by the ``indent`` passed to
the ``IndentPrintConstructor``:

.. code:: python

    def walk_SomeNode(self, node):
        with self.indent():
            self.print(walk_expression(node.exp))

The printed code can be retrieved using the ``printed_text()`` method. Other
posibilities are available by assigning a text-like object to
``self.output_stream`` in the ``__init__()`` method.

.. _PEP 617: https://peps.python.org/pep-0617/

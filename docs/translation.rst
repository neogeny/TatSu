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

A good example of how to do code generation with a ``NodeWalker`` and ``IndentPrintMixin``
is |TatSu|'s own code generator, which can be
found in ``tatsu/ngcodegen/python.py``, or the model
generation found in ``tatsu/ngcodegen/objectomdel.py``.


.. _PEP 617: https://peps.python.org/pep-0617/


Declarative Translation (deprecated)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


|TatSu| provides support for template-based code generation ("translation", see below)
in the ``tatsu.codegen`` module.
Code generation works by defining a translation class for each class in the model specified by the grammar.

Nowadays the preferred code generation strategy is to walk down the AST_ and `print()` the desired output,
with the help of the ``NodWalker`` class, and the ``IndentPrintMixin`` mixin. That's the strategy used
by pegen_, the precursor to the new `PEG parser`_ in Python_. Please take a lookt at the
`mini-tutorial`_ for an example.

Basically, the code generation strategy changed from declarative with library support, to procedural,
breadth or depth first, using only standard Python_. The procedural code must know the AST_ structure
to navigate it, although other strategies are available with ``PreOrderWalker``, ``DepthFirstWalker``,
and ``ContextWalker``.

|TatSu| doesn't impose a way to create translators with it, but it
exposes the facilities it uses to generate the `Python`_ source code for
parsers.

Translation in |TatSu| was *template-based*, but instead of defining or
using a complex templating engine (yet another language), it relies on
the simple but powerful ``string.Formatter`` of the `Python`_ standard
library. The templates are simple strings that, in |TatSu|'s style,
are inlined with the code.

To generate a parser, |TatSu| constructs an object model of the parsed
grammar. A ``tatsu.codegen.CodeGenerator`` instance matches model
objects to classes that descend from ``tatsu.codegen.ModelRenderer`` and
implement the translation and rendering using string templates.
Templates are left-trimmed on whitespace, like `Python`_ *doc-comments*
are. This is an example taken from |TatSu|'s source code:

.. code:: python

    class Lookahead(ModelRenderer):
        template = '''\
                    with self._if():
                    {exp:1::}\
                    '''

Every *attribute* of the object that doesn't start with an underscore
(``_``) may be used as a template field, and fields can be added or
modified by overriding the ``render_fields(fields)`` method. Fields
themselves are *lazily rendered* before being expanded by the template,
so a field may be an instance of a ``ModelRenderer`` descendant.

The ``rendering`` module defines a ``Formatter`` enhanced to support the
rendering of items in an *iterable* one by one. The syntax to achieve
that is:

.. code:: python

        '''
        {fieldname:ind:sep:fmt}
        '''

All of ``ind``, ``sep``, and ``fmt`` are optional, but the three
*colons* are not. A field specified that way will be rendered using:

.. code:: python

    indent(sep.join(fmt % render(v) for v in value), ind)

The extended format can also be used with non-iterables, in which case
the rendering will be:

.. code:: python

    indent(fmt % render(value), ind)

The default multiplier for ``ind`` is ``4``, but that can be overridden
using ``n*m`` (for example ``3*1``) in the format.

**note**
    Using a newline character (``\n``) as separator will interfere with
    left trimming and indentation of templates. To use a newline as
    separator, specify it as ``\\n``, and the renderer will understand
    the intention.


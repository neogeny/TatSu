.. include:: links.rst

Templates Translation
--------------------------


**deprecated**

**note**
    As of |TatSu| 3.2.0, code generation was separated from grammar
    models through ``tatsu.codegen.CodeGenerator`` as to allow for code
    generation targets different from `Python`_. Still, the use of
    inline templates and ``rendering.Renderer`` hasn't changed. See the
    *regex* example for merged modeling and code generation.

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


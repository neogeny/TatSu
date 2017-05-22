.. include:: links.rst


Building Models
---------------

Naming elements in grammar rules makes the parser discard uninteresting
parts of the input, like punctuation, to produce an *Abstract Syntax
Tree* (`AST`_) that reflects the semantic structure of what was parsed.
But an `AST`_ doesn't carry information about the rule that generated
it, so navigating the trees may be difficult.

|TatSu| defines the ``tatsu.model.ModelBuilderSemantics`` semantics
class which helps construct object models from abtract syntax trees:

.. code:: python

    from tatsu.model import ModelBuilderSemantics

    parser = MyParser(semantics=ModelBuilderSemantics())

Then you add the desired node type as first parameter to each grammar
rule:

.. code:: ocaml

    addition::AddOperator = left:mulexpre '+' right:addition ;

``ModelBuilderSemantics`` will synthesize a ``class AddOperator(Node):``
class and use it to construct the node. The synthesized class will have
one attribute with the same name as the named elements in the rule.

You can also use `Python`_'s built-in types as node types, and
``ModelBuilderSemantics`` will do the right thing:

.. code:: ocaml

    integer::int = /[0-9]+/ ;

``ModelBuilderSemantics`` acts as any other semantics class, so its
default behavior can be overidden by defining a method to handle the
result of any particular grammar rule.

Walking Models
~~~~~~~~~~~~~~

The class ``tatsu.model.NodeWalker`` allows for the easy traversal
(*walk*) a model constructed with a ``ModelBuilderSemantics`` instance:

.. code:: python

    from tatsu.model import NodeWalker

    class MyNodeWalker(NodeWalker):

        def walk_AddOperator(self, node):
            left = self.walk(node.left)
            right = self.walk(node.right)

            print('ADDED', left, right)

    model = MyParser(semantics=ModelBuilderSemantics()).parse(input)

    walker = MyNodeWalker()
    walker.walk(model)

When a method with a name like ``walk_AddOperator()`` is defined, it
will be called when a node of that type is *walked*. The *pythonic*
version of the class name may also be used for the *walk* method:
``walk__add_operator()`` (note the double underscore).

If a *walk* method for a node class is not found, then a method for the
class's bases is searched, so it is possible to write *catch-all*
methods such as:

.. code:: python

    def walk_Node(self, node):
        print('Reached Node', node)

    def walk_str(self, s):
        return s

    def walk_object(self, o):
        raise Exception('Unexpected tyle %s walked', type(o).__name__)

Predeclared classes can be passed to ``ModelBuilderSemantics`` instances
through the ``types=`` parameter:

.. code:: python

    from mymodel import AddOperator, MulOperator

    semantics=ModelBuilderSemantics(types=[AddOperator, MulOperator])

``ModelBuilderSemantics`` assumes nothing about ``types=``, so any
constructor (a function, or a partial function) can be used.

Model Class Hierarchies
~~~~~~~~~~~~~~~~~~~~~~~

It is possible to specify a a base class for generated model nodes:

.. code:: ocaml

    additive
        =
        | addition
        | substraction
        ;

    addition::AddOperator::Operator
        =
        left:mulexpre op:'+' right:additive
        ;

    substraction::SubstractOperator::Operator
        =
        left:mulexpre op:'-' right:additive
        ;

|TatSu| will generate the base class if it's not already known.

Base classes can be used as the target class in *walkers*, and in *code
generators*:

.. code:: python

    class MyNodeWalker(NodeWalker):
        def walk_Operator(self, node):
            left = self.walk(node.left)
            right = self.walk(node.right)
            op = self.walk(node.op)

            print(type(node).__name__, op, left, right)


    class Operator(ModelRenderer):
        template = '{left} {op} {right}'

Templates and Translation
-------------------------

**note**
    As of |TatSu| 3.2.0, code generation is separated from grammar
    models through ``tatsu.codegen.CodeGenerator`` as to allow for code
    generation targets different from `Python`_. Still, the use of
    inline templates and ``rendering.Renderer`` hasn't changed. See the
    *regex* example for merged modeling and code generation.

|TatSu| doesn't impose a way to create translators with it, but it
exposes the facilities it uses to generate the `Python`_ source code for
parsers.

Translation in |TatSu| is *template-based*, but instead of defining or
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



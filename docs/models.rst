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


.. include:: links.rst


`Calc` Mini Tutorial
--------------------

|TatSu|  users have suggested that a simple calculator, like the one in the documentation for `PLY`_ would be useful.

Here it is.

The initial grammar
~~~~~~~~~~~~~~~~~~~

This is the original `PLY`_ grammar for arithmetic expressions:

.. code::

    expression : expression + term
               | expression - term
               | term

    term       : term * factor
               | term / factor
               | factor

    factor     : NUMBER
               | ( expression )

And this is the input expression for testing:

.. code:: python

    3 + 5 * ( 10 - 20 )

The Tatsu grammar
~~~~~~~~~~~~~~~~~

The first step is to convert the grammar to |TatSu| syntax and style,
add rules for lexical elements (``number`` in this case), add a
``start`` rule that checks for end of input, and a directive to name the
generated classes:

.. code::

    @@grammar::CALC


    start
        =
        expression $
        ;


    expression
        =
        | expression '+' term
        | expression '-' term
        | term
        ;


    term
        =
        | term '*' factor
        | term '/' factor
        | factor
        ;


    factor
        =
        | '(' expression ')'
        | number
        ;


    number
        =
        /\d+/
        ;


Add *cut* expressions
~~~~~~~~~~~~~~~~~~~~~

*Cut* expressions make a parser commit to a particular option after
certain tokens have been seen. They make parsing more efficient, because
other options are not tried. They also make error messages more precise,
because errors will be reported closest to the point of failure in the
input.

.. code::

    @@grammar::CALC


    start
        =
        expression $
        ;


    expression
        =
        | expression '+' ~ term
        | expression '-' ~ term
        | term
        ;


    term
        =
        | term '*' ~ factor
        | term '/' ~ factor
        | factor
        ;


    factor
        =
        | '(' ~ expression ')'
        | number
        ;


    number
        =
        /\d+/
        ;

Let's save the above grammar in a file called ``calc_cut.ebnf``.
We can now compile the grammar, and test the parser:

.. code:: python

    import json
    from pprint import pprint

    import tatsu


    def simple_parse():
        with open('calc_cut.ebnf') as f:
            grammar = f.read()

        parser = tatsu.compile(grammar)
        ast = parser.parse('3 + 5 * ( 10 - 20 )')

        print('# SIMPLE PARSE')
        print('# AST')
        pprint(ast, width=20, indent=4)

        print()

        print('# JSON')
        print(json.dumps(ast, indent=4))


    if __name__ == '__main__':
        simple_parse()

..

Save the above in ``calc.py``. This is the output:

.. code:: bash

    $ python calc.py

.. code:: python

    # SIMPLE PARSE
    # AST
    [   '3',
        '+',
        [   '5',
            '*',
            [   '(',
                [   '10',
                    '-',
                    '20'],
                ')']]]

    # JSON
    [
        "3",
        "+",
        [
            "5",
            "*",
            [
                "(",
                [
                    "10",
                    "-",
                    "20"
                ],
                ")"
            ]
        ]
    ]


Annotating the grammar
~~~~~~~~~~~~~~~~~~~~~~

Dealing with `AST`_\ s that are lists of lists leads to code that is
difficult to read, and error-prone. |TatSu| allows naming the elements
in a rule to produce more humanly-readable `AST`_\ s and to allow for
clearer semantics code. This is an annotated version of the grammar:

.. code::

    @@grammar::CALC


    start
        =
        expression $
        ;


    expression
        =
        | left:expression op:'+' ~ right:term
        | left:expression op:'-' ~ right:term
        | term
        ;


    term
        =
        | left:term op:'*' ~ right:factor
        | left:term '/' ~ right:factor
        | factor
        ;


    factor
        =
        | '(' ~ @:expression ')'
        | number
        ;


    number
        =
        /\d+/
        ;


Save the annotated grammar in ``calc_annotated.ebnf``, change
the grammar filename in ``calc.py`` and re-execute it to get the resulting AST:

.. code:: python

    # ANNOTATED AST
    {   'left': '3',
        'op': '+',
        'right': {   'left': '5',
                    'op': '*',
                    'right': {   'left': '10',
                                'op': '-',
                                'right': '20'}}}

Semantics
~~~~~~~~~~

Semantic actions for |TatSu| parsers are not specified in the grammar, but in a separate *semantics* class.

.. code:: python

    from pprint import pprint

    import tatsu
    from tatsu.ast import AST


    class CalcBasicSemantics:
        def number(self, ast):
            return int(ast)

        def term(self, ast):
            if not isinstance(ast, AST):
                return ast
            elif ast.op == '*':
                return ast.left * ast.right
            elif ast.op == '/':
                return ast.left / ast.right
            else:
                raise Exception('Unknown operator', ast.op)

        def expression(self, ast):
            if not isinstance(ast, AST):
                return ast
            elif ast.op == '+':
                return ast.left + ast.right
            elif ast.op == '-':
                return ast.left - ast.right
            else:
                raise Exception('Unknown operator', ast.op)


    def parse_with_basic_semantics():
        with open('calc_annotated.ebnf') as f:
            grammar = f.read()

        parser = tatsu.compile(grammar)
        ast = parser.parse(
            '3 + 5 * ( 10 - 20 )',
            semantics=CalcBasicSemantics()
        )

        print('# BASIC SEMANTICS RESULT')
        pprint(ast, width=20, indent=4)


    if __name__ == '__main__':
        parse_with_basic_semantics()

Save the above in ``calc_semantics.py`` and execute it with ``python calc_semantics.py``.
The result is:

.. code:: python

    # BASIC SEMANTICS RESULT
    -47


One rule per expression type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Having semantic actions determine what was parsed with ``isinstance()`` or querying the AST_ for operators is not very pythonic, nor object oriented, and it leads to code that's more difficult to maintain. It's preferable to have one rule per *expression kind*, something that will be necessary if we want to build object models to use *walkers* and *code generation*.


.. code::

    @@grammar::CALC


    start
        =
        expression $
        ;


    expression
        =
        | addition
        | subtraction
        | term
        ;


    addition
        =
        left:expression op:'+' ~ right:term
        ;

    subtraction
        =
        left:expression op:'-' ~ right:term
        ;


    term
        =
        | multiplication
        | division
        | factor
        ;


    multiplication
        =
        left:term op:'*' ~ right:factor
        ;


    division
        =
        left:term '/' ~ right:factor
        ;


    factor
        =
        | '(' ~ @:expression ')'
        | number
        ;


    number
        =
        /\d+/
        ;

Save the above in ``calc_refactored.ebnf``.

.. code:: python

    from pprint import pprint

    import tatsu


    class CalcSemantics:
        def number(self, ast):
            return int(ast)

        def addition(self, ast):
            return ast.left + ast.right

        def subtraction(self, ast):
            return ast.left - ast.right

        def multiplication(self, ast):
            return ast.left * ast.right

        def division(self, ast):
            return ast.left / ast.right


    def parse_refactored():
        with open('calc_refactored.ebnf') as f:
            grammar = f.read()

        parser = tatsu.compile(grammar)
        ast = parser.parse(
            '3 + 5 * ( 10 - 20 )',
            semantics=CalcSemantics()
        )

        print('# REFACTORED SEMANTICS RESULT')
        pprint(ast, width=20, indent=4)
        print()


    if __name__ == '__main__':
        parse_refactored()


The semantics implementation is simpler, and the results are the same:

.. code:: python

    # REFACTORED SEMANTICS RESULT
    -47


Object models
~~~~~~~~~~~~~

Binding semantics to grammar rules is powerful and versatile, but this
approach risks tying the semantics to the *parsing process*, rather than
to the parsed *objects*.

That is not a problem for simple languages, like the arithmetic expression language in this tutorial. But as the complexity of the parsed language increases, the number of grammar rules quickly becomes larger than the types of objects parsed.

|TatSu| can create typed object models directly from the parsing process which can be navigated (*walked*) and transformed (with *code generation*) in later passes.

The first step to create an object model is to annotate the rule names with the desired class names:

.. code::

    @@grammar::Calc


    start
        =
        expression $
        ;


    expression
        =
        | addition
        | subtraction
        | term
        ;


    addition::Add
        =
        left:term op:'+' ~ right:expression
        ;


    subtraction::Subtract
        =
        left:term op:'-' ~ right:expression
        ;


    term
        =
        | multiplication
        | division
        | factor
        ;


    multiplication::Multiply
        =
        left:factor op:'*' ~ right:term
        ;


    division::Divide
        =
        left:factor '/' ~ right:term
        ;


    factor
        =
        | subexpression
        | number
        ;


    subexpression
        =
        '(' ~ @:expression ')'
        ;


    number::int
        =
        /\d+/
        ;

Save the grammar in a file name ``calc_model.ebnf``.

The ``tatsu.objectmodel.Node`` descendants are synthetized at runtime using ``tatsu.semantics.ModelBuilderSemantics``.

This is how the model looks like when generated with the ``tatsu.to_python_model()``
function or from the command line with ``tatsu --object-model calc_model.ebnf -G calc_semantics_model.py``:

.. code:: python

    from tatsu.objectmodel import Node
    from tatsu.semantics import ModelBuilderSemantics


    class ModelBase(Node):
        pass


    class CalcModelBuilderSemantics(ModelBuilderSemantics):
        def __init__(self, context=None, types=None):
            types = [
                t for t in globals().values()
                if type(t) is type and issubclass(t, ModelBase)
            ] + (types or [])
            super(CalcModelBuilderSemantics, self).__init__(context=context, types=types)


    class Add(ModelBase):
        left = None
        op = None
        right = None


    class Subtract(ModelBase):
        left = None
        op = None
        right = None


    class Multiply(ModelBase):
        left = None
        op = None
        right = None


    class Divide(ModelBase):
        left = None
        right = None

The model that results from a parse can be printed, and walked:

.. code:: python

    import tatsu
    from tatsu.walkers import NodeWalker


    class CalcWalker(NodeWalker):
        def walk_object(self, node):
            return node

        def walk__add(self, node):
            return self.walk(node.left) + self.walk(node.right)

        def walk__subtract(self, node):
            return self.walk(node.left) - self.walk(node.right)

        def walk__multiply(self, node):
            return self.walk(node.left) * self.walk(node.right)

        def walk__divide(self, node):
            return self.walk(node.left) / self.walk(node.right)


    def parse_and_walk_model():
        with open('calc_model.ebnf') as f:
            grammar = f.read()

        parser = tatsu.compile(grammar, asmodel=True)
        model = parser.parse('3 + 5 * ( 10 - 20 )')

        print('# WALKER RESULT IS:')
        print(CalcWalker().walk(model))
        print()


    if __name__ == '__main__':
        parse_and_walk_model()

Save the above program in ``calc_model.py`` and execute it to get this result:

.. code:: python

    # WALKER RESULT IS:
    -47


Code Generation
~~~~~~~~~~~~~~~

Translation is one of the most common tasks in language processing.
Analysis often sumarizes the parsed input, and *walkers* are good for that.
In translation, the output can often be as verbose as the input, so a systematic approach that avoids bookkeeping as much as possible is convenient.

|TatSu| provides support for template-based code generation (translation) in the ``tatsu.codegen`` module.
Code generation works by defining a translation class for each class in the model specified by the grammar.

Adjust our previous ``calc_model.ebnf`` grammar and annotate the *number* rule
like so:

.. code::

    number::Number
        =
        value:/\d+/
        ;

The following code generator translates input expressions to the postfix instructions of a stack-based processor:

.. code:: python

    import sys

    from tatsu.codegen import ModelRenderer
    from tatsu.codegen import CodeGenerator

    THIS_MODULE =  sys.modules[__name__]


    class PostfixCodeGenerator(CodeGenerator):
        def __init__(self):
            super().__init__(modules=[THIS_MODULE])


    class Number(ModelRenderer):
        template = '''\
        PUSH {value}'''


    class Add(ModelRenderer):
        template = '''\
        {left}
        {right}
        ADD'''


    class Subtract(ModelRenderer):
        template = '''\
        {left}
        {right}
        SUB'''


    class Multiply(ModelRenderer):
        template = '''\
        {left}
        {right}
        MUL'''


    class Divide(ModelRenderer):
        template = '''\
        {left}
        {right}
        DIV'''

Save the above in ``codegen.py``.
The code generator can be used as follows:

.. code:: python

    from codegen import PostfixCodeGenerator


    def parse_and_translate():
        with open('calc_model.ebnf') as f:
            grammar = f.read()

        parser = tatsu.compile(grammar, asmodel=True)
        model = parser.parse('3 + 5 * ( 10 - 20 )')

        postfix = PostfixCodeGenerator().render(model)

        print('# TRANSLATED TO POSTFIX')
        print(postfix)

    if __name__ == '__main__':
        parse_and_translate()

Save the above program in ``calc_translate.py`` and execute it to get this result:

.. code:: python

    # TRANSLATED TO POSTFIX
    PUSH 3
    PUSH 5
    PUSH 10
    PUSH 20
    SUB
    MUL
    ADD

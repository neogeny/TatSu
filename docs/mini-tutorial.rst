.. include:: links.rst


`Calc` Mini Tutorial
--------------------

|TatSu|  users have suggested that a simple calculator, like the one in the documentation for `PLY`_ would be useful.

Here it is.

The initial grammar
~~~~~~~~~~~~~~~~~~~

This is the original `PLY`_ grammar for arithmetic expressions:

.. code:: ocaml

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

.. code:: ocaml

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

.. code:: ocaml

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

We can now compile the grammar, and test the parser:

.. code:: python

    import json
    from codecs import open
    from pprint import pprint

    import tatsu


    def simple_parse():
        grammar = open('grammars/calc_cut.ebnf').read()

        parser = tatsu.compile(grammar)
        ast = parser.parse('3 + 5 * ( 10 - 20 )')

        print('# SIMPLE PARSE')
        print('# AST')
        pprint(ast, width=20, indent=4)

        print()

        print('# JSON')
        print(json.dumps(ast, indent=4))


    def main():
        simple_parse()


    if __name__ == '__main__':
        main()

..

This is the output:

.. code:: bash

    $ PYTHONPATH=../.. python calc.py

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

.. code:: ocaml

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


This is the resulting AST:

.. code:: python

    # ANNOTATED AST
    {   'left': '3',
        'op': '+',
        'right': {   'left': '5',
                    'op': '*',
                    'right': {   'left': '10',
                                'op': '-',
                                'right': '20'}}}

Semmantics
~~~~~~~~~~

Semantics for |TatSu| parsers are not specified in the grammar, but in a separate *semantics* class.

.. code:: python

    from tatsu.ast import AST

    class CalcBasicSemantics(object):
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
        grammar = open('grammars/calc_annotated.ebnf').read()

        parser = tatsu.compile(grammar)
        ast = parser.parse(
            '3 + 5 * ( 10 - 20 )',
            parse_with_basic_semantics=CalcBasicSemantics()
        )

        print('# BASIC SEMANTICS RESULT')
        pprint(ast, width=20, indent=4)


The result is:

.. code:: python

    # BASIC SEMANTICS RESULT
    -47


One rule per expression type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Having semantic actions determine what was parsed with ``isinstance()`` or querying the AST_ for operators is not very pythonic, nor object oriented, and it leads to code that's more difficult to maintain. It's preferable to have one rule per *expression kind*, something that will be necessary if we want to build object models to use *walkers* and *code generation*.


.. code:: ocaml

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


.. code:: python


    class CalcSemantics(object):
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


    def parse_factored():
        grammar = open('grammars/calc_factored.ebnf').read()

        parser = tatsu.compile(grammar)
        ast = parser.parse(
            '3 + 5 * ( 10 - 20 )',
            semantics=CalcSemantics()
        )

        print('# FACTORED SEMANTICS RESULT')
        pprint(ast, width=20, indent=4)
        print()


The semantics implementation is simpler, and the results are the same:

.. code:: python

    # FACTORED SEMANTICS RESULT
    -47


Object models
~~~~~~~~~~~~~

Binding semantics to grammar rules is powerful and versatile, but this
approach risks tying the semantics to the *parsing process*, rather than
to the *objects* that are parsed.

That is not a problem for simple languages, like the arithmetic expression language in this tutorial. But as the complexity of the parsed language increases, the number of grammar rules quickly becomes larger than the types of objects parsed.

|TatSu| provides for the creation of typed object models directly from the parsing process, and for the navigation (*walking*) and transformation (like *code generation*) of those models in later passes.

The first step in the creation of an object model is to annotate the grammar rule names with the desired class names for the objects parsed:

.. code:: ocaml

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


The ``tatsu.objectmodel.Node`` descendants are synthetized at runtime using ``tatsu.semantics.ModelBuilderSemantics``.

This is how the model looks like when generated with the ``tatsu.to_python_model()`` function:

.. code:: python

    from tatsu.objectmodel import Node
    from tatsu.semantics import ModelBuilderSemantics


    class CalcModelBuilderSemantics(ModelBuilderSemantics):
        def __init__(self):
            types = [
                t for t in globals().values()
                if type(t) is type and issubclass(t, ModelBase)
            ]
            super(CalcModelBuilderSemantics, self).__init__(types=types)


    class ModelBase(Node):
        pass


    class Add(ModelBase):
        def __init__(self,
                     left=None,
                     op=None,
                     right=None,
                     **_kwargs_):
            super(Add, self).__init__(
                left=left,
                op=op,
                right=right,
                **_kwargs_
            )


    class Subtract(ModelBase):
        def __init__(self,
                     left=None,
                     op=None,
                     right=None,
                     **_kwargs_):
            super(Subtract, self).__init__(
                left=left,
                op=op,
                right=right,
                **_kwargs_
            )


    class Multiply(ModelBase):
        def __init__(self,
                     left=None,
                     op=None,
                     right=None,
                     **_kwargs_):
            super(Multiply, self).__init__(
                left=left,
                op=op,
                right=right,
                **_kwargs_
            )


    class Divide(ModelBase):
        def __init__(self,
                     left=None,
                     right=None,
                     **_kwargs_):
            super(Divide, self).__init__(
                left=left,
                right=right,
                **_kwargs_
            )

The model that results from a parse can be printed, and walked:

.. code:: python

    from tatsu.walkers import NodeWalker
    from tatsu.semantics import ModelBuilderSemantics


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
        grammar = open('grammars/calc_model.ebnf').read()

        parser = tatsu.compile(grammar, semantics=ModelBuilderSemantics())
        model = parser.parse('3 + 5 * ( 10 - 20 )')

        print('# WALKER RESULT IS:')
        print(CalcWalker().walk(model))
        print()

The above program produces this result:

.. code:: python

    # WALKER RESULT IS:
    -47


Code Generation
~~~~~~~~~~~~~~~

Translation is one of the most common tasks in language processing.  Analysis often sumarizes the parsed input, and *walkers* are good for that. In translation, the output can often be as verbose as the input, so a systematic approach that avoids bookkeeping as much as possible is convenient.

|TatSu| provides support for template-based code generation (translation) in the ``tatsu.codegen`` module. Code generation works defining a translation class for each class in the model specified by the grammar.

The following code generator translates input expressions to the postfix instructions of a stack-based processor:

.. code:: python

    from tatsu.codegen import ModelRenderer
    from tatsu.codegen import CodeGenerator

    THIS_MODULE =  sys.modules[__name__]


    class PostfixCodeGenerator(CodeGenerator):
        def __init__(self):
            super(PostfixCodeGenerator, self).__init__(modules=[THIS_MODULE])


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

The code generator can be used thus:

.. code:: python

    from codegen import PostfixCodeGenerator


    def parse_and_translate():
        grammar = open('grammars/calc_model.ebnf').read()

        parser = tatsu.compile(grammar, semantics=ModelBuilderSemantics())
        model = parser.parse('3 + 5 * ( 10 - 20 )')

        postfix = PostfixCodeGenerator().render(model)

        print('# TRANSLATED TO POSTFIX')
        print(postfix)


Which results in:

.. code:: python

    # TRANSLATED TO POSTFIX
    PUSH 3
    PUSH 5
    PUSH 10
    PUSH 20
    SUB
    MUL
    ADD

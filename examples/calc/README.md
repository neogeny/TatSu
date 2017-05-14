# CALC - Expression parser and calculator

[TOC]

**Tatsu** has lacked a step-by-step example for a long time, and users have suggested that a simple calculator, like the one in the documentation for [PLY] would be useful. Well, here it is.

[AST]: https://en.wikipedia.org/wiki/Abstract_syntax_tree
[PEG]: https://en.wikipedia.org/wiki/Parsing_expression_grammar
[PLY]: http://www.dabeaz.com/ply/ply.html#ply_nn22

## The initial grammar

This is the original [PLY] grammar for arithmetic expressions:

```ebnf
expression : expression + term
           | expression - term
           | term

term       : term * factor
           | term / factor
           | factor

factor     : NUMBER
           | ( expression )
```

And this is the input expression for testing:

```python
3 + 5 * ( 10 - 20 )
```

## The Tatsu grammar

The first step is to convert the grammar to **Tatsu** syntax and style, add rules for lexical elements (``NUMBER`` in this case), and add a ``start`` rule that checks for end of input, and a directive to name the generated classes:

```ocaml
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
```

## Remove left recursion

Left recursion in [PEG] grammars is still a research subject, and existing left-recursion algorithms cannot handle all cases that are intuitivelly correct. It's best to stick to the [PEG] definition, and remove left recursion:

```ocaml
@@grammar::CALC


start
    =
    expression $
    ;


expression
    =
    | term '+' expression
    | term '-' expression
    | term
    ;


term
    =
    | factor '*' term
    | factor '/' term
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
```

## Add _cut_ expressions

_Cut_ expressions make a parser commit to a particular option after certain tokens have been seen.  They make parsing more efficient, because other options are not tried. They also make error messages more precise, because errors will be reported closest to the point of failure in the input.


```ocaml
@@grammar::CALC


start
    =
    expression $
    ;


expression
    =
    | term '+' ~ expression
    | term '-' ~ expression
    | term
    ;


term
    =
    | factor '*' ~ term
    | factor '/' ~ term
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
```

We can now compile the grammar, and test the parser:

```bash
$ PYTHONPATH=../../.. python -m tatsu -o calc_parser.py calc.ebnf
$ PYTHONPATH=../../.. python calc_parser.py ../input.txt
AST:
[u'3', u'+', [u'5', u'*', [u'(', [u'10', u'-', u'20'], u')']]]

JSON:
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
```

The default output for the generated parser consists of the ``__str__`` and [JSON] representations of the [AST] resulting from the parse.

## Adding semantics

Semantics for **Tatsu** parsers are not specified in the grammar, but in a separate _semantics_ class.

```python
from __future__ import print_function
import sys
from calc_parser import CalcParser


class CalcSemantics(object):
    def number(self, ast):
       return int(ast)

    def factor(self, ast):
       if not isinstance(ast, list):
           return ast
       else:
           return ast[1]

    def term(self, ast):
        if not isinstance(ast, list):
            return ast
        elif ast[1] == '*':
            return ast[0] * ast[2]
        elif ast[1] == '/':
            return ast[0] / ast[2]
        else:
            raise Exception('Unknown operator', ast[1])

    def expression(self, ast):
        if not isinstance(ast, list):
            return ast
        elif ast[1] == '+':
            return ast[0] + ast[2]
        elif ast[1] == '-':
            return ast[0] - ast[2]
        else:
            raise Exception('Unknown operator', ast[1])


def calc(text):
    parser = CalcParser(semantics=CalcSemantics())
    return parser.parse(text)

if __name__ == '__main__':
    text = open(sys.argv[1]).read()
    result = calc(text)
    print(text.strip(), '=', result)
```

```bash
$ PYTHONPATH=../../.. python -m tatsu -o calc_parser.py calc.ebnf
------------------------------------------------------------------------
          50  lines in grammar
           5  rules in grammar
          41  nodes in AST
$ PYTHONPATH=../../.. python calc.py ../input.txt
3 + 5 * ( 10 - 20 ) = -47
```

## Annotating the grammar

Dealing with [AST]s that are lists of lists leads to code that is difficult to read, and
error-prone. **Tatsu** allows naming the elements in a rule to produce more humanly-readable [AST]s and to allow for clearer semantics code. This is an annotated version of the grammar:

```ocaml
@@grammar::Calc


start
    =
    expression $
    ;


expression
    =
    | left:term op:'+' ~ right:expression
    | left:term op:'-' ~ right:expression
    | term:term
    ;


term
    =
    | left:factor op:'*' ~ right:term
    | left:factor '/' ~ right:term
    | factor:factor
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
```

And these are the corresponding semantics:

```python
class CalcSemantics(object):
    def number(self, ast):
       return int(ast)

    def term(self, ast):
        if ast.factor:
            return ast.factor
        elif ast.op == '*':
            return ast.left * ast.right
        elif ast.op == '/':
            return ast.left / ast.right
        else:
            raise Exception('Unknown operator', ast.op)

    def expression(self, ast):
        if ast.term:
            return ast.term
        elif ast.op == '+':
            return ast.left + ast.right
        elif ast.op == '-':
            return ast.left - ast.right
        else:
            raise Exception('Unknown operator', ast.op)
```

The result is the same:

```bash
$ PYTHONPATH=../../.. python calc.py ../input.txt
3 + 5 * ( 10 - 20 ) = -47
```

But the [AST] is not too satisfactory:

```json
{
  "left": {
    "factor": "3",
    "left": null,
    "op": null,
    "right": null
  },
  "op": "+",
  "right": {
    "term": {
      "left": "5",
      "op": "*",
      "right": {
        "factor": {
          "left": {
            "factor": "10",
            "left": null,
            "op": null,
            "right": null
          },
          "op": "-",
          "right": {
            "term": {
              "factor": "20",
              "left": null,
              "op": null,
              "right": null
            },
            "left": null,
            "op": null,
            "right": null
          },
          "term": null
        },
        "left": null,
        "op": null,
        "right": null
      },
      "factor": null
    },
    "left": null,
    "op": null,
    "right": null
  },
  "term": null
}
```

## One rule per expression type

Having semantic actions determine what was parsed with ``isinstance()`` or querying the [AST] for operators is not pythonic, nor object oriented, and it leads to code that's more difficult to maintain. It's preferable to have one rule per _expression kind_, something that will be necessary if we want to build object models to use _walkers_ and _code generation_.


```ocaml
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


addition
    =
    left:term op:'+' ~ right:expression
    ;


subtraction
    =
    left:term op:'-' ~ right:expression
    ;


term
    =
    | multiplication
    | division
    | factor
    ;


multiplication
    =
    left:factor op:'*' ~ right:term
    ;


division
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


number
    =
    /\d+/
    ;
```


The corresponding semantics are:

```python
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
```


## Object models

Binding semantics to grammar rules is powerful and versatile, but this approach risks tying the semantics to the *parsing process*, rather than to *the objects* that are parsed.  That is not a problem for simple languages, like the arithmetic expression language in this tutorial. But as the complexity of the parsed language increases, the number of grammar rules quickly becomes larger than the types of objects parsed. **Tatsu** provides for the creation of typed object models directly from the parsing process, and for the navigation (_walking_) and transformation (_code generation_) of those models in later passes.

The first step in the creation of an object model as [AST] is to annotate the grammar with the desired class names for the objects parsed:

```ocaml
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


number::Number
    =
    value:/\d+/
    ;
```

The object model classes can be generated using the `-g` option in `tatsu`:

```bash
$ PYTHONPATH=../../.. python -m tatsu -g -o calc_model.py calc.ebnf
```

If the model classes are not generated, they can be synthetized at runtime using ``tatsu.semantics.ModelBuilderSemantics``. The class definitions for arithmetic expressions look like this:


```python
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
```

The model that results from a parse can be printed, and walked:

```python
import sys
from tatsu.walkers import NodeWalker
from calc_parser import CalcParser
from calc_model import CalcModelBuilderSemantics


class CalcWalker(NodeWalker):
    def walk_object(self, node):
        return node

    def walk_Add(self, node):
        return self.walk(node.left) + self.walk(node.right)

    def walk_Subtract(self, node):
        return self.walk(node.left) - self.walk(node.right)

    def walk_Multiply(self, node):
        return self.walk(node.left) * self.walk(node.right)

    def walk_Divide(self, node):
        return self.walk(node.left) / self.walk(node.right)


def calc(text):
    parser = CalcParser(semantics=CalcModelBuilderSemantics())
    return parser.parse(text)


if __name__ == '__main__':
    text = open(sys.argv[1]).read()
    model = calc(text)
    print(model)
    print(text.strip(), '=', CalcWalker().walk(model))
```

The above program produces this result:

```bash
{
  "__class__": "Add",
  "right": {
    "__class__": "Multiply",
    "right": {
      "__class__": "Subtract",
      "right": 20,
      "op": "-",
      "left": 10
    },
    "op": "*",
    "left": 5
  },
  "op": "+",
  "left": 3
}
3 + 5 * ( 10 - 20 ) = -47
```


## Left Recursion and Left Associativity


## Code Generation

Translation is one of the most common tasks in language processing. Analysis often sumarizes the parsed input, and _walkers_ are good for that. In translation, the output can often be as verbose as the input, so a systematic approach that avoids bookkeeping as much as possible. **Tatsu** provides support for template-based code generation (translation) in the ``tatsu.codegen`` module.  Code generation works defining a translation class for each class in the model specified by the grammar.

The following code generator translates input expressions to the postfix instructions of a stack-based processor:

```python
import sys
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


print(PostfixCodeGenerator().render(model))
```

Which results in:

```bash
PUSH 3
PUSH 5
PUSH 10
PUSH 20
SUB
MUL
ADD
```



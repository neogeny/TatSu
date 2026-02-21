.. Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
.. SPDX-License-Identifier: BSD-4-Clause

.. include:: links.rst

Using the Tool
--------------

As a Library
~~~~~~~~~~~~

|TatSu| can be used as a library, much like `Python`_'s ``re``, by embedding grammars as strings and generating grammar models instead of generating Python_ code.

-   ``tatsu.compile(grammar, name=None, **kwargs)``

    Compiles the grammar and generates a *model* that can subsequently be used for parsing input with.

-   ``tatsu.parse(grammar, input, start=None, **kwargs)``

    Compiles the grammar and parses the given input producing an AST_ as result.
    The result is equivalent to calling::

        model = compile(grammar)
        ast = model.parse(input)

    Compiled grammars are cached for efficiency.

-   ``tatsu.to_python_sourcecode(grammar, name=None, filename=None, **kwargs)``

    Compiles the grammar to the `Python`_ source code that implements the
    parser.

-   ``to_python_model(grammar, name=None, filename=None, **kwargs)``

    Compiles the grammar and generates the `Python`_ source code that
    implements the object model defined by rule annotations.

This is an example of how to use **TatSu** as a library:

.. code:: python

    GRAMMAR = '''
        @@grammar::Calc

        start = expression $ ;

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
            | '(' ~ @:expression ')'
            | number
            ;

        number = /\d+/ ;
    '''


    def main():
        import pprint
        import json
        from tatsu import parse
        from tatsu.util import asjson

        ast = parse(GRAMMAR, '3 + 5 * ( 10 - 20 )')
        print('PPRINT')
        pprint.pprint(ast, indent=2, width=20)
        print()

        print('JSON')
        print(json.dumps(asjson(ast), indent=2))
        print()


    if __name__ == '__main__':
        main()

And this is the output:

.. code:: bash

    PPRINT
    [ '3',
      '+',
      [ '5',
        '*',
        [ '10',
          '-',
          '20']]]

    JSON
    [
      "3",
      "+",
      [
        "5",
        "*",
        [
          "10",
          "-",
          "20"
        ]
      ]
    ]


Compiling grammars to Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**TatSu** can be run from the command line:

.. code:: bash

    $ python -m tatsu

Or:

.. code:: bash

    $ scripts/tatsu

Or just:

.. code:: bash

    $ tatsu

if **TatSu** was installed using *easy\_install* or *pip*.

The *-h* and *--help* parameters provide full usage information:

.. code:: bash

    $ tatsu --help
    usage: tatsu [--generate-parser | --draw | --railroad | --object-model |
                 --pretty | --pretty-lean] [--color] [--trace] [--left-recursion]
                 [--name NAME] [--nameguard] [--outfile FILE]
                 [--object-model-outfile FILE] [--whitespace CHARACTERS]
                 [--base-type CLASSPATH] [--help] [--version]
                 GRAMMAR

    竜TatSu takes a grammar in extended EBNF as input, and outputs a memoizing
    PEG/Packrat parser in Python.

    positional arguments:
      GRAMMAR               the filename of the TatSu grammar to parse

    options:
      --generate-parser     generate parser code from the grammar (default)
      --draw, -d            generate a diagram of the grammar (.svg, .png, .jpeg,
                            .dot, ... / requres --outfile)
      --railroad, -r        output a railroad diagram of the grammar in ASCII/Text
                            Art
      --object-model, -g    generate object model from the class names given as
                            rule arguments
      --pretty, -p          generate a prettified version of the input grammar
      --pretty-lean         like --pretty, but without name: or ::Parameter
                            annotations

    parse-time options:
      --color, -c           use color in traces (requires the colorama library)
      --trace, -t           produce verbose parsing output

    generation options:
      --left-recursion, -l  turns left-recursion support on
      --name, -m NAME       Name for the grammar (defaults to GRAMMAR base name)
      --nameguard, -n       allow tokens that are prefixes of others
      --outfile, --output, -o FILE
                            output file (default is stdout)
      --object-model-outfile, -G FILE
                            generate object model and save to FILE
      --whitespace, -w CHARACTERS
                            characters to skip during parsing (use "" to disable)
      --base-type CLASSPATH
                            class to use as base type for the object model, for
                            example "mymodule.MyNode"

    common options:
      --help, -h            show this help message and exit
      --version, -V         provide version information and exit
    $


The Generated Parsers
~~~~~~~~~~~~~~~~~~~~~

A **TatSu** generated parser consists of the following classes:

-  A ``MyLanguageBuffer`` class derived from ``tatsu.buffering.Buffer``
   that handles the grammar definitions for *whitespace*, *comments*,
   and *case significance*.
-  A ``MyLanguageParser`` class derived from ``tatsu.parsing.Parser``
   which uses a ``MyLanguageBuffer`` for traversing input text, and
   implements the parser using one method for each grammar rule:

.. code:: python

            def _somerulename_(self):
                ...

-  A ``MyLanguageSemantics`` class with one semantic method per grammar
   rule. Each method receives as its single parameter the `Abstract
   Syntax Tree`_ (`AST`_) built from the rule invocation:

.. code:: python

            def somerulename(self, ast):
                return ast

-  A ``if __name__ == '__main__':`` definition, so the generated parser
   can be executed as a `Python`_ script.

The methods in the delegate class return the same `AST`_ received as
parameter. Custom semantic classes can override the methods to have
them return anything (for example, a `Semantic Graph`_). The semantics
class can be used as a template for the final semantics implementation,
which can omit methods for the rules that do not need semantic
treatment.

If present, a ``_default()`` method will be called in the semantics
class when no method matched the rule name:

.. code:: python

    def _default(self, ast):
        ...
        return ast

If present, a ``_postproc()`` method will be called in the semantics
class after each rule (including the semantics) is processed. This
method will receive the current parsing context as parameter:

.. code:: python

    def _postproc(self, context, ast):
        ...

Using the Generated Parser
~~~~~~~~~~~~~~~~~~~~~~~~~~

To use the generated parser, just subclass the base or the abstract
parser. Then create an instance of it. Then invoke its ``parse()`` method,
passing the grammar to parse and the starting rule's name as parameters:

.. code:: python

    from tatsu.util import asjson
    from myparser import MyParser

    parser = MyParser()
    ast = parser.parse('text to parse', start='start')
    print(ast)
    print(json.dumps(asjson(ast), indent=2))

The generated parsers' constructors accept named arguments to specify
whitespace characters, the regular expression for comments, case
sensitivity, verbosity, and more (see below).

To add semantic actions, just pass a semantic delegate to the parse
method:

.. code:: python

    model = parser.parse(text, start='start', semantics=MySemantics())

If special lexical treatment is required (as in *80 column* languages),
then a descendant of ``tatsu.tokenizing.Tokenizer`` can be passed instead of
the text:

.. code:: python

    class MySpecialTokenizer(Tokenizer):
        ...

    tokenizer = MySpecialTokenizer(text)
    model = parser.parse(tokenizer, start='start', semantics=MySemantics())

The generated parser's module can also be invoked as a script:

.. code:: bash

    $ python myparser.py inputfile startrule

As a script, the generated parser's module accepts some options:

.. code:: bash

    $ python myparser.py -h
    usage: myparser.py [-h] [-c] [-l] [-n] [-t] [-w WHITESPACE] FILE [STARTRULE]

    Simple parser for DBD.

    positional arguments:
        FILE                  the input file to parse
        STARTRULE             the start rule for parsing

    optional arguments:
        -h, --help            show this help message and exit
        -c, --color           use color in traces (requires the colorama library)
        -l, --list            list all rules and exit
        -n, --no-nameguard    disable the 'nameguard' feature
        -t, --trace           output trace information
        -w WHITESPACE, --whitespace WHITESPACE
                            whitespace specification

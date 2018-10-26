[![license](https://img.shields.io/badge/license-BSD-blue.svg)](https://raw.githubusercontent.com/neogeny/tatsu/master/LICENSE.txt) [![pyversions](https://img.shields.io/pypi/pyversions/tatsu.svg)](https://pypi.python.org/pypi/tatsu) [![fury](https://badge.fury.io/py/tatsu.svg)](https://badge.fury.io/py/tatsu) [![circleci](https://circleci.com/gh/neogeny/TatSu.svg?style=shield)](https://circleci.com/gh/neogeny/TatSu) [![travis](https://secure.travis-ci.org/neogeny/TatSu.svg)](http://travis-ci.org/neogeny/TatSu) [![docs](https://readthedocs.org/projects/tatsu/badge/?version=stable)](http://tatsu.readthedocs.io/en/stable/) [![landscape](https://landscape.io/github/apalala/TatSu/master/landscape.png)](https://landscape.io/github/apalala/TatSu/master)

> *At least for the people who send me mail about a new language that they're designing, the general advice is: do it to learn about how to write a compiler. Don't have any expectations that anyone will use it, unless you hook up with some sort of organization in a position to push it hard. It's a lottery, and some can buy a lot of the tickets. There are plenty of beautiful languages (more beautiful than C) that didn't catch on. But someone does win the lottery, and doing a language at least teaches you something.*
>
> [Dennis Ritchie](http://en.wikipedia.org/wiki/Dennis_Ritchie) (1941-2011) Creator of the [C](http://en.wikipedia.org/wiki/C_language) programming language and of [Unix](http://en.wikipedia.org/wiki/Unix)

竜 **TatSu**
============

竜 **TatSu** (the successor to [Grako](https://bitbucket.org/neogeny/grako/)) is a tool that takes grammars in a variation of [EBNF](http://en.wikipedia.org/wiki/Ebnf) as input, and outputs [memoizing](http://en.wikipedia.org/wiki/Memoization) ([Packrat](http://bford.info/packrat/)) [PEG](http://en.wikipedia.org/wiki/Parsing_expression_grammar) parsers in [Python](http://python.org).

竜 **TatSu** can compile a grammar stored in a string into a `tatsu.grammars.Grammar` object that can be used to parse any given input, much like the [re](https://docs.python.org/3.7/library/re.html) module does with regular expressions, or it can generate a [Python](http://python.org) module that implements the parser.

竜 **TatSu** has experimental support for [left-recursive](https://en.wikipedia.org/wiki/Left_recursion) rules in [PEG](http://en.wikipedia.org/wiki/Parsing_expression_grammar) grammars using the [algorithm](http://norswap.com/pubs/sle2016.pdf) by *Laurent* and *Mens*. The generated [AST](http://en.wikipedia.org/wiki/Abstract_syntax_tree) has the expected left associativity.

Installation
------------

``` {.sourceCode .bash}
$ pip install TatSu
```

Using the Tool
--------------

竜 **TatSu** can be used as a library, much like [Python](http://python.org)'s `re`, by embedding grammars as strings and generating grammar models instead of generating [Python](http://python.org) code.

-   `tatsu.compile(grammar, name=None, **kwargs)`

    Compiles the grammar and generates a *model* that can subsequently be used for parsing input with.

-   `tatsu.parse(grammar, input, **kwargs)`

    Compiles the grammar and parses the given input producing an [AST](http://en.wikipedia.org/wiki/Abstract_syntax_tree) as result. The result is equivalent to calling:

        model = compile(grammar)
        ast = model.parse(input)

    Compiled grammars are cached for efficiency.

-   `tatsu.to_python_sourcecode(grammar, name=None, filename=None, **kwargs)`

    Compiles the grammar to the [Python](http://python.org) sourcecode that implements the parser.

This is an example of how to use 竜 **TatSu** as a library:

``` {.sourceCode .python}
GRAMMAR = '''
    @@grammar::CALC


    start = expression $ ;


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


    number = /\d+/ ;
'''


if __name__ == '__main__':
    import pprint
    import json
    from tatsu import parse
    from tatsu.util import asjson

    ast = parse(GRAMMAR, '3 + 5 * ( 10 - 20 )')
    print('# PPRINT')
    pprint.pprint(ast, indent=2, width=20)
    print()

    print('# JSON')
    print(json.dumps(asjson(ast), indent=2))
    print()
```

竜 **TatSu** will use the first rule defined in the grammar as the *start* rule.

This is the output:

``` {.sourceCode .console}
# PPRINT
[ '3',
  '+',
  [ '5',
    '*',
    [ '10',
      '-',
      '20']]]

# JSON
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
```

License
-------

You may use 竜 **TatSu** under the terms of the [BSD](http://en.wikipedia.org/wiki/BSD_licenses#2-clause_license_.28.22Simplified_BSD_License.22_or_.22FreeBSD_License.22.29)-style license described in the enclosed [LICENSE.txt](LICENSE.txt) file. *If your project requires different licensing* please [email](mailto:apalala@gmail.com).

Documentation
-------------

For a detailed explanation of what 竜 **TatSu** is capable of, please see the [documentation](http://tatsu.readthedocs.io/).

Questions?
----------

For general Q&A, please use the [\[tatsu\]](https://stackoverflow.com/tags/tatsu/info) tag on [StackOverflow](http://stackoverflow.com/tags/tatsu/info).

Changes
-------

See the [CHANGELOG](https://github.com/neogeny/TatSu/releases) for details.

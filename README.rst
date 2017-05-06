|fury| |license| |pyversions| |travis| |landscape|

    *At least for the people who send me mail about a new language that
    they're designing, the general advice is: do it to learn about how
    to write a compiler. Don't have any expectations that anyone will
    use it, unless you hook up with some sort of organization in a
    position to push it hard. It's a lottery, and some can buy a lot of
    the tickets. There are plenty of beautiful languages (more beautiful
    than C) that didn't catch on. But someone does win the lottery, and
    doing a language at least teaches you something.*

    `Dennis Ritchie`_ (1941-2011) *Creator of the `C`_ programming
    language and of `Unix`_*

Tatsu
=====

**Tatsu** (the successor to **Grako**) is a tool that takes grammars in a
variation of `EBNF`_ as input, and outputs `memoizing`_ (`Packrat`_)
`PEG`_ parsers in `Python`_.

**Tatsu** can also compile a grammar stored in a string into a
``tatsu.grammars.Grammar`` object that can be used to parse any given
input, much like the `re`_ module does with regular expressions.

Installation
------------

.. code:: bash

    $ pip install tatsu


Using the Tool
--------------

**Tatsu** can generate Python_ code for a parser, be used as a library, much like `Python`_'s ``re``, by embedding grammars as strings and generating grammar models instead of generating code.

-  ``tatsu.compile(grammar, name=None, **kwargs)`` > Compiles the
   grammar and generates a *model* that can subsequently be used for
   parsing input with.

-  ``tatsu.parse(grammar, input, **kwargs)`` > Compiles the grammar and
   parses the given input producing an
   `AST <https://en.wikipedia.org/wiki/Abstract_syntax_tree>`__ as
   result. The result is equivalent to calling
   ``model = compile(grammar); model.parse(input)``. Compiled grammars
   are cached for efficiency.

-  ``tatsu.to_python_sourcecode(grammar, name=None, filename=None, **kwargs)``
   > Compiles the grammar to the `Python`_ sourcecode that implements
   the parser.

This is an example of how to use **Tatsu** as a library:

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

        json_ast = asjson(ast)
        print('JSON')
        print(json.dumps(json_ast, indent=2))
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

License
-------

You may use **Tatsu** under the terms of the `BSD`_-style license
described in the enclosed **`LICENSE.txt`_** file. *If your project
requires different licensing* please `email`_.

Documentation
-------------

For a detailed explanation of what **Tatsu** is capable off, please see the
documentation_.

.. _documentation: http://tatsu.readthedocs.io/

Questions?
----------

For general Q&A, please use the ``[tatsu]`` tag on `StackOverflow`_.

Changes
-------

See the `CHANGELOG`_ for details.

.. _Dennis Ritchie: http://en.wikipedia.org/wiki/Dennis_Ritchie
.. _C: http://en.wikipedia.org/wiki/C_language
.. _Unix: http://en.wikipedia.org/wiki/Unix
.. _make a donation: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=P9PV7ZACB669J
.. _EBNF: http://en.wikipedia.org/wiki/Ebnf
.. _memoizing: http://en.wikipedia.org/wiki/Memoization
.. _Packrat: http://bford.info/packrat/
.. _PEG: http://en.wikipedia.org/wiki/Parsing_expression_grammar
.. _Python: http://python.org
.. _re: https://docs.python.org/3.4/library/re.html
.. _Perl: http://www.perl.org/
.. _context managers: http://docs.python.org/2/library/contextlib.html
.. _Cyclomatic complexity: http://en.wikipedia.org/wiki/Cyclomatic_complexity
.. _KLOC: http://en.wikipedia.org/wiki/KLOC
.. _regex: https://pypi.python.org/pypi/regex
.. _colorama: https://pypi.python.org/pypi/colorama/
.. _pygraphviz: https://pypi.python.org/pypi/pygraphviz
.. _Ruby: http://www.ruby-lang.org/
.. _Abstract Syntax Tree: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _AST: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _Semantic Graph: http://en.wikipedia.org/wiki/Abstract_semantic_graph
.. _VIM: http://www.vim.org/
.. _Sublime Text: https://www.sublimetext.com
.. _raw string literal: https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals
.. _Reserved Words: https://en.wikipedia.org/wiki/Reserved_word
.. _Keywords: https://en.wikipedia.org/wiki/Reserved_word
.. _keywords: https://en.wikipedia.org/wiki/Reserved_word
.. _keyword: https://en.wikipedia.org/wiki/Reserved_word
.. _Warth et al: http://www.vpri.org/pdf/tr2007002_packrat.pdf
.. _ANTLR: http://www.antlr.org/
.. _parsewkt: https://github.com/cleder/parsewkt
.. _Well-known text: http://en.wikipedia.org/wiki/Well-known_text
.. _WTK: http://en.wikipedia.org/wiki/Well-known_text
.. _lambdafu: http://blog.marcus-brinkmann.de/
.. _smc.mw: https://github.com/lambdafu/smc.mw
.. _MediaWiki: http://www.mediawiki.org/wiki/MediaWiki
.. _BSD: http://en.wikipedia.org/wiki/BSD_licenses#2-clause_license_.28.22Simplified_BSD_License.22_or_.22FreeBSD_License.22.29
.. _LICENSE.txt: LICENSE.txt
.. _email: mailto:apalala@gmail.com
.. _StackOverflow: http://stackoverflow.com/tags/tatsu/info
.. _Tatsu Forum: https://groups.google.com/forum/?fromgroups#!forum/tatsu
.. _Euler: http://en.wikipedia.org/wiki/Euler_programming_language
.. _Algol W: http://en.wikipedia.org/wiki/Algol_W
.. _Pascal: http://en.wikipedia.org/wiki/Pascal_programming_language
.. _Modula: http://en.wikipedia.org/wiki/Modula
.. _Modula-2: http://en.wikipedia.org/wiki/Modula-2
.. _Oberon: http://en.wikipedia.org/wiki/Oberon_(programming_language)
.. _Oberon-2: http://en.wikipedia.org/wiki/Oberon-2
.. _Algorithms + Data Structures = Programs: http://www.amazon.com/Algorithms-Structures-Prentice-Hall-Automatic-Computation/dp/0130224189/
.. _Wirth: http://en.wikipedia.org/wiki/Niklaus_Wirth
.. _LL(1): http://en.wikipedia.org/wiki/LL(1)
.. _PL/0: http://en.wikipedia.org/wiki/PL/0
.. _introduced: http://dl.acm.org/citation.cfm?id=964001.964011
.. _PEG.js: http://pegjs.majda.cz/
.. _blog post: http://dietbuddha.blogspot.com/2012/12/52python-encapsulating-exceptions-with.html
.. _Python Weekly: http://www.pythonweekly.com/
.. _exceptions: http://www.jeffknupp.com/blog/2013/02/06/write-cleaner-python-use-exceptions/
.. _Jack: http://en.wikipedia.org/wiki/Javacc
.. _PyPy: http://pypy.org/
.. _PyPy team: http://pypy.org/people.html
.. _CSAIL at MIT: http://www.csail.mit.edu/
.. _PEG and Packrat parsing mailing list: https://lists.csail.mit.edu/mailman/listinfo/peg
.. _UCAB: http://www.ucab.edu.ve/
.. _USB: http://www.usb.ve/
.. _declensions: http://en.wikipedia.org/wiki/Declension
.. _English: http://en.wikipedia.org/wiki/English_grammar
.. _Japanese: http://en.wikipedia.org/wiki/Japanese_grammar
.. _Marcus Brinkmann: http://blog.marcus-brinkmann.de/
.. _Robert Speer: https://bitbucket.org/r_speer
.. _Basel Shishani: https://bitbucket.org/basel-shishani
.. _Paul Sargent: https://bitbucket.org/PaulS/
.. _Kathryn Long: https://bitbucket.org/starkat
.. _David Röthlisberger: https://bitbucket.org/drothlis/
.. _basel-shishani: https://bitbucket.org/basel-shishani
.. _drothlis: https://bitbucket.org/drothlis
.. _franz\_g: https://bitbucket.org/franz_g
.. _gapag: https://bitbucket.org/gapag
.. _gegenschall: https://bitbucket.org/gegenschall
.. _gkimbar: https://bitbucket.org/gkimbar
.. _jimon: https://bitbucket.org/jimon
.. _leewz: https://bitbucket.org/leewz
.. _linkdd: https://bitbucket.org/linkdd
.. _nehz: https://bitbucket.org/nehz
.. _neumond: https://bitbucket.org/neumond
.. _pauls: https://bitbucket.org/pauls
.. _pgebhard: https://bitbucket.org/pgebhard
.. _r\_speer: https://bitbucket.org/r_speer
.. _siemer: https://bitbucket.org/siemer
.. _sjbrownBitbucket: https://bitbucket.org/sjbrownBitbucket
.. _starkat: https://bitbucket.org/starkat
.. _tonico\_strasser: https://bitbucket.org/tonico_strasser
.. _vinay.sajip: https://bitbucket.org/vinay.sajip
.. _vmuriart: https://bitbucket.org/vmuriart
.. _CHANGELOG: CHANGELOG.md

.. |fury| image:: https://badge.fury.io/py/tatsu.svg
   :target: https://badge.fury.io/py/tatsu
.. |license| image:: https://img.shields.io/badge/license-BSD-blue.svg
   :target: https://raw.githubusercontent.com/apalala/tatsu/master/LICENSE.txt
.. |pyversions| image:: https://img.shields.io/pypi/pyversions/tatsu.svg
   :target: https://pypi.python.org/pypi/tatsu
.. |travis| image:: https://secure.travis-ci.org/apalala/tatsu.svg
   :target: http://travis-ci.org/apalala/tatsu
.. |landscape| image:: https://landscape.io/github/apalala/tatsu/master/landscape.png
   :target: https://landscape.io/github/apalala/tatsu/master
.. |donate| image:: https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif
   :target: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=P9PV7ZACB669J

.. |dragon| unicode:: 0x7ADC .. unicode dragon
.. |TatSu| replace:: |dragon| **TatSu**

|license| |pyversions| |fury| |actions| |docs|

    *At least for the people who send me mail about a new language that
    they're designing, the general advice is: do it to learn about how
    to write a compiler. Don't have any expectations that anyone will
    use it, unless you hook up with some sort of organization in a
    position to push it hard. It's a lottery, and some can buy a lot of
    the tickets. There are plenty of beautiful languages (more beautiful
    than C) that didn't catch on. But someone does win the lottery, and
    doing a language at least teaches you something.*

    `Dennis Ritchie`_ (1941-2011) Creator of the C_ programming
    language and of Unix_


|TatSu|
=======

.. code-block:: python

    def WARNING():
        """
        TatSu>=5.7 requires Python>=3.10

        Python 3.8, 3.9, and 3.10 introduced new language features
        that allow writing better programs more clearly. Code written
        for Python 3.7 should run fine on Python up to 3.1q with no changes.

        Python has adopted an annual release schedule (PEP-602).

        Python 3.11 will be released in Oct 2022
        Python 3.10 was released     in Oct 2021
        Python 3.9  bugfix releases final in May 2022
        Python 3.8  bugfix releases final in May 2021
        Python 3.7  bugfix releases final in mid 2020

        Compelling reasons to upgrade projects to the latest Python
        """
        pass


|TatSu| is a tool that takes grammars in a variation of `EBNF`_ as input, and
outputs `memoizing`_ (`Packrat`_) `PEG`_ parsers in `Python`_.

|TatSu| can compile a grammar stored in a string into a
``tatsu.grammars.Grammar`` object that can be used to parse any given
input, much like the `re`_ module does with regular expressions, or it can generate a Python_ module that implements the parser.

|TatSu| supports `left-recursive`_  rules in PEG_ grammars using the
algorithm_ by *Laurent* and *Mens*. The generated AST_ has the expected left associativity.

.. _algorithm: http://norswap.com/pubs/sle2016.pdf

Installation
------------

.. code-block:: bash

    $ pip install TatSu


Using the Tool
--------------

|TatSu| can be used as a library, much like `Python`_'s ``re``, by embedding grammars as strings and generating grammar models instead of generating Python_ code.

-   ``tatsu.compile(grammar, name=None, **kwargs)``

    Compiles the grammar and generates a *model* that can subsequently be used for parsing input with.

-   ``tatsu.parse(grammar, input, **kwargs)``

    Compiles the grammar and parses the given input producing an AST_ as result. The result is equivalent to calling::

        model = compile(grammar)
        ast = model.parse(input)

    Compiled grammars are cached for efficiency.

-   ``tatsu.to_python_sourcecode(grammar, name=None, filename=None, **kwargs)``

    Compiles the grammar to the `Python`_ sourcecode that implements the parser.

This is an example of how to use |TatSu| as a library:

.. code-block:: python

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
        import json
        from tatsu import parse
        from tatsu.util import asjson

        ast = parse(GRAMMAR, '3 + 5 * ( 10 - 20 )')
        print(json.dumps(asjson(ast), indent=2))
..

|TatSu| will use the first rule defined in the grammar as the *start* rule.

This is the output:

.. code-block:: console

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

Documentation
-------------

For a detailed explanation of what |TatSu| is capable of, please see the
documentation_.

.. _documentation: http://tatsu.readthedocs.io/


Questions?
----------

Please use the `[tatsu]`_ tag on `StackOverflow`_ for general Q&A, and limit
Github issues to bugs, enhancement proposals, and feature requests.

.. _[tatsu]: https://stackoverflow.com/tags/tatsu/info


Changes
-------

See the `CHANGELOG`_ for details.


License
-------

You may use |TatSu| under the terms of the `BSD`_-style license
described in the enclosed `LICENSE.txt`_ file. *If your project
requires different licensing* please `email`_.


.. _ANTLR: http://www.antlr.org/
.. _AST: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _Abstract Syntax Tree: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _Algol W: http://en.wikipedia.org/wiki/Algol_W
.. _Algorithms + Data Structures = Programs: http://www.amazon.com/Algorithms-Structures-Prentice-Hall-Automatic-Computation/dp/0130224189/
.. _BSD: http://en.wikipedia.org/wiki/BSD_licenses#2-clause_license_.28.22Simplified_BSD_License.22_or_.22FreeBSD_License.22.29
.. _Basel Shishani: https://bitbucket.org/basel-shishani
.. _C: http://en.wikipedia.org/wiki/C_language
.. _CHANGELOG: https://github.com/neogeny/TatSu/releases
.. _CSAIL at MIT: http://www.csail.mit.edu/
.. _Cyclomatic complexity: http://en.wikipedia.org/wiki/Cyclomatic_complexity
.. _David Röthlisberger: https://bitbucket.org/drothlis/
.. _Dennis Ritchie: http://en.wikipedia.org/wiki/Dennis_Ritchie
.. _EBNF: http://en.wikipedia.org/wiki/Ebnf
.. _English: http://en.wikipedia.org/wiki/English_grammar
.. _Euler: http://en.wikipedia.org/wiki/Euler_programming_language
.. _Grako: https://bitbucket.org/neogeny/grako/
.. _Jack: http://en.wikipedia.org/wiki/Javacc
.. _Japanese: http://en.wikipedia.org/wiki/Japanese_grammar
.. _KLOC: http://en.wikipedia.org/wiki/KLOC
.. _Kathryn Long: https://bitbucket.org/starkat
.. _Keywords: https://en.wikipedia.org/wiki/Reserved_word
.. _`left-recursive`: https://en.wikipedia.org/wiki/Left_recursion
.. _LL(1): http://en.wikipedia.org/wiki/LL(1)
.. _Marcus Brinkmann: http://blog.marcus-brinkmann.de/
.. _MediaWiki: http://www.mediawiki.org/wiki/MediaWiki
.. _Modula-2: http://en.wikipedia.org/wiki/Modula-2
.. _Modula: http://en.wikipedia.org/wiki/Modula
.. _Oberon-2: http://en.wikipedia.org/wiki/Oberon-2
.. _Oberon: http://en.wikipedia.org/wiki/Oberon_(programming_language)
.. _PEG and Packrat parsing mailing list: https://lists.csail.mit.edu/mailman/listinfo/peg
.. _PEG.js: http://pegjs.majda.cz/
.. _PEG: http://en.wikipedia.org/wiki/Parsing_expression_grammar
.. _PL/0: http://en.wikipedia.org/wiki/PL/0
.. _Packrat: http://bford.info/packrat/
.. _Pascal: http://en.wikipedia.org/wiki/Pascal_programming_language
.. _Paul Sargent: https://bitbucket.org/PaulS/
.. _Perl: http://www.perl.org/
.. _PyPy team: http://pypy.org/people.html
.. _PyPy: http://pypy.org/
.. _Python Weekly: http://www.pythonweekly.com/
.. _Python: http://python.org
.. _Reserved Words: https://en.wikipedia.org/wiki/Reserved_word
.. _Robert Speer: https://bitbucket.org/r_speer
.. _Ruby: http://www.ruby-lang.org/
.. _Semantic Graph: http://en.wikipedia.org/wiki/Abstract_semantic_graph
.. _StackOverflow: http://stackoverflow.com/tags/tatsu/info
.. _Sublime Text: https://www.sublimetext.com
.. _TatSu Forum: https://groups.google.com/forum/?fromgroups#!forum/tatsu
.. _UCAB: http://www.ucab.edu.ve/
.. _USB: http://www.usb.ve/
.. _Unix: http://en.wikipedia.org/wiki/Unix
.. _VIM: http://www.vim.org/
.. _WTK: http://en.wikipedia.org/wiki/Well-known_text
.. _Warth et al: http://www.vpri.org/pdf/tr2007002_packrat.pdf
.. _Well-known text: http://en.wikipedia.org/wiki/Well-known_text
.. _Wirth: http://en.wikipedia.org/wiki/Niklaus_Wirth
.. _`LICENSE.txt`: LICENSE.txt
.. _basel-shishani: https://bitbucket.org/basel-shishani
.. _blog post: http://dietbuddha.blogspot.com/2012/12/52python-encapsulating-exceptions-with.html
.. _colorama: https://pypi.python.org/pypi/colorama/
.. _context managers: http://docs.python.org/2/library/contextlib.html
.. _declensions: http://en.wikipedia.org/wiki/Declension
.. _drothlis: https://bitbucket.org/drothlis
.. _email: mailto:apalala@gmail.com
.. _exceptions: http://www.jeffknupp.com/blog/2013/02/06/write-cleaner-python-use-exceptions/
.. _franz\_g: https://bitbucket.org/franz_g
.. _gapag: https://bitbucket.org/gapag
.. _gegenschall: https://bitbucket.org/gegenschall
.. _gkimbar: https://bitbucket.org/gkimbar
.. _introduced: http://dl.acm.org/citation.cfm?id=964001.964011
.. _jimon: https://bitbucket.org/jimon
.. _keyword: https://en.wikipedia.org/wiki/Reserved_word
.. _keywords: https://en.wikipedia.org/wiki/Reserved_word
.. _lambdafu: http://blog.marcus-brinkmann.de/
.. _leewz: https://bitbucket.org/leewz
.. _linkdd: https://bitbucket.org/linkdd
.. _make a donation: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=P9PV7ZACB669J
.. _memoizing: http://en.wikipedia.org/wiki/Memoization
.. _nehz: https://bitbucket.org/nehz
.. _neumond: https://bitbucket.org/neumond
.. _parsewkt: https://github.com/cleder/parsewkt
.. _pauls: https://bitbucket.org/pauls
.. _pgebhard: https://bitbucket.org/pgebhard
.. _pygraphviz: https://pypi.python.org/pypi/pygraphviz
.. _r\_speer: https://bitbucket.org/r_speer
.. _raw string literal: https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals
.. _re: https://docs.python.org/3.7/library/re.html
.. _regex: https://pypi.python.org/pypi/regex
.. _siemer: https://bitbucket.org/siemer
.. _sjbrownBitbucket: https://bitbucket.org/sjbrownBitbucket
.. _smc.mw: https://github.com/lambdafu/smc.mw
.. _starkat: https://bitbucket.org/starkat
.. _tonico\_strasser: https://bitbucket.org/tonico_strasser
.. _vinay.sajip: https://bitbucket.org/vinay.sajip
.. _vmuriart: https://bitbucket.org/vmuriart

.. |fury| image:: https://badge.fury.io/py/TatSu.svg
   :target: https://badge.fury.io/py/TatSu
.. |license| image:: https://img.shields.io/badge/license-BSD-blue.svg
   :target: https://raw.githubusercontent.com/neogeny/tatsu/master/LICENSE.txt
.. |pyversions| image:: https://img.shields.io/pypi/pyversions/tatsu.svg
   :target: https://pypi.python.org/pypi/tatsu
.. |travis| image:: https://secure.travis-ci.org/neogeny/TatSu.svg
   :target: http://travis-ci.org/neogeny/TatSu
.. |actions| image:: https://github.com/neogeny/TatSu/workflows/tests/badge.svg
    :target: https://github.com/neogeny/TatSu/actions
.. |circleci| image:: https://circleci.com/gh/neogeny/TatSu.svg?style=shield
    :target: https://circleci.com/gh/neogeny/TatSu
.. |landscape| image:: https://landscape.io/github/apalala/TatSu/master/landscape.png
   :target: https://landscape.io/github/apalala/TatSu/master
.. |donate| image:: https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif
   :target: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=2TW56SV6WNJV6
.. |quantifiedcode| image:: https://www.quantifiedcode.com/api/v1/project/f60bbd94ae2d4bd5b2e04c241c9d47ff/badge.svg
   :target: https://www.quantifiedcode.com/app/project/f60bbd94ae2d4bd5b2e04c241c9d47ff
   :alt: Code issues
.. |docs| image:: https://readthedocs.org/projects/tatsu/badge/?version=stable
   :target: http://tatsu.readthedocs.io/en/stable/

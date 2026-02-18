.. Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
.. SPDX-License-Identifier: BSD-4-Clause

.. |dragon| unicode:: 0x7ADC .. unicode dragon
.. |nbsp| unicode:: 0xA0 .. non breakable space
.. |TatSu| replace:: |dragon|\ |nbsp|\ **TatSu**
.. |TatSu-LTS| replace:: |dragon|\ |nbsp|\ **TatSu-LTS**
.. _RELEASES: https://github.com/neogeny/TatSu/releases

| |license|
| |pyversions|
| |fury|
| |actions|
| |docs|
| |installs|
| |sponsor|
|

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

|TatSu| is a tool that takes grammars in a superset of `EBNF`_ as input, and
outputs `memoizing`_ (`Packrat`_) `PEG`_ parsers in `Python`_. The classic
variations of EBNF_ (Tomassetti, EasyExtend, Wirth) and `ISO EBNF`_ are also
supported as input grammar format.

Why use a PEG_ parser? Because `regular languages`_ (those parsable with Python's ``re`` package) *"cannot count"*. Any language with nested structures or with balancing of demarcations requires more than regular expressions to be parsed.

|TatSu| can compile a grammar stored in a string into a
``tatsu.grammars.Grammar`` object that can be used to parse any given
input, much like the `re`_ module does with regular expressions, or it can generate a Python_ module that implements the parser.

|TatSu| supports `left-recursive`_  rules in PEG_ grammars using the
algorithm_ by *Laurent* and *Mens*. The generated AST_ has the expected left associativity.

|TatSu| expects a maintained version of Python (>=3.14 at the moment).  While no code
in |TatSu| yet depends on new language or standard library features,
the authors don't want to be constrained by Python version compatibility considerations
when developing future releases. That said, currently all tests run in versions down to
Python 3.12.

*If you need support for previous versions of Python, please consider* `TatSu-LTS`_,
*a  friendly fork of* |TatSu| *aimed at compatibility with other versions of Python still used by
many projects. The developers of both projects work together to promote compatibility
with most versions of Python.*

.. _algorithm: http://norswap.com/pubs/sle2016.pdf
.. _TatSu-LTS: https://pypi.org/project/TatSu-LTS/

Installation
------------

.. code-block:: bash

    $ pip install TatSu


Using the Tool
--------------

|TatSu| can be used as a library, much like `Python`_'s ``re``, by embedding grammars as strings and generating grammar models instead of generating Python_ code.

This compiles the grammar and generates an in-memory *parser* that can subsequently be used for parsing input with:

.. code-block:: python

   parser = tatsu.compile(grammar)


Compiles the grammar and parses the given input producing an AST_ as result:

.. code-block:: python

    ast = tatsu.parse(grammar, input)

The result is equivalent to calling:

.. code-block:: python

    parser = compile(grammar)
    ast = parser.parse(input)

Compiled grammars are cached for efficiency.

This compiles the grammar to the `Python`_ sourcecode that implements the parser:

.. code-block:: python

    parser_source = tatsu.to_python_sourcecode(grammar)

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

See the `RELEASES`_ for details.


License
-------

You may use |TatSu| under the terms of the `BSD`_-style license
described in the enclosed `LICENSE`_ file. *If your project
requires different licensing* please `email`_.


For Fun
-------

This is a diagram of the grammar for |TatSu|'s own grammar language:


.. code:: console

    start ●─grammar─■

    grammar ●─`TATSU`──┬→─────────────────┬──rule──┬→───────────────┬───🔚 ─■
                       ├→──┬─directive─┬──┤        ├→──┬─rule────┬──┤
                       │   └─keyword───┘  │        │   └─keyword─┘  │
                       └─────────────────<┘        └───────────────<┘

    directive ●─'@@'─ !['keyword'] ✂ ───┬───┬─'comments'─────┬─ ✂ ─ ✂ ─'::' ✂ ─regex────────┬─ ✂ ──■
                                        │   └─'eol_comments'─┘                      ─────── │
                                        ├─'whitespace' ✂ ─'::' ✂ ───┬─regex───┬─────────────┤
                                        │                           ├─string──┤ ─────────── │
                                        │                           ├─'None'──┤ ─────────── │
                                        │                           ├─'False'─┤ ─────────── │
                                        │                           └─`None`──┘ ─────────── │
                                        ├───┬─'nameguard'──────┬─ ✂ ───┬─'::' ✂ ─boolean─┬──┤
                                        │   ├─'ignorecase'─────┤       └─`True`──────────┘  │
                                        │   ├─'left_recursion'─┤                            │
                                        │   ├─'parseinfo'──────┤                            │
                                        │   └─'memoization'────┘                            │
                                        ├─'grammar' ✂ ─'::' ✂ ─word─────────────────────────┤
                                        └─'namechars' ✂ ─'::' ✂ ─string─────────────────────┘

    keywords ●───┬─keywords─┬───■
                 └─────────<┘

    keyword ●─'@@keyword' ✂ ─'::' ✂ ───┬→───────────────────────────────────┬───■
                                       ├→ @+:(──┬─word───┬─)─ ![──┬─':'─┬─]─┤
                                       │        └─string─┘        └─'='─┘   │
                                       └───────────────────────────────────<┘

    paramdef ●───┬─'::' ✂ ─params─────────────────────────┬──■
                 └─'(' ✂ ───┬─kwparams──────────────┬─')'─┘
                            ├─params',' ✂ ─kwparams─┤
                            └─params────────────────┘

    rule ●───┬→──────────┬──name ✂ ───┬─→ >( <'paramdef'> )─┬───┬─→'<' ✂ ─known_name─┬───┬─'='──┬─ ✂ ─expreRULE_END ✂ ──■
             ├→decorator─┤            └─→───────────────────┘   └─→──────────────────┘   ├─':='─┤
             └──────────<┘                                                               └─':'──┘

    RULE_END ●───┬─EMPTYLINE──┬─→';'─┬──┬──■
                 │            └─→────┘  │
                 ├──🔚 ─────────────────┤
                 └─';'──────────────────┘

    EMPTYLINE ●─/(?:\s*(?:\r?\n|\r)){2,}/──■

    decorator ●─'@'─ !['@'] ✂ ─ @:(──┬─'override'─┬─)─■
                                     ├─'name'─────┤
                                     └─'nomemo'───┘

    params ●─ @+:(first_param)──┬→─────────────────────────────┬───■
                                ├→',' @+:(literal)─ !['='] ✂ ──┤
                                └─────────────────────────────<┘

    first_param ●───┬─path────┬──■
                    └─literal─┘

    kwparams ●───┬→────────────┬───■
                 ├→',' ✂ ─pair─┤
                 └────────────<┘

    pair ●─ @+:(word)'=' ✂ ─ @+:(literal)─■

    expre ●───┬─choice───┬──■
              └─sequence─┘

    choice ●───┬─→'|' ✂ ──┬─ @+:(option)──┬─'|' ✂ ─ @+:(option)─┬───■
               └─→────────┘               └────────────────────<┘

    option ●─ @:(sequence)─■

    sequence ●───┬── &[element',']──┬→───────────────┬───┬──■
                 │                  ├→',' ✂ ─element─┤   │
                 │                  └───────────────<┘   │
                 └───┬── ![EMPTYLINE]element─┬───────────┘
                     └──────────────────────<┘

    element ●───┬─rule_include─┬──■
                ├─named────────┤
                ├─override─────┤
                └─term─────────┘

    rule_include ●─'>' ✂ ─ @:(known_name)─■

    named ●───┬─named_list───┬──■
              └─named_single─┘

    named_list ●─name'+:' ✂ ─term─■

    named_single ●─name':' ✂ ─term─■

    override ●───┬─override_list──────────────┬──■
                 ├─override_single────────────┤
                 └─override_single_deprecated─┘

    override_list ●─'@+:' ✂ ─ @:(term)─■

    override_single ●─'@:' ✂ ─ @:(term)─■

    override_single_deprecated ●─'@' ✂ ─ @:(term)─■

    term ●───┬─void───────────────┬──■
             ├─gather─────────────┤
             ├─join───────────────┤
             ├─left_join──────────┤
             ├─right_join─────────┤
             ├─empty_closure──────┤
             ├─positive_closure───┤
             ├─closure────────────┤
             ├─optional───────────┤
             ├─skip_to────────────┤
             ├─lookahead──────────┤
             ├─negative_lookahead─┤
             ├─cut────────────────┤
             ├─cut_deprecated─────┤
             └─atom───────────────┘

    group ●─'(' ✂ ─ @:(expre)')' ✂ ──■

    gather ●── &[atom'.{'] ✂ ───┬─positive_gather─┬──■
                                └─normal_gather───┘

    positive_gather ●─atom'.{'expre'}'──┬─'+'─┬─ ✂ ──■
                                        └─'-'─┘

    normal_gather ●─atom'.{' ✂ ─expre'}'──┬─→'*' ✂ ──┬─ ✂ ──■
                                          └─→────────┘

    join ●── &[atom'%{'] ✂ ───┬─positive_join─┬──■
                              └─normal_join───┘

    positive_join ●─atom'%{'expre'}'──┬─'+'─┬─ ✂ ──■
                                      └─'-'─┘

    normal_join ●─atom'%{' ✂ ─expre'}'──┬─→'*' ✂ ──┬─ ✂ ──■
                                        └─→────────┘

    left_join ●─atom'<{' ✂ ─expre'}'──┬─'+'─┬─ ✂ ──■
                                      └─'-'─┘

    right_join ●─atom'>{' ✂ ─expre'}'──┬─'+'─┬─ ✂ ──■
                                       └─'-'─┘

    positive_closure ●───┬─'{' @:(expre)'}'──┬─'-'─┬─ ✂ ──┬──■
                         │                   └─'+'─┘      │
                         └─ @:(atom)'+' ✂ ────────────────┘

    closure ●───┬─'{' @:(expre)'}'──┬─→'*'─┬─ ✂ ──┬──■
                │                   └─→────┘      │
                └─ @:(atom)'*' ✂ ─────────────────┘

    empty_closure ●─'{' @:( ∅ )'}'─■

    optional ●───┬─'[' ✂ ─ @:(expre)']' ✂ ──────────┬──■
                 └─ @:(atom)─ ![──┬─'?"'─┬─]'?' ✂ ──┘
                                  ├─"?'"─┤
                                  └─'?/'─┘

    lookahead ●─'&' ✂ ─ @:(term)─■

    negative_lookahead ●─'!' ✂ ─ @:(term)─■

    skip_to ●─'->' ✂ ─ @:(term)─■

    atom ●───┬─group────┬──■
             ├─token────┤
             ├─alert────┤
             ├─constant─┤
             ├─call─────┤
             ├─pattern──┤
             ├─dot──────┤
             └─eof──────┘

    call ●─word─■

    void ●─'()' ✂ ──■

    fail ●─'!()' ✂ ──■

    cut ●─'~' ✂ ──■

    cut_deprecated ●─'>>' ✂ ──■

    known_name ●─name ✂ ──■

    name ●─word─■

    constant ●── &['`']──┬─/(?ms)```((?:.|\n)*?)```/──┬──■
                         ├─'`' @:(literal)'`'─────────┤
                         └─/`(.*?)`/──────────────────┘

    alert ●─/\^+/─constant─■

    token ●───┬─string─────┬──■
              └─raw_string─┘

    literal ●───┬─string─────┬──■
                ├─raw_string─┤
                ├─boolean────┤
                ├─word───────┤
                ├─hex────────┤
                ├─float──────┤
                ├─int────────┤
                └─null───────┘

    string ●─STRING─■

    raw_string ●─//─ @:(STRING)─■

    STRING ●───┬─ @:(/"((?:[^"\n]|\\"|\\\\)*?)"/─) ✂ ─────┬──■
               └─ @:(/r"'((?:[^'\n]|\\'|\\\\)*?)'"/─) ✂ ──┘

    hex ●─/0[xX](?:\d|[a-fA-F])+/──■

    float ●─/[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[Ee][-+]?\d+)?/──■

    int ●─/[-+]?\d+/──■

    path ●─/(?!\d)\w+(?:::(?!\d)\w+)+/──■

    word ●─/(?!\d)\w+/──■

    dot ●─'/./'─■

    pattern ●─regexes─■

    regexes ●───┬→─────────────┬───■
                ├→'+' ✂ ─regex─┤
                └─────────────<┘

    regex ●───┬─'/' ✂ ─ @:(/(?:[^/\\]|\\/|\\.)*/─)'/' ✂ ──┬──■
              ├─'?' @:(STRING)────────────────────────────┤
              └─deprecated_regex──────────────────────────┘

    deprecated_regex ●─'?/' ✂ ─ @:(/(?:.|\n)*?(?=/\?)/─)//\?+/─ ✂ ──■

    boolean ●───┬─'True'──┬──■
                └─'False'─┘

    null ●─'None'─■

    eof ●─'$' ✂ ──■




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
.. _ISO EBNF: http://en.wikipedia.org/wiki/Ebnf
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
.. _`LICENSE`: LICENSE
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
.. _r\_speer: https://bitbucket.org/r_speer
.. _raw string literal: https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals
.. _re: https://docs.python.org/3.7/library/re.html
.. _regular languages: https://en.wikipedia.org/wiki/Regular_language
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
   :target: https://raw.githubusercontent.com/neogeny/tatsu/master/LICENSE
.. |pyversions| image:: https://img.shields.io/pypi/pyversions/tatsu.svg
   :target: https://pypi.python.org/pypi/tatsu
.. |actions| image:: https://github.com/neogeny/TatSu/actions/workflows/default.yml/badge.svg
   :target: https://github.com/neogeny/TatSu/actions/workflows/default.yml
.. |docs| image:: https://readthedocs.org/projects/tatsu/badge/?version=stable&logo=readthedocs
   :target: http://tatsu.readthedocs.io/en/stable/
.. |installs| image:: https://img.shields.io/pypi/dm/tatsu.svg?label=installs&logo=pypi
   :target: https://pypistats.org/packages/tatsu
.. |downloads| image:: https://img.shields.io/github/downloads/neogeny/tatsu/total?label=downloads
   :target: https://pypistats.org/packages/tatsu
.. |sponsor| image:: https://img.shields.io/badge/Sponsor-EA4AAA?label=TatSu
   :target: https://github.com/sponsors/neogeny

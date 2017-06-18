.. |dragon| unicode:: 0x7ADC .. unicode dragon
.. |TatSu| replace:: |dragon| **TatSu**

Change Log
==========

|TatSu| uses `Semantic Versioning`_ for its releases, so parts
of the version number may increase without any significant changes or
backwards incompatibilities in the software.

The format of this *Change Log* is inspired by `keeapachangelog.org`_.

`X.Y.Z`_ @ 2017
---------------
.. _X.Y.Z: https://github.com/apalala/tatsu/compare/v4.2.1...master


`4.2.1`_ @ 2017-06-18
---------------------
.. _4.2.1: https://github.com/apalala/tatsu/compare/v4.2.0...v4.2.1


Fixed
~~~~~

*   `#27`_ Left-recursive parsers would drop or skip input on many combinations of grammars and correct/incorrect inputs(`@manueljacob`_)

*   Documentation fixes (`@manueljacob`_, `@paulhoule`_)

.. _#27: https://github.com/neogeny/TatSu/issues/27



`4.2.0`_ @ 2017-05-21
---------------------
.. _4.2.0: https://github.com/apalala/tatsu/compare/v4.1.1...v4.2.0

Added
~~~~~

*   Parse speeds on large files reduced by 5-20% by optimizing parse contexts and closures, and unifying the AST_ and CST_ stacks.

*   Added the *"skip to"* expression ( ``->``), useful for writing *recovery* rules.  The parser will advance over input, one character at time, until the expression matches. Whitespace and comments will be skipped at each step.

*   Added the *any* expression ( ``/./``) for matching the next character in the input.

*   The ANTLR_ grammar for Python3_ to the `g2e` example, and udate `g2e` to handle more ANTLR_ syntax.

*   Check typing with Mypy_.


Changed
~~~~~~~

*   Removed the very old _regex_ example.

*   Make parse traces more compact. Add a sample to the docs.

*   Explain Grako_ compatibility in docs.


`4.1.1`_ @ 2017-05-21
---------------------
.. _4.1.1: https://github.com/apalala/tatsu/compare/v4.1.0...v4.1.1

Fixed
~~~~~

*   ``tatus.objectmodel.Node`` not setting attributes from ``AST``.



`4.1.0`_ @ 2017-05-21
---------------------
.. _4.1.0: https://github.com/apalala/tatsu/compare/v4.0.0...v4.1.0

Added
~~~~~

*  New support for *left recursion* with correct associativity. All test
   cases pass.

*  Left recursion is enabled by default. Use the
   ``@@left_recursion :: False`` directive to diasable it.

*  Renamed the decorator for generated rule methods to ``@tatsumasu``.

*  Refactored the ``tatsu.contexts.ParseContext`` for clarity.

*  The ``@@ignorecase`` directive and the ``ignorecase=`` parameter no
   longer appy to regular expressions (patterns) in grammars. Use
   ``(?i)`` in the pattern to ignore the case in a particular pattern.

*  Now ``tatsu.g2e`` is a library and executable module for translating
   `ANTLR`_ grammars to **TatSu**.

*  Modernized the ``calc`` example and made it part of the documentation
   as *Mini Tutorial*.

*  Simplified the generated object models using the semantics of class
   attributes in Python_

`4.0.0`_ @ 2017-05-06
---------------------
.. _4.0.0: https://github.com/apalala/tatsu/compare/0.0.0...v4.0.0

-  First release.

.. _Semantic Versioning: http://semver.org/
.. _keeapachangelog.org: http://keepachangelog.com/

.. _ANTLR: http://www.antlr.org/
.. _AST: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _Abstract Syntax Tree: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _Algol W: http://en.wikipedia.org/wiki/Algol_W
.. _Algorithms + Data Structures = Programs: http://www.amazon.com/Algorithms-Structures-Prentice-Hall-Automatic-Computation/dp/0130224189/
.. _BSD: http://en.wikipedia.org/wiki/BSD_licenses#2-clause_license_.28.22Simplified_BSD_License.22_or_.22FreeBSD_License.22.29
.. _C: http://en.wikipedia.org/wiki/C_language
.. _CSAIL at MIT: http://www.csail.mit.edu/
.. _CST: https://en.wikipedia.org/wiki/Parse_tree
.. _Cyclomatic complexity: http://en.wikipedia.org/wiki/Cyclomatic_complexity
.. _Dennis Ritchie: http://en.wikipedia.org/wiki/Dennis_Ritchie
.. _EBNF: http://en.wikipedia.org/wiki/Ebnf
.. _English: http://en.wikipedia.org/wiki/English_grammar
.. _Euler: http://en.wikipedia.org/wiki/Euler_programming_language
.. _Grako: https://pypi.python.org/pypi/grako/
.. _Jack: http://en.wikipedia.org/wiki/Javacc
.. _Japanese: http://en.wikipedia.org/wiki/Japanese_grammar
.. _KLOC: http://en.wikipedia.org/wiki/KLOC
.. _Keywords: https://en.wikipedia.org/wiki/Reserved_word
.. _`left-recursive`: https://en.wikipedia.org/wiki/Left_recursion
.. _LICENSE.txt: LICENSE.txt
.. _LL(1): http://en.wikipedia.org/wiki/LL(1)
.. _MediaWiki: http://www.mediawiki.org/wiki/MediaWiki
.. _Modula-2: http://en.wikipedia.org/wiki/Modula-2
.. _Modula: http://en.wikipedia.org/wiki/Modula
.. _Mypy: http://mypy-lang.org
.. _Oberon-2: http://en.wikipedia.org/wiki/Oberon-2
.. _Oberon: http://en.wikipedia.org/wiki/Oberon_(programming_language)
.. _PEG and Packrat parsing mailing list: https://lists.csail.mit.edu/mailman/listinfo/peg
.. _PEG.js: http://pegjs.majda.cz/
.. _PEG: http://en.wikipedia.org/wiki/Parsing_expression_grammar
.. _PL/0: http://en.wikipedia.org/wiki/PL/0
.. _PLY: http://www.dabeaz.com/ply/ply.html#ply_nn22
.. _Packrat: http://bford.info/packrat/
.. _Pascal: http://en.wikipedia.org/wiki/Pascal_programming_language
.. _Perl: http://www.perl.org/
.. _PyPy team: http://pypy.org/people.html
.. _PyPy: http://pypy.org/
.. _Python Weekly: http://www.pythonweekly.com/
.. _Python: http://python.org
.. _Python3: http://python.org
.. _Reserved Words: https://en.wikipedia.org/wiki/Reserved_word
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
.. _blog post: http://dietbuddha.blogspot.com/2012/12/52python-encapsulating-exceptions-with.html
.. _colorama: https://pypi.python.org/pypi/colorama/
.. _context managers: http://docs.python.org/2/library/contextlib.html
.. _declensions: http://en.wikipedia.org/wiki/Declension
.. _email: mailto:apalala@gmail.com
.. _exceptions: http://www.jeffknupp.com/blog/2013/02/06/write-cleaner-python-use-exceptions/
.. _introduced: http://dl.acm.org/citation.cfm?id=964001.964011
.. _keyword: https://en.wikipedia.org/wiki/Reserved_word
.. _keywords: https://en.wikipedia.org/wiki/Reserved_word
.. _lambdafu: http://blog.marcus-brinkmann.de/
.. _make a donation: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=P9PV7ZACB669J
.. _memoizing: http://en.wikipedia.org/wiki/Memoization
.. _parsewkt: https://github.com/cleder/parsewkt
.. _pygraphviz: https://pypi.python.org/pypi/pygraphviz
.. _raw string literal: https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals
.. _re: https://docs.python.org/3.4/library/re.html
.. _regex: https://pypi.python.org/pypi/regex
.. _smc.mw: https://github.com/lambdafu/smc.mw

.. _Basel Shishani: https://bitbucket.org/basel-shishani
.. _David Delassus: https://bitbucket.org/linkdd
.. _David Röthlisberger: https://bitbucket.org/drothlis/
.. _Dmytro Ivanov: https://bitbucket.org/jimon
.. _Franklin Lee: https://bitbucket.org/leewz
.. _Gabriele Paganelli: https://bitbucket.org/gapag
.. _Kathryn Long: https://bitbucket.org/starkat
.. _Manuel Jacob: https://github.com/manueljacob
.. _@manueljacob: https://github.com/manueljacob
.. _Marcus Brinkmann: https://bitbucket.org/lambdafu/
.. _Max Liebkies: https://bitbucket.org/gegenschall
.. _Paul Houle: https://github.com/paulhoule
.. _@paulhoule: https://github.com/paulhoule
.. _Paul Sargent: https://bitbucket.org/pauls
.. _Robert Speer: https://bitbucket.org/r_speer
.. _Ryan Gonzales: https://github.com/kirbyfan64
.. _S Brown: https://bitbucket.org/sjbrownBitbucket
.. _Tonico Strasser: https://bitbucket.org/tonico_strasser
.. _Victor Uriarte: https://bitbucket.org/vmuriart
.. _Vinay Sajip: https://bitbucket.org/vinay.sajip
.. _basel-shishani: https://bitbucket.org/basel-shishani
.. _drothlis: https://bitbucket.org/drothlis
.. _franz\_g: https://bitbucket.org/franz_g
.. _gkimbar: https://bitbucket.org/gkimbar
.. _nehz: https://bitbucket.org/nehz
.. _neumond: https://bitbucket.org/neumond
.. _pgebhard: https://bitbucket.org/pgebhard
.. _siemer: https://bitbucket.org/siemer


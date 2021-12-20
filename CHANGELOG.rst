.. |dragon| unicode:: 0x7ADC .. unicode dragon
.. |TatSu| replace:: |dragon| **TatSu**

Change Log
==========

|TatSu| uses `Semantic Versioning`_ for its releases, so parts
of the version number may increase without any significant changes or
backwards incompatibilities in the software.

The format of this *Change Log* is inspired by `keeapachangelog.org`_.


`X.Y.Z`_ @ 2022
---------------
.. _`X.Y.Z`: https://github.com/apalala/tatsu/compare/v5.7.3...master


`5.7.3`_ @ 2021-12-20
---------------------
.. _`5.7.3`: https://github.com/apalala/tatsu/compare/v5.7.2...v5.7.3

*   Fix that settings passed to ``Context.parse()`` were ignored. Add ``Context.active_config`` for the configuration active during a parse
*   Define ``Node._parent`` as part of the ``@dataclass``


`5.7.2`_ @ 2021-12-18
---------------------
.. _`5.7.2`: https://github.com/apalala/tatsu/compare/v5.7.1...v5.7.2

*   Make ``AST`` and ``Node`` hashable. Necessary for caching ``Node.children()``
*   Implement ``Node.__eq__()`` in terms of identity or ``Node.ast.__eq__()__``
*   Fix regression in which rule order is lost in generated parsers (`@dtrckd`_)
*   Restore ``Node.ast`` (was removed because of problems with ``__eq__()``)
*   Get ``Node.children()`` from ``Node.ast`` when there are no attributes defined for the ``Node``. This restores the desired behavior while developing a parse model.

`5.7.1`_ @ 2021-12-03
---------------------
.. _`5.7.1`: https://github.com/apalala/tatsu/compare/v5.6.1...v5.7.1

*   Simplified this CHANGELOG by not linking to issues or and pull requests that can be queried on Github
*   Now ``config: ParserConfig`` is used in ``__init__()`` and ``parse()`` methods of ``contexts.ParseContext``, ``grammars.Grammar``, and elsewhere to avoid long parameter lists. ``ParserConfig`` also provides clean and clear ways of overridinga group of settings
*   All names defined in the successful choice in a rule are now defined in the resulting `AST`_. Names within optionals that did not match will have their values set to ``None``, and closures that did not match will be set to ``[]``
*   Moved build configuration from ``setup.py`` in favor of ``setup.cfg``  and ``pyproject.toml`` (`@KOLANICH`_)
*   ``Node.children()`` is now computed only when required, and cached
*   Classes in generated object models are now ``@dataclass``
*   Optimize and get rid of bugs and annoyances while keeping backwards compatibility
*   Drop support for Python < 3.10


`5.6.1`_ @ 2021-03-22
---------------------
.. _`5.6.1`: https://github.com/apalala/tatsu/compare/v5.6.0...v5.6.1

*   Fix bug in which rule fields were forced on empty ``AST`` (`@Victorious3`_)

`5.6.0`_ @ 2021-03-21
---------------------
.. _`5.6.0`: https://github.com/apalala/tatsu/compare/v5.5.0...v5.6.0

*   Several important refactorings in ``contexts.ParseContext``
*   Make ``ignorecase`` settings apply to defined ``@@keywords``
*   Move checking of keywords used as names into ``ParseContext``
*   Output of generated parsers again matches that of model parsers
*   Improve *"expecting one of:"* messages so elements are in declaration order
*   Stop code generation if there are closures over possibly empty expressions
*   Preserve name declaration order in returned ``AST``
*   Update the bootstrap parser (``tatsu/bootstrap.py``) to the generated parser
*   Now generated parser's ``main()`` only outputs the JSON for the parse ``AST``
*   Minor version bumped in case the many fixes break backwards-compatibility
*   Minor documentation issues fixed
*   All tests run with Python 3.8, 3.9, 3.10


`5.5.0`_ @ 2020-01-26
---------------------
.. _`5.5.0`: https://github.com/apalala/tatsu/compare/v5.0.0...v5.5.0

*  `#156`_   Clarify limitations of left-recursion in PEG (`@apalala`_)
*  `#159`_   Clean up examples and tutorial, upgrade them to Python 3 (`@okomarov`_)

.. _#156: https://github.com/neogeny/TatSu/issues/156
.. _#159: https://github.com/neogeny/TatSu/pull/159


`5.0.0`_ @ 2020-01-26
-----------------------
.. _5.0.0: https://github.com/apalala/tatsu/compare/v4.4.0...v5.0.0

*   |TatSu| is now only tested against Python 3.8. Earlier versions of Python are now deprecated, and Python 2.X versions are no longer supported.
*   Apply ``nameguard`` only if ``token[0].isalpha()``. This solves a regression afecting previous TatSu and Grako grammars (`@apalala`_).
*   Remove ``pygraphviz`` from develoment requirements, as it doesn't build under Py38
*  `#56`_   Include missing ``tatsu/g2e/antlr.ebnf`` in distribution
*  `#138`_   Reimplement the calculation of ``FIRST``, ``FOLLOW``, and ``LOOKAHEAD`` sets using latest theories. For now, this should improve parser error reporting, but should eventually enable the simplification of parsing of leftrec grammars (`@apalala`_).
*  `#153`_   Import ABCs from ``collections.abc`` (`@tirkarthi`_)
* The AST for sequences is now a ``tuple`` (it used to be a ``list``-derived ``closure``)


.. _#56: https://github.com/neogeny/TatSu/issues/56
.. _#138: https://github.com/neogeny/TatSu/issues/138
.. _#153: https://github.com/neogeny/TatSu/issues/153

`4.4.0`_ @ 2019-04-22
-----------------------
.. _4.4.0: https://github.com/apalala/tatsu/compare/v4.3.0...v4.4.0

*   The default regexp for whitespace was changed to ``(?s)\s+``
*   Allow empty patterns (``//``) like Python does
*  `#65`_ Allow initial, consecutive, and trailing ``@namechars``
*  `#73`_ Allow ``@@whitespace :: None`` and ``@@whitespace :: False``
*  `#75`_ Complete implemenation of left recursion (`@Victorious3`_)
*  `#77`_ Allow ``@keyword`` throughout the grammar
*  `#89`_ Make all attributes defined in the rule present in the resulting ``AST`` or ``Node`` even if the associated expression was not parsed
*  `#93`_ Fix trace colorization on Windows
*  `#96`_ Documented each ``@@directive``
*   Switched the documentation to the "Alabaster" theme
*   Various code and documentation fixes (`@davesque`_, `@nicholasbishop`_, `@rayjolt`_)

.. _#65: https://github.com/neogeny/TatSu/issues/65
.. _#73: https://github.com/neogeny/TatSu/issues/73
.. _#75: https://github.com/neogeny/TatSu/issues/75
.. _#77: https://github.com/neogeny/TatSu/issues/77
.. _#89: https://github.com/neogeny/TatSu/issues/89
.. _#93: https://github.com/neogeny/TatSu/issues/93
.. _#96: https://github.com/neogeny/TatSu/issues/96


`4.3.0`_ @ 2018-11-17
---------------------

.. _`4.3.0`: https://github.com/apalala/tatsu/compare/v4.2.6...v4.3.0

*   `#66`_ Fix multiline ( ``(?x)`` ) patterns not properly supported in grammar  (`@pdw-mb`_)
*   `#70`_ Important upgrade to ``ModelBuilder`` and grammar specification of classes for generated nodes. See `pull request #78`_ for details (`@Victorious3`_)

.. _#66: https://github.com/neogeny/TatSu/issues/66
.. _#70: https://github.com/neogeny/TatSu/issues/70
.. _pull request #78: https://github.com/neogeny/TatSu/pull/78


`4.2.6`_ @ 2018-05-06
----------------------
.. _4.2.6: https://github.com/apalala/tatsu/compare/v4.2.5...v4.2.6

*   `#56`_ Add missing ``tatsu/g2e/antlr.ebnf`` to distribution  (`@Ruth-Polymnia`_)
*   `#62`_ Fix |TatSu| ignoring start rule provided in command line  (`@r-chaves`_)
*   Fix typos in documentation (`@mjdominus`_)

.. _#56: https://github.com/neogeny/TatSu/issues/56
.. _#62: https://github.com/neogeny/TatSu/issues/62


`4.2.5`_ @ 2017-11-26
---------------------
.. _4.2.5: https://github.com/apalala/tatsu/compare/v4.2.4...v4.2.5

*   `#42`_ Rename vim files from ``grako.vim`` to ``tatsu.vim``  (`@fcoelho`_)
*   `#51`_ Fix inconsistent code generation for ``whitespace``  (`@fpom`_)
*   `#54`_ Only care about case of first letter of rule name for determining advance over whitespace (`@acw1251`_)


.. _#42: https://github.com/neogeny/TatSu/issues/42
.. _#51: https://github.com/neogeny/TatSu/issues/51
.. _#54: https://github.com/neogeny/TatSu/pull/54


`4.2.4`_ @ 2017-07-10
---------------------
.. _4.2.4: https://github.com/apalala/tatsu/compare/v4.2.3...v4.2.4

Fixed
~~~~~

*   `#40`_ Make the start rule default to the first rule defined in the grammar (`@hariedo`_)
*   `#43`_ Import 're' from tatsu.util to support optional 'regex'-only features (`@azazel75`_)
*   `#47`_ Fix incorrect sample code in documentation (`@apalala`_)


.. _#40: https://github.com/neogeny/TatSu/issues/40
.. _#43: https://github.com/neogeny/TatSu/issues/43
.. _#47: https://github.com/neogeny/TatSu/issues/47


`4.2.3`_ @ 2017-07-10
---------------------
.. _4.2.3: https://github.com/apalala/tatsu/compare/v4.2.2...v4.2.3

Fixed
~~~~~

*  `#37`_ Regression: The ``#include`` pragma works by using the ``EBNFBuffer`` from ``grammars.py``. Somehow the default ``EBNFBootstrapBuffer`` from ``bootstrap.py`` has been used instead (`@gegenschall`_).

*  `#38`_ Documentation: Use of ``json.dumps()`` requires ``ast.asjson()`` (`@davidchen`_).

.. _#37: https://github.com/neogeny/TatSu/issues/37
.. _#38: https://github.com/neogeny/TatSu/issues/38


`4.2.2`_ @ 2017-07-01
---------------------
.. _4.2.2: https://github.com/apalala/tatsu/compare/v4.2.1...v4.2.2

Fixed
~~~~~

*   `#27`_ Undo the fixes to dropped input on left recursion because they broke previous expected behavior.

*   `#33`_ Fixes to the calc example and mini tutorial (`@heronils`_)

*   `#34`_ More left-recursion test cases (`@manueljacob`_).

.. _#33: https://github.com/neogeny/TatSu/issues/33
.. _#34: https://github.com/neogeny/TatSu/issues/34


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

*   The ANTLR_ grammar for Python3_ to the ``g2e`` example, and udate ``g2e`` to handle more ANTLR_ syntax.

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

.. _@acw1251: https://github.com/acw1251
.. _@apalala: https://github.com/apalala
.. _@azazel75: https://github.com/azazel75
.. _@davidchen: https://github.com/davidchen
.. _@dtrckd: https://github.com/dtrckd
.. _@fcoelho: https://github.com/fcoelho
.. _@fpom: https://github.com/fpom
.. _@gegenschall: https://bitbucket.org/gegenschall
.. _@hariedo: https://github.com/hariedo
.. _@heronils: https://github.com/heronils
.. _@KOLANICH: https://github.com/KOLANICH
.. _@manueljacob: https://github.com/manueljacob
.. _@mjdominus: https://github.com/mjdominus
.. _@paulhoule: https://github.com/paulhoule
.. _@Ruth-Polymnia: https://github.com/Ruth-Polymnia
.. _@r-chaves: https://github.com/r-chaves
.. _@Victorious3: https://github.com/Victorious3
.. _@pdw-mb: https://github.com/pdw-mb
.. _@davesque: https://github.com/davesque
.. _@nicholasbishop: https://github.com/nicholasbishop
.. _@rayjolt: https://github.com/rayjolt
.. _@tirkarthi: https://github.com/tirkarthi
.. _@okomarov: https://github.com/okomarov

.. _Basel Shishani: https://bitbucket.org/basel-shishani
.. _David Chen: https://github.com/davidchen
.. _David Delassus: https://bitbucket.org/linkdd
.. _David Röthlisberger: https://bitbucket.org/drothlis/
.. _Dmytro Ivanov: https://bitbucket.org/jimon
.. _Franklin Lee: https://bitbucket.org/leewz
.. _Gabriele Paganelli: https://bitbucket.org/gapag
.. _Kathryn Long: https://bitbucket.org/starkat
.. _Manuel Jacob: https://github.com/manueljacob
.. _Marcus Brinkmann: https://bitbucket.org/lambdafu/
.. _Max Liebkies: https://bitbucket.org/gegenschall
.. _Paul Houle: https://github.com/paulhoule
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

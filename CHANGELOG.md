# Change Log

&#7ADC; **TatSu** uses [Semantic Versioning][] for its releases, so parts of the version number may increase without any significant changes or backwards incompatibilities in the software.

The format of this *Change Log* is inspired by [keeapachangelog.org][].

## [X.Y.Z][] @ 2017
[X.Y.Z]: https://github.com/apalala/tatsu/compare/v4.0.0...master

### Added

-   New support for _left recursion_ with correct associativity. All test cases pass.

-   Left recursion is enabled by default. Use the `@@left_recursion :: False` directive to diasable it.

-   Renamed the decorator for generated rule methods to `@tatsumasu`.

-   Refactored the `tatsu.contexts.ParseContext` for clarity.

-   The `@@ignorecase` directive and the `ignorecase=` parameter no longer appy to regular expressions (patterns) in grammars. Use `(?i)` in the pattern to ignore the case in a particular pattern.

-   Now `tatsu.g2e` is a library and executable module for translating [ANTLR][] grammars to **TatSu**.

## [4.0.0][] @ 2017-05-06
[4.0.0]: https://github.com/apalala/tatsu/compare/0.0.0...v4.0.0

-   First release.

[ANTLR]: http://www.antlr.org
[AST]: http://en.wikipedia.org/wiki/Abstract_syntax_tree
[ASTs]: http://en.wikipedia.org/wiki/Abstract_syntax_tree
[Abstract Syntax Tree]: http://en.wikipedia.org/wiki/Abstract_syntax_tree
[BSD]: http://en.wikipedia.org/wiki/BSD_licenses
[COBOL]: http://en.wikipedia.org/wiki/Cobol
[CST]:  http://en.wikipedia.org/wiki/Concrete_syntax_tree
[Cyclomatic complexity]: http://en.wikipedia.org/wiki/Cyclomatic_complexity
[Cython]: http://cython.org/
[EBNF]: http://en.wikipedia.org/wiki/Ebnf
[JSON]: http://www.json.org/
[Java]:  http://en.wikipedia.org/wiki/Java_(programming_language)
[KLOC]: http://en.wikipedia.org/wiki/KLOC
[NATURAL]: http://en.wikipedia.org/wiki/NATURAL
[PEG]: http://en.wikipedia.org/wiki/Parsing_expression_grammar
[PLY]: http://www.dabeaz.com/ply/ply.html#ply_nn22
[POSIX]: https://en.wikipedia.org/wiki/POSIX
[Packrat]: http://bford.info/packrat/
[Perl]: http://www.perl.org/
[PyPi]: http://pypi.org/
[PyPy]: http://pypy.org/
[Python]: http://python.org
[Ruby]: http://www.ruby-lang.org/
[Semantic Versioning]: http://semver.org/
[Sublime Text]: https://www.sublimetext.com
[Travis CI]: https://travis-ci.org
[VB6]: http://en.wikipedia.org/wiki/Visual_basic_6
[Vim spell]: http://vimdoc.sourceforge.net/htmldoc/spell.html
[Visitor Pattern]: http://en.wikipedia.org/wiki/Visitor_pattern
[Warth et al]: http://www.vpri.org/pdf/tr2007002_packrat.pdf
[YAML]: https://en.wikipedia.org/wiki/YAML
[colorama]: https://pypi.python.org/pypi/colorama/
[context managers]: http://docs.python.org/2/library/contextlib.html
[email]: mailto:apalala@gmail.com
[flake8]: https://pypi.python.org/pypi/flake8
[keeapachangelog.org]: http://keepachangelog.com/
[keywords]: https://en.wikipedia.org/wiki/Reserved_word
[legacy code]: http://en.wikipedia.org/wiki/Legacy_code
[legacy]: http://en.wikipedia.org/wiki/Legacy_code
[memoizing]: http://en.wikipedia.org/wiki/Memoization
[pygraphviz]: https://pypi.python.org/pypi/pygraphviz
[pytest]: https://pypi.org/project/pytest/
[raw string literal]: https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals
[re]: https://docs.python.org/3.4/library/re.html
[regex]: https://pypi.python.org/pypi/regex
[string literal]: https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals
[tox]: https://testrun.org/tox/latest/

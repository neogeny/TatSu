.. Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
.. SPDX-License-Identifier: BSD-4-Clause

.. include:: links.rst
.. highlight:: none

Parser Configuration
--------------------

|TatSu| has many configuration options. They are all defined in
``tatsu.parserconfig.ParserConfig``. With the introduction of ``ParserConfig``
there's no need to declare every configuration parameter as an optional named
argument in entry points and internal methods.

The defaults set in ``ParserConfig`` are suitable for most cases, and they are
easy to override.

Entry points still accept configuration options as named keyword arguments, but
those are gathered in ``**settings`` (aka ``**kwargs``) argument for a``ParserConfig``
to validate when called.

.. code:: python

    @dataclass
    class ParserConfig:
        name: str | None = 'Test'
        filename: str = ''

        start: str | None = None

        tokenizercls: type[Tokenizer] | None = None
        semantics: type | None = None

        comment_recovery: bool = False   # warning: not implemented

        memoization: bool = True
        memoize_lookaheads: bool = True
        memo_cache_size: int = MEMO_CACHE_SIZE

        colorize: bool = True  # INFO: requires the colorama library
        trace: bool = False
        trace_filename: bool = False
        trace_length: int = 72
        trace_separator: str = C_DERIVE

        grammar: str | None = None
        left_recursion: bool = True

        comments: str | None = None
        eol_comments: str | None = None
        keywords: Collection[str] = field(default_factory=set)

        ignorecase: bool | None = False
        namechars: str = ''
        nameguard: bool | None = None  # implied by namechars
        whitespace: str | None = undefined

        parseinfo: bool = False

Entry points and internal methods in |TatSu| have an optional
``config: ParserConfig | None = None`` argument.

.. code:: Python

    def parse(
        grammar,
        input,
        start=None,
        name=None,
        semantics=None,
        asmodel=False,
        config: ParserConfig | None = None,
        **settings,
    ):

If no ``ParserConfig`` is passed, a default one is created. Configuration
attributes may be overridden by relevant arguments in ``**settings``.

These are different ways to apply a configuration setting:

.. code:: Python

    config = tatsu.parserconfig.ParserConfig()
    config.left_recursion = False
    ast = tatsu.parse(grammar, text, config=config)

    config = tatsu.parserconfig.ParserConfig(left_recursion=False)
    ast = tatsu.parse(grammar, text, config=config)

    ast = tatsu.parse(grammar, text, left_recursion=False)


name
~~~~
.. code:: Python

    name: str | None = 'Test'

The name of the grammar. It's used in generated Python parsers and may be
used in error reporting.


filename
~~~~~~~~

.. code:: Python

    filename: str = ''

The file name from which the grammar was read. It may be used in error reporting.


start
~~~~~

.. code:: Python

    start: str | None = None

The name of the rule on which to start parsing. It may be used to invoke
only a specific part of the parser.

.. code:: Python

    ast = parse(grammar, '(2+2)*2', start='expression')


tokenizercls
~~~~~~~~~~~~

.. code:: Python

    tokenizercls: type[Tokenizer] | None = None

The class that implements tokenization for the parser. If it's not defined
then the parsing modules will default to ``buffering.Buffer``.

This option was applied in the prototype PEG parser for Python to be
able to reuse the native Python tokenizer.


semantics
~~~~~~~~~

.. code:: Python

    semantics: type | None = None

The class implementing parser semantics. See other sections of the
documentation for meaning, implementation and default and generated
semantic classes and objects.

memoization
~~~~~~~~~~~

.. code:: Python

    memoization: bool = True

Enable or disable memoization in the parser. Only specific input languages
require this to be ``False``.


memoize_lookaheads
~~~~~~~~~~~~~~~~~~

.. code:: Python

    memoize_lookaheads: bool = True

Enables or disables memoization for lookaheads. Only specific input languages
require this to be ``False``.

memo_cache_size
~~~~~~~~~~~~~~~

.. code:: Python

    memo_cache_size: int = MEMO_CACHE_SIZE

The size of the cache for memos. As parsing progresses, previous memos
are seldom needed, so there's a bound to the number of memos saved
(currently 1024).

colorize
~~~~~~~~

.. code:: Python

    colorize: bool = True

Colorize trace output. Colorization requires that the ``colorama`` library
is available.

trace
~~~~~

.. code:: Python

    trace: bool = False

Produce a trace of the parsing process. See the `Traces <traces.html>`_
section for more information.


trace_filename
~~~~~~~~~~~~~~

.. code:: Python

    trace_filename: bool = False

Include the input text's filename in trace output.

trace_length
~~~~~~~~~~~~

.. code:: Python

    trace_length: int = 72

The max width of a line in a trace.

trace_separator
~~~~~~~~~~~~~~~

.. code:: Python

    trace_separator: str = C_DERIVE

The separator to use between lines in a trace.

grammar
~~~~~~~

.. code:: Python

    grammar: str | None = None

An alias for the `name <#name>`_ option.

left_recursion
~~~~~~~~~~~~~~

.. code:: Python

    left_recursion: bool = True

Enable or disable left recursion in analysis and parsing.

comments
~~~~~~~~

.. code:: Python

    comments: str | None = None

A regular expression describing comments in the input. Comments are skipped
during parsing.

eol_comments
~~~~~~~~~~~~

.. code:: Python

    eol_comments: str | None = None

A regular expression describing end-of-line comments in the input.
Comments are skipped during parsing.


keywords
~~~~~~~~

.. code:: Python

    keywords: Collection[str] = field(default_factory=set)

The list of keywords in the input language. See
`Reserved Words and Keywords <syntax.html#reserved-words-and-keywords>`_
for more information.

ignorecase
~~~~~~~~~~

.. code:: Python

    ignorecase: bool | None = False

namechars
~~~~~~~~~

.. code:: Python

    namechars: str = ''

Additional characters that can be part of an identifier
(for example ``namechars='$@'``').

nameguard
~~~~~~~~~

.. code:: Python

    nameguard: bool = False  # implied by namechars

When set to ``True``, avoids matching tokens when the next character in the input sequence is
alphanumeric or a ``@@namechar``. Defaults to ``False``.
See `token expression <syntax.html#text-or-text>`_ for an explanation.

whitespace
~~~~~~~~~~

.. code:: Python

    whitespace: str | None = undefined

Provides a regular expression for the whitespace to be ignored by the parser.
See the `@@whitespace <directives.html#whitespace-regexp>`_ section for more
information.


parseinfo
~~~~~~~~~

.. code:: Python

    parseinfo: bool = False

When ``parseinfo==True``, a ``parseinfo`` entry is added to `AST`_ nodes
that are dict-like. The entry provides information about what was parsed and
where. See `Abstract Syntax Trees <ast.html>`_ for more information.


.. code:: Python

    class ParseInfo(NamedTuple):
        tokenizer: Any
        rule: str
        pos: int
        endpos: int
        line: int
        endline: int
        alerts: list[Alert] = []  # noqa: RUF012

        def text_lines(self):
            return self.tokenizer.get_lines(self.line, self.endline)

        def line_index(self):
            return self.tokenizer.line_index(self.line, self.endline)

        @property
        def buffer(self):
            return self.tokenizer


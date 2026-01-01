.. include:: links.rst
.. highlight:: none

Parser Configuration
--------------------

|TatSu| has many configuration options. They are all defined in
``tatsu.config.ParserConfig``. With the introduction of ``ParserConfig``
there's no need to declare every configuration parameter as an optional named
argument in entry points and internal methods. The defaults set in
``ParserConfig`` are suitable for most cases, and they are easy to override.

.. code:: python

    @dataclass
    class ParserConfig:
        name: str | None = 'Test'
        filename: str = ''
        encoding: str = 'utf-8'

        start: str | None = None  # FIXME
        start_rule: str | None = None  # FIXME
        rule_name: str | None = None  # Backward compatibility

        comments_re: re.Pattern | str | None = None  # WARNING: deprecated
        eol_comments_re: re.Pattern | str | None = None  # WARNING: deprecated

        tokenizercls: type[Tokenizer] | None = None  # FIXME
        semantics: type | None = None

        comment_recovery: bool = False   # warning: not implemented

        memoization: bool = True
        memoize_lookaheads: bool = True
        memo_cache_size: int = MEMO_CACHE_SIZE

        colorize: bool = False  # INFO: requires the colorama library
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
        nameguard: bool = False  # implied by namechars
        whitespace: str | None = _undefined_str

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

These are several ways to apply a configuration setting:

.. code:: Python

    config = tatsu.config.ParserConfig()
    config.left_recursion = False
    ast = tatsu.parse(grammar, text, config=config)

    config = tatsu.config.ParserConfig(left_recursion=False)
    ast = tatsu.parse(grammar, text, config=config)

    ast = tatsu.parse(grammar, text, left_recursion=False)


name
~~~~
.. code:: Python

    name: str | None = 'Test'

filename
~~~~~~~~

.. code:: Python

    filename: str = ''

encoding
~~~~~~~~

.. code:: Python

    encoding: str = 'utf-8'

start
~~~~~

.. code:: Python

    start: str | None = None  # FIXME


tokenizercls
~~~~~~~~~~~~

.. code:: Python

    tokenizercls: type[Tokenizer] | None = None  # FIXME


semantics
~~~~~~~~~

.. code:: Python

    semantics: type | None = None

memoization
~~~~~~~~~~~

.. code:: Python

    memoization: bool = True


memoize_lookaheads
~~~~~~~~~~~~~~~~~~

.. code:: Python

    memoize_lookaheads: bool = True

memo_cache_size
~~~~~~~~~~~~~~~

.. code:: Python

    memo_cache_size: int = MEMO_CACHE_SIZE

colorize
~~~~~~~~

.. code:: Python

    colorize: bool = False

trace
~~~~~

.. code:: Python

    trace: bool = False


trace_filename
~~~~~~~~~~~~~~

.. code:: Python

    trace_filename: bool = False

trace_length
~~~~~~~~~~~~

.. code:: Python

    trace_length: int = 72

trace_separator
~~~~~~~~~~~~~~~

.. code:: Python

    trace_separator: str = C_DERIVE

grammar
~~~~~~~

.. code:: Python

    grammar: str | None = None

left_recursion
~~~~~~~~~~~~~~

.. code:: Python

    left_recursion: bool = True

comments
~~~~~~~~

.. code:: Python

    comments: str | None = None

eol_comments
~~~~~~~~~~~~

.. code:: Python

    eol_comments: str | None = None

keywords
~~~~~~~~

.. code:: Python

    keywords: Collection[str] = field(default_factory=set)

ignorecase
~~~~~~~~~~

.. code:: Python

    ignorecase: bool | None = False

namechars
~~~~~~~~~

.. code:: Python

    namechars: str = ''

nameguard
~~~~~~~~~

.. code:: Python

    nameguard: bool = False  # implied by namechars

whitespace
~~~~~~~~~~

.. code:: Python

    whitespace: str | None = _undefined_str

parseinfo
~~~~~~~~~

.. code:: Python

    parseinfo: bool = False

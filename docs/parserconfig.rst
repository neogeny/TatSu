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

        comments_re: re.Pattern | str | None = None
        eol_comments_re: re.Pattern | str | None = None

        tokenizercls: type[Tokenizer] | None = None  # FIXME
        semantics: type | None = None

        comment_recovery: bool = False

        memoization: bool = True
        memoize_lookaheads: bool = True
        memo_cache_size: int = MEMO_CACHE_SIZE

        colorize: bool = False
        trace: bool = False
        trace_filename: bool = False
        trace_length: int = 72
        trace_separator: str = C_DERIVE

        grammar: str | None = None
        left_recursion: bool = True

        comments: str | None = None
        eol_comments: str | None = None
        keywords: Collection[str] = field(default_factory=list)

        ignorecase: bool | None = False
        namechars: str = ''
        nameguard: bool | None = None  # implied by namechars
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

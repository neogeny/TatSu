from __future__ import annotations

from tatsu.grammars import Grammar

from .config import DEFAULT_PYGMENTS_STYLE, CLIConfig


def colorize_output(
    payload: str,
    language: str,
    style: str = DEFAULT_PYGMENTS_STYLE,
) -> str:
    from pygments import highlight
    from pygments.formatters import Terminal256Formatter
    from pygments.lexers import get_lexer_by_name

    lexer = get_lexer_by_name(language)
    fmt = Terminal256Formatter(style=style)
    return highlight(payload, lexer, fmt)


def render_grammar(
    gram: Grammar,
    cfg: CLIConfig,
    *,
    name: str | None = None,
) -> str:
    """Render a Grammar in the selected mode.

    Sets *name* to the output basename (without extension) when -o is a directory.
    """
    if cfg.optimized:
        gram = gram.optimized()

    _ = name
    if cfg.model:
        payload = repr(gram)
    elif cfg.railroads:
        payload = gram.railroads()
    elif cfg.pretty:
        payload = gram.pretty()
    else:
        payload = gram.asjsons()
    return payload

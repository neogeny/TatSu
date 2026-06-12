from __future__ import annotations

from .config import DEFAULT_PYGMENTS_STYLE


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

from __future__ import annotations

import os
import sys

from tatsu.tool.cling.config import DEFAULT_PYGMENTS_STYLE, CLIConfig


def _should_colorize(cfg: CLIConfig) -> bool:
    if cfg.color == "always":
        return True
    if cfg.color == "never":
        return False
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _colorize(
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

from __future__ import annotations

from tatsu.grammars import Grammar
from tatsu.ngcodegen import modelgen, parsergen, pythongen

from .cfg import DEFAULT_PYGMENTS_STYLE, CLIConfig


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
    model: Grammar,
    cfg: CLIConfig,
    *,
    name: str | None = None,
) -> str:
    """Render a Grammar in the selected mode.

    Sets *name* to the output basename (without extension) when -o is a directory.
    """
    if cfg.optimized:
        model = model.optimized()

    _ = name
    if cfg.model:
        result = repr(model)
    elif cfg.railroads:
        result = model.railroads()
    elif cfg.pretty:
        result = model.pretty()
    elif cfg.pretty_lean:
        result = model.pretty_lean()
    elif cfg.object_model:
        result = modelgen(model)
    elif cfg.parser_model:
        result = parsergen(model)
    elif cfg.generage_parser:
        result = pythongen(model)
    else:
        result = model.asjsons()
    return result

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any

from ...ngcodegen import modelgen, parsergen, pythongen
from ...peg import Grammar
from ...util.asjson import asjsons
from ...util.checkpygments import is_pygments_available
from .cfg import DEFAULT_PYGMENTS_STYLE, CLIConfig


def format_result(cfg: CLIConfig, result: Any) -> str:
    if cfg.model:
        return repr(result)
    return asjsons(result)


def colorize_output(
    payload: str,
    language: str,
    style: str = DEFAULT_PYGMENTS_STYLE,
) -> str:
    if not is_pygments_available():
        return payload

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
    if cfg.generate_parser:
        result = pythongen(model, parser_name=cfg.name)
    elif cfg.model:
        result = repr(model)
    elif cfg.railroads:
        result = model.railroads()
    elif cfg.pretty:
        result = model.pretty()
    elif cfg.pretty_lean:
        result = model.pretty_lean()
    elif cfg.object_model:
        result = modelgen(model, name=cfg.name)
    elif cfg.parser_model:
        result = parsergen(model, name=cfg.name)
    else:
        result = model.asjsons()
    return result

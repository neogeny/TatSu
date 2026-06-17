# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from pathlib import Path
from typing import Any

from tatsu.grammars import Grammar
from tatsu.tool.cling.config import CLIError


type Results = list[tuple[str, Any]]


def load_grammar(path: str | Path) -> Grammar:
    """Load a Grammar from an .ebnf or .json file."""

    p = Path(path)
    try:
        source = p.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise CLIError(str(e)) from e
    if p.suffix == ".json":
        return Grammar.loads(source)
    from ..api import compile

    return compile(source)

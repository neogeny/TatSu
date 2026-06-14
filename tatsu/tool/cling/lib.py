# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from pathlib import Path
from typing import Any

from tatsu.grammars.model import Grammar


type Results = list[tuple[str, Any]]


def load_grammar(path: str | Path) -> Grammar:
    """Load a Grammar from an .ebnf or .json file."""
    from ...grammars.model import Grammar as _Grammar

    p = Path(path)
    source = p.read_text(encoding="utf-8")
    if p.suffix == ".json":
        return _Grammar.loads(source)
    from ..api import compile

    return compile(source)

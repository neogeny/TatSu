# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from ...grammars.model import Grammar


type Results = list[tuple[str, Any]]


@dataclass
class CLIConfig:
    """Parsed command-line configuration, matching ogopego's CLIConfig struct."""

    # Global flags
    color: str = "auto"
    output: str = ""
    trace: bool = False
    quiet: bool = False
    profile: bool = False

    # Subcommand state
    command: str = ""
    path: str = ""
    inputs: list[str] = field(default_factory=list)

    # format flags
    json: bool = False
    model: bool = False
    pretty: bool = False
    railroads: bool = False

    # run flags
    start: str = ""
    nproc: int = 0


def _load_grammar(path: str) -> Grammar:
    """Load a Grammar from an .ebnf or .json file."""
    from ...grammars.model import Grammar as _Grammar

    p = Path(path)
    source = p.read_text(encoding="utf-8")
    if p.suffix == ".json":
        return _Grammar.loads(source)
    from ..api import compile

    return compile(source)

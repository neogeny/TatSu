# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from pathlib import Path
from typing import Any

from tatsu.config import ParserConfig
from tatsu.util.asjson import asjsons
from tatsu.util.heart import NullHeart

from .lib import CLIConfig, Results, _load_grammar


def _format_result(cfg: CLIConfig, result: Any) -> str:
    """Format a parse result as a string."""
    if cfg.json:
        return asjsons(result)
    if cfg.model:
        return repr(result)
    return f"{result!s}"


def run_cmd(cfg: CLIConfig) -> Results:
    """Handle the ``run`` subcommand."""
    from ...util.parproc import parproc_visual

    grammar = _load_grammar(cfg.path)
    start = cfg.start or None

    results: list[tuple[str, Any]] = []
    if len(cfg.inputs) == 1:
        path = cfg.inputs[0]
        text = Path(path).read_text(encoding="utf-8")
        result = grammar.parse(text, start=start)
        results.append((path, result))
    else:
        config = ParserConfig.new()
        config.heart = NullHeart()

        def parse_file(path: str) -> Any:
            text = Path(path).read_text(encoding="utf-8")
            return grammar.parse(text, start=start)

        results += [
            (r.payload, _format_result(cfg, r.outcome))
            for r in parproc_visual(
                parse_file,
                cfg.inputs,
                parallel=cfg.nproc > 0,
            )
        ]
    return results

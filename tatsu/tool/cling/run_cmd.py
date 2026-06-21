# Copyright © 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...config import ParserConfig
from ...peg import Grammar
from ...util.bars import BarRow, Col, Multi
from ...util.heart import Heart
from ...util.parproc import VisualPayload, parproc_visual
from ...util.ztyle import Style
from .cfg import CLIConfig
from .lib import Results, load_grammar
from .sum import format_result, show_summary


class FileHeartRow(BarRow, Heart):
    def __init__(self, name: str, total: int) -> None:
        s = Style()
        white = s.white()
        green = s.green()
        dim = s.black().bold()

        super().__init__(
            cols=[f"   {white(name):<60} ", Col.bar],
            fill="⎯⎯⎯",
            style=[green, green, dim],
            label=name,
            total=total,
            stop_on_complete=False,
        )

    def start(self) -> None:
        super().start()

    def beat(self, mark: int, total: int) -> None:
        self.update(mark, total)

    def dead(self) -> bool:
        return False


@dataclass(slots=True)
class GrammarPayload(VisualPayload):
    grammar: Grammar
    start: str
    heart: FileHeartRow
    idx: int


def run_cmd(cfg: CLIConfig) -> Results:
    start_time = time.time()

    if not cfg.grammar:
        raise ValueError("No grammar specified")

    grammarpath = Path(cfg.grammar)
    grammar = load_grammar(grammarpath)
    start = cfg.start or None

    return run_with_progress(start_time, grammar, start, cfg)


def run_with_progress(
    start_time: float,
    grammar: Any,
    start: str | None,
    cfg: CLIConfig,
) -> Results:
    inputs = cfg.inputs
    multi = Multi([], out=sys.stderr)

    name = Path(cfg.grammar).name
    total = len(inputs)

    s = Style()
    yellow = s.yellow()
    top_row = BarRow(
        label=name,
        cols=[Col.bar],
        fill="--.",
        style=[yellow, yellow, s],
        total=total,
    )
    multi.add_row(top_row)

    paths = [Path(input) for input in inputs]
    payloads = []
    for idx, path in enumerate(paths):
        text = path.read_text()
        fh = FileHeartRow(path.name, len(text))
        payloads.append(
            GrammarPayload(
                path,
                text,
                grammar=grammar,
                start=start or "",
                heart=fh,
                idx=idx,
            )
        )

    def parse_file_task(data: GrammarPayload) -> Any:
        path = Path(data.path)
        text = data.payload
        grammar, start = data.grammar, data.start

        config = ParserConfig.new()
        heart = data.heart
        config.heart = heart

        relpath = path.absolute().relative_to(Path().absolute())
        config.source = str(relpath)

        multi.add_row(heart)
        heart.start()
        heart.update(0, len(text))
        sys.setrecursionlimit(2**16)
        try:
            return grammar.parse(text, start=start, config=config)
        finally:
            heart.update(len(text), len(text))
            heart.stop()

    multi.start()
    top_row.start()
    try:
        results = parproc_visual(
            parse_file_task,
            payloads,
            top_row,
            parallel=True,
            reraise=False,
            summary=False,
            max_workers=cfg.nproc,
        )
        if cfg.summary or not cfg.quiet:
            results = show_summary(cfg, start_time, results, multi)
        joined = list(results)
    finally:
        multi.stop()

    return [
        (
            str(r.payload.path),
            format_result(cfg, r.outcome),
        )
        for r in joined
    ]

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
from ...util.bars import Bar, BarRow, Fill, Multi
from ...util.heart import Heart
from ...util.parproc import VisualPayload, parproc_visual
from .cfg import CLIConfig
from .global_opt import add_global_options
from .lib import Results, load_grammar
from .sum import format_result, show_summary


class HeartBar(Heart, Bar):
    def __init__(self, fill: Fill) -> None:
        super().__init__(fill=fill)
        self.stopped = False

    def beat(self, mark: int, total: int) -> None:
        self.update(mark, total)

    def dead(self) -> bool:
        return self.stopped

    def stop(self) -> None:
        self.stopped = True


class FileHeartRow(BarRow, Heart):
    def __init__(self, name: str, total: int) -> None:
        from ...util.style import Style

        _bold_white = Style().bold().white()
        _green = Style().green()
        fill = (
            _green("-"),
            _green("-"),
            Style("-").white().dim(),
        )
        bar = HeartBar(fill=fill)
        super().__init__(
            cols=[f" {_bold_white(name):<50} ", bar],
            fill=fill,
            bar=bar,
            label=name,
            total=total,
        )
        self.stotal_on_complete = False

        self.update(0, total)

    def beat(self, mark: int, total: int) -> None:
        self.update(mark, total)

    def dead(self) -> bool:
        return self.stopped

    def stop(self) -> None:
        super().stop()
        if isinstance(self.bar, HeartBar):
            self.bar.stop()


@dataclass(slots=True)
class GrammarPayload(VisualPayload):
    grammar: Grammar
    start: str
    heart: FileHeartRow


def parse_file_task(payload: GrammarPayload) -> Any:
    path = Path(payload.path)
    text = payload.payload
    grammar, start = payload.grammar, payload.start

    config = ParserConfig.new()
    heart = payload.heart
    config.heart = heart

    relpath = path.absolute().relative_to(Path().absolute())
    config.source = str(relpath)

    try:
        return grammar.parse(text, start=start, config=config)
    finally:
        heart.stop()


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
    from ...util.style import Style

    _yellow = Style().yellow()

    multi = Multi([], out=sys.stderr)

    name = Path(cfg.grammar).name
    total = len(cfg.inputs)
    bar = Bar(fill=(_yellow("-"), _yellow("-"), "."))
    top_row = BarRow(
        label=name,
        bar=bar,
        cols=[bar],
        total=total,
    )
    multi.add_row(top_row)

    paths = [Path(input) for input in cfg.inputs]
    payloads = []
    for path in paths:
        text = path.read_text()
        fh = FileHeartRow(path.name, len(text))
        multi.add_row(fh)
        payloads.append(
            GrammarPayload(
                path,
                text,
                grammar=grammar,
                start=start or "",
                heart=fh,
            )
        )
    multi.start()
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

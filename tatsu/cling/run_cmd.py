# Copyright © 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tatsu.barz.broker import BarBroker

from .. import packetz
from ..barz import BarRow, Col, Multi
from ..config import ParserConfig
from ..exceptions import FailedParse
from ..parproc import (
    Result,
    VisualPayload,
    parproc,
)
from ..parproc.summary import show_result, show_summary
from ..peg import Grammar
from ..util.heart import Heart
from ..ztyle import Style
from .cfg import CLIConfig
from .fmt import format_result
from .lib import Results, load_grammar


class FileHeartRow(BarRow, Heart):
    def __init__(self, queue: packetz.PacketzQueue, name: str, total: int) -> None:
        self.queue = queue
        s = Style()
        white = s.bright_white().bold()
        green = s.green()
        dim = s.black().bold()

        super().__init__(
            cols=[f"   {white(name):<60} ", Col.bar, " " * 12],
            fill="⎯⎯⎯",
            style=[green, green, dim],
            label=name,
            total=total,
            selfstop=False,
        )

    def start(self) -> None:
        super().start()

    def beat(self, mark: int, total: int) -> None:
        self.start()
        self.update(mark, total)
        self.queue.send(data=self)

    def dead(self) -> bool:
        return False


@dataclass(slots=True)
class GrammarPayload(VisualPayload):
    grammar: Grammar
    start: str
    heart: FileHeartRow
    idx: int

    def raises(self) -> tuple[type[Exception], ...]:
        return (RecursionError, FailedParse)


def run_cmd(cfg: CLIConfig) -> Results:
    start_time = time.time()

    if not cfg.grammar:
        raise ValueError("No grammar specified")

    grammarpath = Path(cfg.grammar)
    grammar = load_grammar(grammarpath)
    start = cfg.start or None

    return run_with_progress(start_time, grammar, start, cfg)


def parse_file_task(data: GrammarPayload, *_args, **_kwargs) -> Any:
    path = Path(data.path)
    text = data.payload
    grammar, start = data.grammar, data.start

    config = ParserConfig.new()
    heart = data.heart
    config.heart = heart

    relpath = path.absolute().relative_to(Path().absolute())
    config.source = str(relpath)

    heart.start()
    sys.setrecursionlimit(2**16)
    try:
        return grammar.parse(text, start=start, config=config)
    except RecursionError as e:
        return e
    finally:
        heart.beat(mark=len(text), total=len(text))
        heart.stop()


def run_with_progress(
    start_time: float,
    grammar: Any,
    start: str | None,
    cfg: CLIConfig,
) -> Results:
    inputs = cfg.inputs

    name = Path(cfg.grammar).name
    total = len(inputs)

    multi = Multi([], out=sys.stderr)
    broker = BarBroker(multi)

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
    top_row.start()

    paths = [Path(input) for input in inputs]
    payloads = []
    filehearts: dict[str, FileHeartRow] = {}
    for idx, path in enumerate(paths):
        text = path.read_text()
        fh = FileHeartRow(broker.queue, path.name, len(text))
        multi.add_row(fh)
        payloads.append(
            GrammarPayload(
                path,
                text,
                grammar=grammar,  # ty: ignore
                start=start or "",
                heart=fh,
                idx=idx,
            )
        )
        filehearts[fh.id] = fh

    try:
        results = parproc(
            parse_file_task,
            payloads,
            top_row,
            parallel=True,
            reraise=False,
            # WARNING we do the summary in-process
            summary=False,
            verbose=False,
            max_workers=cfg.nproc,
        )

        def show_results(results: Iterable[Result]) -> Iterable[Result]:
            count = 0
            last = None
            for r in results:
                yield r
                count += 1  # noqa: SIM113
                top_row.update(pos=count, total=total)
                if last:
                    show_result(multi.print, last, cfg.usecolor)
                last = r
            if last:
                show_result(multi.print, last, cfg.usecolor)

        if not cfg.quiet or cfg.summary:
            broker.start()

        results = show_results(results)
        if cfg.summary or cfg.verbose or not cfg.quiet:
            results = show_summary(
                start_time,
                results,
                eprint=multi.print,
                usecolor=cfg.usecolor,
                verbose=cfg.verbose,
            )
        joined = list(results)
    finally:
        multi.stop()

    return [
        (
            str(r.payload.path),
            format_result(cfg, r.outcome),
        )
        for r in joined
        if not r.exception
    ]

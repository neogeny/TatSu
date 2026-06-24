# Copyright © 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, assert_never

from ... import packetz
from ...barz import BarRow, Col, Multi
from ...config import ParserConfig
from ...exceptions import FailedParse
from ...packetz import (
    PacketLike,
)
from ...parproc import (
    Result,
    VisualPayload,
    parproc_visual,
    show_summary,
)
from ...peg import Grammar
from ...util.heart import Heart
from ...ztyle import Style
from .cfg import CLIConfig
from .fmt import format_result
from .lib import Results, load_grammar


# GLOBAL
multi = Multi([], out=sys.stderr)


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
        packetz.send(data=self)

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


def parse_file_task(data: GrammarPayload) -> Any:
    path = Path(data.path)
    text = data.payload
    grammar, start = data.grammar, data.start

    config = ParserConfig.new()
    heart = data.heart
    config.heart = heart

    relpath = path.absolute().relative_to(Path().absolute())
    config.source = str(relpath)

    heart.start()
    heart.update(pos=0, total=len(text))
    sys.setrecursionlimit(2**16)
    try:
        return grammar.parse(text, start=start, config=config)
    except RecursionError as e:
        return e
    finally:
        heart.update(pos=len(text), total=len(text))
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
    filehearts: dict[str, FileHeartRow] = {}
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
        filehearts[fh.id] = fh

    if not cfg.quiet or cfg.summary:
        multi.start()
    if not cfg.quiet:
        top_row.start()

    def filter_to_results(values: Iterable[Any]) -> Iterable[Result]:
        for value in values:
            if value is None:
                continue
            match value:
                case Result() as result:
                    row = filehearts[result.payload.heart.id]
                    row.stop()
                    yield result
                case PacketLike(data=FileHeartRow() as row_packet):
                    row = filehearts[row_packet.id]
                    row.update(**row_packet.snap())
                    if row.is_active():
                        multi.add_row(row)
                case _:
                    assert_never(value)  # ty: ignore

    try:
        values = parproc_visual(
            parse_file_task,
            payloads,
            top_row,
            parallel=True,
            reraise=False,
            # WARNING We can't pass an eprint function if multiproc is chosen
            eprint=multi.print,
            # WARNING we do the summary in-process
            summary=False,
            verbose=False,
            max_workers=cfg.nproc,
        )
        results = filter_to_results(values)
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

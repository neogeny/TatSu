# Copyright © 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.progress import Progress

from tatsu.grammars import Grammar
from tatsu.util.heart import Heart
from tatsu.util.parproc import VisualPayload

from ...config import ParserConfig
from ...util.parproc import ProgressPair, parproc_visual
from ...util.richtest import is_rich_library_available
from .config import CLIConfig
from .lib import Results, load_grammar
from .sum import Printer, format_result, show_summary


class ProgressHeartProtocol(Heart):
    def finish(self) -> None:
        pass


@dataclass(slots=True)
class GrammarPayload(VisualPayload):
    grammar: Grammar
    start: str
    new_fileheart: Callable[[str, int], ProgressHeartProtocol]
    heart: ProgressHeartProtocol | None = None


def parse_file_task(payload: GrammarPayload) -> Any:
    path = Path(payload.path)
    text = payload.payload
    grammar, start, new_fileheart = (
        payload.grammar,
        payload.start,
        payload.new_fileheart,
    )

    config = ParserConfig.new()

    heart = new_fileheart(path.name, len(text))
    payload.heart = heart
    config.heart = heart

    relpath = path.absolute().relative_to(Path().absolute())
    config.source = str(relpath)

    try:
        return grammar.parse(text, start=start, config=config)
    finally:
        heart.finish()


def make_new_fileheart(task_progress) -> Callable[[str, int], ProgressHeartProtocol]:

    def new_fileheart(
        name: str, size: int, task_progress=task_progress
    ) -> ProgressHeartProtocol:

        class ProgressHeart(ProgressHeartProtocol):
            def __init__(self, name: str, total: int, task_progress) -> None:
                self._name = name
                self.task = task_progress.add_task(f"  {self._name}", total=total)
                self.beat(0, total)
                self.stopped = False

            @property
            def name(self) -> str:
                return f'{self._name:40} '

            def beat(self, mark: int, total: int) -> None:
                if total == 0:
                    return
                task_progress.update(
                    self.task,
                    completed=mark,
                    total=total,
                    color="green",
                    description=f"  [bold white]{self.name}[green][/]",
                )

            def dead(self) -> bool:
                return self.stopped

            def finish(self) -> None:
                task_progress.remove_task(self.task)

        return ProgressHeart(name=name, total=size, task_progress=task_progress)

    return new_fileheart


def run_cmd(cfg: CLIConfig) -> Results:
    start_time = time.time()

    if not cfg.grammar:
        raise ValueError("No grammar specified")

    grammarpath = Path(cfg.grammar)
    grammar = load_grammar(grammarpath)
    start = cfg.start or None

    if len(cfg.inputs) == 1:
        input = cfg.inputs[0]
        text = Path(input).read_text(encoding="utf-8")
        result = grammar.parse(text, start=start)
        return [(input, format_result(cfg, result))]

    if is_rich_library_available() and not cfg.quiet:
        return run_with_progress(start_time, grammar, start, cfg)
    else:
        return run_without_progress(grammar, start, cfg)


def run_without_progress(
    grammar: Any,
    start: str | None,
    cfg: CLIConfig,
) -> Results:
    from ...util.parproc import parproc

    config = ParserConfig.new()

    def parse_single_file(path: str) -> Any:
        text = Path(path).read_text(encoding="utf-8")
        return grammar.parse(text, start=start, config=config)

    parallel = cfg.nproc is None or cfg.nproc > 0
    return [
        (r.payload, format_result(cfg, r.outcome))
        for r in parproc(parse_single_file, cfg.inputs, parallel=parallel)
        if r is not None and r.outcome is not None and r.exception is None
    ]


def run_with_progress(
    start_time: float,
    grammar: Any,
    start: str | None,
    cfg: CLIConfig,
) -> Results:
    from rich.progress import (  # pyright: ignore[reportMissingImports]
        BarColumn,
        TaskID,
        TextColumn,
    )
    from rich.table import Table

    class DualProgress(Progress, Printer):
        def __init__(self, *columns, **kwargs) -> None:
            super().__init__(*columns, transient=True, **kwargs)
            self._file_cols = [
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="green"),
                # TaskProgressColumn(style="green"),
            ]
            self._main_id: TaskID | None = None

        def set_main(self, tid: TaskID) -> None:
            self._main_id = tid

        def get_renderables(self):
            for task in self.tasks:
                if not task.visible:
                    continue
                columns = self.columns if task.id == self._main_id else self._file_cols
                table = Table.grid(padding=(0, 1))
                for _ in columns:
                    table.add_column(no_wrap=True)
                table.add_row(*(c.render(task) for c in columns))  # pyright: ignore[reportAttributeAccessIssue]
                yield table

    top_progress = DualProgress(
        # TaskProgressColumn(),
        # TimeElapsedColumn(),
        # TimeRemainingColumn(),
        # TextColumn("[name][progress.description]"),
        # TextColumn("[progress.description][task.description]"),
        BarColumn(
            bar_width=None,
            complete_style="yellow",
        ),
        refresh_per_second=1,
        speed_estimate_period=30.0,
    )
    task_progress = top_progress
    new_fileheart = make_new_fileheart(task_progress)

    name = Path(cfg.grammar).name
    total = len(cfg.inputs)
    toptask = top_progress.add_task(name, total=total)
    top_progress.set_main(toptask)

    def build_progressbar(_stotal: int) -> ProgressPair:
        return top_progress, toptask

    paths = [Path(input) for input in cfg.inputs]
    payloads = [
        GrammarPayload(
            path,
            path.read_text(),
            grammar=grammar,
            start=start or "",
            new_fileheart=new_fileheart,
        )
        for path in paths
    ]
    try:
        results = parproc_visual(
            parse_file_task,
            payloads,
            build_progressbar=build_progressbar,
            parallel=True,
            reraise=False,
            summary=False,
        )
        if not cfg.quiet:
            results = show_summary(cfg, start_time, top_progress, results)
    finally:
        print(file=sys.stderr)
        top_progress.stop()
        print(file=sys.stderr)

    return [(str(r.payload.path), format_result(cfg, r.outcome)) for r in results]

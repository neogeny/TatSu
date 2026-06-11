# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tatsu.util.strtools import countlines

from ...config import ParserConfig
from ...util.asjson import asjsons
from ...util.parproc import ProgressPair, parproc_visual
from ...util.richtest import is_rich_library_available
from .lib import CLIConfig, Results, _load_grammar


def _format_result(cfg: CLIConfig, result: Any) -> str:
    if cfg.json:
        return asjsons(result)
    if cfg.model:
        return repr(result)
    return f"{result!s}"


def run_cmd(cfg: CLIConfig) -> Results:
    grammar = _load_grammar(cfg.path)
    start = cfg.start or None

    if len(cfg.inputs) == 1:
        path = cfg.inputs[0]
        text = Path(path).read_text(encoding="utf-8")
        result = grammar.parse(text, start=start)
        return [(path, result)]

    if is_rich_library_available() and not cfg.quiet:
        return _run_with_progress(grammar, start, cfg)

    return _run_direct(grammar, start, cfg)


def _run_direct(
    grammar: Any,
    start: str | None,
    cfg: CLIConfig,
) -> Results:
    from ...util.parproc import parproc

    config = ParserConfig.new()

    def parse_file(path: str) -> Any:
        text = Path(path).read_text(encoding="utf-8")
        return grammar.parse(text, start=start, config=config)

    return [
        (r.payload, _format_result(cfg, r.outcome))
        for r in parproc(parse_file, cfg.inputs, parallel=cfg.nproc > 0)
        if r is not None and r.outcome is not None and r.exception is None
    ]


def _run_with_progress(
    grammar: Any,
    start: str | None,
    cfg: CLIConfig,
) -> Results:
    from rich.progress import (  # pyright: ignore[reportMissingImports]
        BarColumn,
        Progress,
        TaskID,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table

    class DualProgress(Progress):
        def __init__(self, *columns, **kwargs):
            super().__init__(*columns, **kwargs)
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
                table.add_row(*(c.render(task) for c in columns))
                yield table

    top_progress = DualProgress(
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        # TextColumn("[name][progress.description]"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None, complete_style="yellow"),
        refresh_per_second=1,
        speed_estimate_period=30.0,
    )
    task_progress = top_progress

    class ProgressHeart:
        def __init__(self, name: str, total: int) -> None:
            self.name = name
            self.task = task_progress.add_task(name, total=total)

        def beat(self, mark: int, total: int) -> None:
            if total == 0:
                return
            task_progress.update(
                self.task,
                completed=mark,
                total=total,
                coloer='greem',
                description=f"[bold white]{self.name:40} [green][/]",
            )

        def finish(self) -> None:
            task_progress.remove_task(self.task)

    def parse_file(path: str) -> Any:
        text = Path(path).read_text(encoding="utf-8")

        fileheart = ProgressHeart(Path(path).name, len(text))
        config = ParserConfig.new()
        config.heart = fileheart
        try:
            tree = grammar.parse(text, start=start, config=config)
            tree.linecount = len(text)
            return tree
        finally:
            fileheart.finish()

    total = len(cfg.inputs)
    toptask = top_progress.add_task(Path(cfg.path).name, total=total)
    top_progress.set_main(toptask)

    def build_progressbar(total: int) -> ProgressPair:
        return (top_progress, toptask)

    results: list[tuple[str, Any]] = []
    for r in parproc_visual(
        parse_file,
        cfg.inputs,
        build_progressbar=build_progressbar,
        parallel=True,
    ):
        if r is None:
            continue
        if r.exception is None and r.outcome is not None:
            results.append((r.payload, _format_result(cfg, r.outcome)))
    top_progress.stop()
    return results

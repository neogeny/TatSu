# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ...config import ParserConfig
from ...util.parproc import ProgressPair, Result, VisualPayload, parproc_visual
from ...util.richtest import is_rich_library_available
from .lib import (
    CLIConfig,
    Results,
    format_result,
    load_grammar,
    show_summary,
)


def run_cmd(cfg: CLIConfig) -> Results:
    grammar = load_grammar(cfg.path)
    start = cfg.start or None

    if len(cfg.inputs) == 1:
        path = cfg.inputs[0]
        text = Path(path).read_text(encoding="utf-8")
        result = grammar.parse(text, start=start)
        return [(path, result)]

    if is_rich_library_available() and not cfg.quiet:
        return run_with_progress(grammar, start, cfg)
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

    return [
        (r.payload, format_result(cfg, r.outcome))
        for r in parproc(parse_single_file, cfg.inputs, parallel=cfg.nproc > 0)
        if r is not None and r.outcome is not None and r.exception is None
    ]


def run_with_progress(
    grammar: Any,
    start: str | None,
    cfg: CLIConfig,
) -> Results:
    from rich.progress import (  # pyright: ignore[reportMissingImports]
        BarColumn,
        Progress,
        TaskID,
        TextColumn,
    )
    from rich.table import Table

    class DualProgress(Progress):
        def __init__(self, *columns, **kwargs) -> None:
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
        # TaskProgressColumn(),
        # TimeElapsedColumn(),
        # TimeRemainingColumn(),
        # TextColumn("[name][progress.description]"),
        # TextColumn("[progress.description][task.description]"),
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

    def parse_file(payload: VisualPayload) -> Any:
        path = Path(payload.path)
        text = payload.content

        config = ParserConfig.new()

        fileheart = ProgressHeart(path.name, len(text))
        config.heart = fileheart

        relpath = path.absolute().relative_to(Path().absolute())
        config.source = str(relpath)

        try:
            return grammar.parse(text, start=start, config=config)
        finally:
            fileheart.finish()

    total = len(cfg.inputs)
    toptask = top_progress.add_task(Path(cfg.path).name, total=total)
    top_progress.set_main(toptask)

    def build_progressbar(total: int) -> ProgressPair:
        return (top_progress, toptask)

    paths = [Path(input) for input in cfg.inputs]
    payloads = [VisualPayload(path, path.read_text()) for path in paths]
    start_time = time.time()
    results: list[Result] = []
    results = list(
        parproc_visual(
            parse_file,
            payloads,
            build_progressbar=build_progressbar,
            parallel=True,
            reraise=False,
            summary=False,
        )
    )
    top_progress.stop()
    results = list(results)
    total_time = time.time() - start_time
    show_summary(cfg, total_time, results)

    return [(r.payload.path, r.outcome) for r in results]

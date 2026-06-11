# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from tatsu.util.strtools import countlines

from ...config import ParserConfig
from ...util.parproc import ProgressPair, parproc_visual
from ...util.richtest import is_rich_library_available
from .lib import (
    CLIConfig,
    ParseStats,
    Results,
    format_result,
    load_grammar,
    show_results,
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

    return run_direct(grammar, start, cfg)


def run_direct(
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
        (r.payload, format_result(cfg, r.outcome))
        for r in parproc(parse_file, cfg.inputs, parallel=cfg.nproc > 0)
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

    file_lc: dict[str, Any] = {}
    for p in cfg.inputs:
        text = Path(p).read_text(encoding="utf-8")
        file_lc[p] = countlines(text)

    def parse_file(pathstr: str) -> Any:
        path = Path(pathstr)
        text = Path(path).read_text(encoding="utf-8")
        relpath = path.absolute().relative_to(Path().absolute())

        fileheart = ProgressHeart(path.name, len(text))
        config = ParserConfig.new()
        config.heart = fileheart
        config.source = str(relpath)
        try:
            return grammar.parse(text, start=start, config=config)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            return e
        finally:
            fileheart.finish()

    total = len(cfg.inputs)
    source_lines = sum(file_lc[p].totl for p in cfg.inputs)
    code_lines = sum(file_lc[p].code for p in cfg.inputs)
    comment_lines = sum(file_lc[p].cmnt for p in cfg.inputs)
    blank_lines = sum(file_lc[p].blnk for p in cfg.inputs)
    stats = ParseStats(
        total_files=total,
        source_lines=source_lines,
        code_lines=code_lines,
        comment_lines=comment_lines,
        blank_lines=blank_lines,
    )
    start_time = time.time()
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
        summary=False,
    ):
        if r is None:
            continue
        stats.run_time += r.time
        stats.results.append(r)
        if isinstance(r.outcome, Exception):
            continue
        stats.success_count += 1
        lc = file_lc[r.payload]
        stats.success_linecount += lc.code
        results.append((r.payload, format_result(cfg, r.outcome)))
    stats.total_time = time.time() - start_time
    top_progress.stop()

    show_summary(cfg, stats)
    return results

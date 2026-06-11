# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tatsu.util.strtools import countlines

from ...config import ParserConfig
from ...util.asjson import asjsons
from ...util.parproc import ProgressPair, Result, parproc_visual
from ...util.richtest import is_rich_library_available
from .lib import CLIConfig, Results, _load_grammar


@dataclass
class ParseStats:
    total_files: int = 0
    source_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    success_count: int = 0
    success_linecount: int = 0
    total_time: float = 0.0
    run_time: float = 0.0
    results: list[Result] = field(default_factory=list)


def _format_duration(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h:
        return f"{h}:{m:02d}:{s:05.2f}"
    return f"{m}:{s:05.2f}"


def _show_results(stats: ParseStats) -> None:
    from rich.console import Console

    console = Console(stderr=True)

    for r in stats.results:
        if r.exception or isinstance(r.outcome, Exception):
            print(file=sys.stderr)
            print(r.outcome, file=sys.stderr)

    console.print("[dim cyan]results[/dim cyan]:")
    for r in stats.results:
        name = Path(r.payload).name
        if r.exception or isinstance(r.outcome, Exception):
            console.print(f"  [red]✗[/red]  [magenta]{r.time:>6.2f}s[/magenta]  {name}")
        else:
            console.print(
                f"  [green]✓[/green]  [bright_cyan]{r.time:>6.2f}s[/bright_cyan]  {name}"
            )


def _show_summary(stats: ParseStats) -> None:
    from rich.console import Console
    from rich.table import Table

    console = Console(stderr=True)
    failures = stats.total_files - stats.success_count
    success_rate = (
        100 * stats.success_count / stats.total_files if stats.total_files else 0
    )
    lines_per_second = (
        stats.success_linecount / stats.run_time if stats.run_time > 0 else 0
    )

    table = Table(show_header=False, box=None)
    table.add_column(style="dim cyan", justify="right")
    table.add_column(style="bright_white")

    table.add_row("files input", f"{stats.total_files:>12}")
    table.add_row("source lines input", f"{stats.source_lines:>12}")
    table.add_row("total lines processed", f"{stats.success_linecount:>12}")
    rate_color = (
        "green" if success_rate >= 100 else "yellow" if success_rate > 0 else "red"
    )
    table.add_row("lines/sec", f"[yellow]{lines_per_second:>12,.0f}[/yellow]")
    table.add_row("successes", f"[green]{stats.success_count:>12}[/green]")
    table.add_row("failures", f"[red]{failures:>12}[/red]")
    table.add_row(
        "success rate", f"[{rate_color}]{success_rate:>11.1f}%[/{rate_color}]"
    )
    table.add_row("time", _format_duration(stats.total_time).rjust(12))
    table.add_row("run time", _format_duration(stats.run_time).rjust(12))

    console.print()
    console.print(table)

    if failures:
        console.print(f"\n[red bold]FAILURES: {failures}")
        sys.exit(1)


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
            tree = grammar.parse(text, start=start, config=config)
            return tree
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
        results.append((r.payload, _format_result(cfg, r.outcome)))
    stats.total_time = time.time() - start_time
    top_progress.stop()

    if cfg.verbose:
        _show_results(stats)
    if not cfg.quiet:
        _show_summary(stats)
    return results

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import time
from collections.abc import Generator, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ...util import asjsons, countlines, slicetowidth
from ...util.colorize import Color
from ...util.parproc import Result, StrPayload
from .cfg import CLIConfig


class Printer(Protocol):
    def print(self, *args: Any, **kwargs: Any) -> None: ...


class StdErrPrinter(Printer):
    def print(self, *args: Any, **kwargs: Any) -> None:
        print(*args, **kwargs, file=sys.stderr)


@dataclass
class ParseStats:
    file_count: int = 0
    totl_lines: int = 0
    code_lines: int = 0
    cmnt_lines: int = 0
    blnk_lines: int = 0
    succ_count: int = 0
    succ_lines: int = 0
    succ_rate: float = 0.0
    run_time: float = 0.0
    slocs_avg: float = 0.0


def format_result(cfg: CLIConfig, result: Any) -> str:
    if cfg.model:
        return repr(result)
    return asjsons(result)


def format_duration(seconds: float, fractions: bool = False) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h >= 1:
        if fractions:
            return f"{h}:{m:02d}:{s:05.2f}"
        return f"{h}:{m:02d}:{s:02.0f}"
    if fractions:
        return f"{m}:{s:05.2f}"
    return f"{m}:{s:02.0f}"


def result_stats(stats: ParseStats, results: Iterable[Result]) -> Iterable[Result]:
    eolcmt = {
        ".java": "//",
        ".py": "#",
        ".rs": "//",
        ".go": "//",
        ".js": "//",
        ".ts": "//",
    }
    for r in results:
        stats.file_count += 1
        stats.run_time += r.runtime

        # Compensate for Visual Non-Visual
        p = r.payload
        if not hasattr(r.payload, 'path'):
            p = StrPayload(r.payload)

        suffix = p.path.suffix
        counts = countlines(p.payload, eolcmt.get(suffix, "//"))
        stats.totl_lines += counts.totl
        stats.code_lines += counts.code
        stats.cmnt_lines += counts.cmnt
        stats.blnk_lines += counts.blnk

        if r.success and not r.exception:
            stats.succ_count += 1
            stats.succ_lines += counts.totl
        yield r

    stats.slocs_avg = stats.totl_lines / stats.run_time if stats.run_time > 0 else 0
    stats.succ_rate = stats.succ_count / stats.file_count if stats.file_count else 0


def show_summary(
    cfg: CLIConfig,
    start_time: float,
    results: Iterable[Result],
    printer: Printer | None = None,
) -> Generator[Result, None, None]:
    from rich.console import Console
    from rich.table import Table

    _color = Color(cfg.usecolor)
    if printer is None:
        printer = StdErrPrinter()

    if cfg.verbose:
        results = show_results(cfg, printer, results)

    stats = ParseStats()
    results = result_stats(stats, results)
    results = list(results)
    failures = stats.file_count - stats.succ_count

    console = Console(stderr=True)
    outresults: list[Result] = []
    if cfg.verbose:
        for r in results:
            if not (r.exception or isinstance(r.outcome, Exception)):
                outresults.append(r)
                continue
            print(file=sys.stderr)
            print(r.exception, file=sys.stderr)

        if failures:
            console.print(f"[red bold]FAILURES: {failures}[/]")
        else:
            console.print(f"[green bold]NO FAILURES: {failures}[/]")

    table = Table(show_header=False, box=None)
    table.add_column(style="dim cyan", justify="right")
    table.add_column(style="bright_white")

    table.add_row("files input", f"{stats.file_count:>12}")
    table.add_row("source lines input", f"{stats.totl_lines:>12}")
    table.add_row("success lines", f"{stats.succ_lines:>12}")
    table.add_row("sloc", f"{stats.code_lines:>12}")
    rate_color = (
        "green"
        if stats.succ_rate >= 1.0
        else "yellow"
        if stats.succ_rate > 0.6
        else "red"
    )
    table.add_row("successes", f"[green]{stats.succ_count:>12}[/green]")
    table.add_row("failures", f"[red]{failures:>12}[/red]")
    table.add_row(
        "success rate",
        f"[{rate_color}]{100.0 * stats.succ_rate:>12.0f} %[/{rate_color}]",
    )

    if stats.slocs_avg >= 200:
        csloc = "green"
    elif stats.slocs_avg >= 180:
        csloc = "yellow"
    else:
        csloc = "red"
    table.add_row("sloc/sec", f"[{csloc}]{stats.slocs_avg:>12,.0f} sl/s[/{csloc}]")

    table.add_row("run time", format_duration(stats.run_time, False).rjust(12))
    total_time = time.time() - start_time
    table.add_row("wall time", format_duration(total_time, False).rjust(12))

    console.print()
    console.print(table)
    yield from outresults


def show_results(
    _cfg: CLIConfig,
    printer: Printer,
    results: Iterable[Result],
) -> Iterable[Result]:
    from rich.markup import render

    def rprint(s: str = "", *args, file=sys.stderr, **kwargs) -> None:
        _ = file
        printer.print(render(s), *args, **kwargs)

    rprint("[dim cyan]results[/dim cyan]:")

    maxw = 40
    padc = 0

    def success_results(results) -> Iterable[Result]:
        yield from results
        # for r in results:
        #     name = slicetowidth(Path(r.payload.path).name, maxw)
        #     if not r.exception and not isinstance(r.outcome, Exception):
        #         rprint(
        #             f"{'':{padc}}[green]✓[/] {name:{maxw}} [green]{r.runtime:>4.1f}s",
        #         )
        #     yield r

    for r in success_results(results):
        name = slicetowidth(Path(r.payload.path).name, maxw)
        if r.exception or isinstance(r.outcome, Exception):
            rprint(f"{'':{padc}}[red]✗[/] {name:{maxw}} [red]{r.runtime:>4.1f}s")
        yield r

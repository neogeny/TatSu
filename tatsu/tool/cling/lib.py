# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tatsu.util.asjson import asjsons
from tatsu.util.parproc import Result


if TYPE_CHECKING:
    from ...grammars.model import Grammar


type Results = list[tuple[str, Any]]


@dataclass
class CLIConfig:
    """Parsed command-line configuration, matching ogopego's CLIConfig struct."""

    # Global flags
    color: str = "auto"
    output: str = ""
    verbose: bool = False
    quiet: bool = False
    profile: bool = False
    trace: bool = False

    # Subcommand state
    command: str = ""
    path: str = ""
    inputs: list[str] = field(default_factory=list)

    # format flags
    json: bool = False
    model: bool = False
    pretty: bool = False
    railroads: bool = False

    # run flags
    start: str = ""
    nproc: int = 0


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


def load_grammar(path: str) -> Grammar:
    """Load a Grammar from an .ebnf or .json file."""
    from ...grammars.model import Grammar as _Grammar

    p = Path(path)
    source = p.read_text(encoding="utf-8")
    if p.suffix == ".json":
        return _Grammar.loads(source)
    from ..api import compile

    return compile(source)


def format_result(cfg: CLIConfig, result: Any) -> str:
    if cfg.json:
        return asjsons(result)
    if cfg.model:
        return repr(result)
    return f"{result!s}"


def format_duration(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h:
        return f"{h}:{m:02d}:{s:05.2f}"
    return f"{m}:{s:05.2f}"


def show_results(cfg: CLIConfig, stats: ParseStats) -> None:
    from rich.console import Console

    console = Console(stderr=True)

    for r in stats.results:
        if isinstance(r.outcome, Exception):
            print(file=sys.stderr)
            print(r.outcome, file=sys.stderr)
        if r.exception:
            print(file=sys.stderr)
            print(r.exception, file=sys.stderr)

    console.print("[dim cyan]results[/dim cyan]:")
    for r in stats.results:
        name = Path(r.payload).name
        if r.exception or isinstance(r.outcome, Exception):
            console.print(f"  [red]✗[/red]  [magenta]{r.time:>6.2f}s[/magenta]  {name}")
        else:
            console.print(
                f"  [green]✓[/green]  [bright_cyan]{r.time:>6.2f}s[/bright_cyan]  {name}"
            )


def show_summary(cfg: CLIConfig, stats: ParseStats) -> None:
    if cfg.quiet:
        return
    if cfg.verbose:
        show_results(cfg, stats)

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
    table.add_row("time", format_duration(stats.total_time).rjust(12))
    table.add_row("run time", format_duration(stats.run_time).rjust(12))

    console.print()
    console.print(table)

    if failures:
        console.print(f"\n[red bold]FAILURES: {failures}")
        sys.exit(1)

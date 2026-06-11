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
from ...util.unicode_characters import U_CHECK_MARK, U_CROSSED_SWORDS
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
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )

    # from ...util.common import startscript

    top_progress = Progress(
        # TextColumn(f"[progress.description]{startscript()}"),
        TextColumn("[name][progress.description]"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        TextColumn("[progress.description]{task.description}"),
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
            pct = mark / total * 100
            task_progress.update(
                self.task,
                completed=mark,
                total=total,
                description=f"{pct:4.1f}% [bold white]{self.name} [/]",
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
        finally:
            fileheart.finish()

        @dataclass
        class wrapper:
            count: int
            tree: Any

        count = countlines(text).code
        return wrapper(count, tree)

    total = len(cfg.inputs)
    toptask = top_progress.add_task(Path(cfg.path).name, total=total)

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
        # name = Path(r.payload).name
        if r.exception is None and r.outcome is not None:
            icon = U_CHECK_MARK
            color = "green"
            results.append((r.payload, _format_result(cfg, r.outcome)))
        else:
            icon = U_CROSSED_SWORDS
            color = "red"
        pct = 100 * len(results) / total
        # WARNING the main bar is updated by parproc
        # progress.update(
        #     topheart.task,
        #     advance=1,
        #     description=f"[{color}]{pct:4.1f}% {icon} {name}",
        # )

    # progress.update(topheart.task, advance=total, description="")
    top_progress.stop()
    return results

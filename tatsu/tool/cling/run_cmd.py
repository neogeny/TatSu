# Copyright © 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...config import ParserConfig
from ...grammars import Grammar
from ...util.heart import Heart
from ...util.parproc import ProgressPair, VisualPayload, parproc_visual
from ...util.richtest import is_rich_library_available
from .cfg import CLIConfig
from .global_opt import add_global_options
from .lib import Results, load_grammar
from .prog import make_progressbar
from .sum import format_result, show_summary


def add_run_cmd(subparsers):
    run_parser = subparsers.add_parser(
        "run",
        help="Parse input files with the given grammar",
    )
    add_global_options(run_parser)
    run_parser.add_argument(
        "grammar",
        help="Path to a grammar in EBNF or JSON format",
    )
    run_parser.add_argument(
        "inputs",
        nargs="+",
        help="The files to be parsed",
    )

    format = run_parser.add_mutually_exclusive_group()
    format.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="json",
        default=True,
        help="Output the grammar in JSON format",
    )
    format.add_argument(
        "-jl",
        "--jsonl",
        action="store_true",
        dest="json_lines",
        default=False,
        help="Output the grammar in JSON Lines format",
    )
    format.add_argument(
        "-m",
        "--model",
        action="store_true",
        dest="model",
        help="Output the model code according to the grammar",
    )
    run_parser.add_argument(
        "-s", "--start", default="", dest="start", help="Name of the start rule"
    )
    run_parser.add_argument(
        "-n",
        "--nproc",
        type=int,
        default=0,
        dest="nproc",
        help="Number of concurrent workers",
    )
    run_parser.add_argument(
        "-u",
        "--summary",
        action="store_true",
        help="Always show summary (overrides --quiet)",
    )
    return run_parser


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

    if is_rich_library_available() and not cfg.quiet:
        return run_with_progress(start_time, grammar, start, cfg)
    else:
        return run_without_progress(start_time, grammar, start, cfg)


def run_without_progress(
    start_time: float,
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
    results = parproc(parse_single_file, cfg.inputs, parallel=parallel)

    if cfg.summary or not cfg.quiet:
        results = show_summary(cfg, start_time, results)

    return [
        (r.payload, format_result(cfg, r.outcome))
        for r in results
        if r is not None and r.outcome is not None and r.exception is None
    ]


def run_with_progress(
    start_time: float,
    grammar: Any,
    start: str | None,
    cfg: CLIConfig,
) -> Results:
    top_progress = make_progressbar()
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
            max_workers=cfg.nproc,
        )
        if cfg.summary or not cfg.quiet:
            results = show_summary(cfg, start_time, results, top_progress)
    finally:
        print(file=sys.stderr)
        top_progress.stop()
        print(file=sys.stderr)

    return [(str(r.payload.path), format_result(cfg, r.outcome)) for r in results]

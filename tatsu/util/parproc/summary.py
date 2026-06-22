# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import time
from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import countlines, debugging, slicetowidth
from ..ztyle import Color
from .result import Result


type PrintFunc = Callable[..., None]


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


class SummaryStyle:
    def __init__(self, color: Color):
        self.label = color.style(dim=True).cyan()
        self.plain = color.style()
        self.good = color.style().green()
        self.bad = color.style().red()
        self.warn = color.style().yellow()
        self.bold_good = color.style(bold=True).green()
        self.bold_bad = color.style(bold=True).red()


class ResultsStyle:
    def __init__(self, color: Color | None = None):
        color = color or Color.default()
        self.header = color.style(dim=True).cyan()
        self.good = color.style().green()
        self.bad = color.style().red()
        self.plain = color.style()


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

        p = r.payload
        if not hasattr(r.payload, 'path'):
            from .parproc import StrPayload

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
    start_time: float,
    results: Iterable[Result],
    /,
    eprint: PrintFunc = debugging.eprint,
    *,
    usecolor: bool = True,
    verbose: bool = True,
) -> Generator[Result, None, None]:
    s = SummaryStyle(Color(usecolor))
    if verbose:
        results = show_results(eprint, results, usecolor=usecolor)

    st = ParseStats()
    results = result_stats(st, results)
    results = list(results)
    fail = st.file_count - st.succ_count

    results = list(results)
    out: list[Result] = []
    for r in results:
        out.append(r)
        if verbose and r.exception:
            eprint()
            eprint(r.exception)

    if verbose:
        mk = s.bold_bad if fail else s.bold_good
        eprint()
        eprint(mk(f"FAILURES: {fail}" if fail else f"NO FAILURES: {fail}"))

    W = 18

    def row(la: str, va: Any) -> str:
        return f"{s.label(f'{la:>{W}}')}  {va}"

    eprint()
    eprint(row("files input", s.plain(f"{st.file_count:>12}")))
    eprint(row("source lines input", s.plain(f"{st.totl_lines:>12}")))
    eprint(row("success lines", s.plain(f"{st.succ_lines:>12}")))
    eprint(row("sloc", s.plain(f"{st.code_lines:>12}")))

    rate_st = s.good if st.succ_rate >= 1.0 else s.warn if st.succ_rate > 0.6 else s.bad
    eprint(row("successes", s.good(f"{st.succ_count:>12}")))
    eprint(row("failures", s.bad(f"{fail:>12}")))
    eprint(row("success rate", rate_st(f"{100.0 * st.succ_rate:>12.0f} %")))

    sloc_st = (
        s.good if st.slocs_avg >= 200 else s.warn if st.slocs_avg >= 180 else s.bad
    )
    eprint(row("sloc/sec", sloc_st(f"{st.slocs_avg:>12,.0f} sl/s")))

    eprint(row("run time", s.plain(format_duration(st.run_time, False).rjust(12))))
    eprint(
        row(
            "wall time",
            s.plain(format_duration(time.time() - start_time, False).rjust(12)),
        )
    )
    eprint()
    yield from out


def show_result(rprint: PrintFunc, r: Result) -> None:
    s = ResultsStyle()
    nm = slicetowidth(Path(r.payload.path).name, 40)
    if r.exception or isinstance(r.outcome, Exception):
        rprint(f" {s.bad('✗')} {s.plain(f'{nm}'):45}{s.bad(f'⏲ {r.runtime:>7.3f}')}")
    else:
        rprint(f" {s.good('✓')} {s.plain(f'{nm}'):45}{s.good(f'⏲ {r.runtime:>7.3f}')}")


def show_results(
    rprint: PrintFunc,
    results: Iterable[Result],
    /,
    *,
    usecolor: bool = False,
) -> Iterable[Result]:
    for r in results:
        show_result(rprint, r)
        yield r

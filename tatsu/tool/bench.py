#!/usr/bin/env python3
# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .. import grammars
from ..exceptions import FailedParse
from ..parsing import Parser
from ..tool.api import compile, to_python_sourcecode
from ..util.common import try_read, typename
from ..util.strtools import countlines
from ..util.timetools import timer


@dataclass
class BenchmarkResult:
    typename: str
    file_count: int
    error_count: int
    setup_time: float
    total_parsing_time: float
    avg_parsing_time: float
    avg_lines_sec: float


def _setup_mem_parser(grammar_src: str) -> tuple[grammars.Grammar, float]:
    with timer() as t:
        model = compile(grammar_src)
    return model, t.delta


def _setup_gen_parser(
    grammar_src: str, grammar_name: str
) -> tuple[Parser, float, Path]:
    parser_file = f"temp_parser_{int(time.time())}.py"
    parser_path = Path(parser_file).resolve()

    with timer() as tgen:
        python_source = to_python_sourcecode(grammar_src, name=grammar_name)
        parser_path.write_text(python_source, encoding='utf-8')

        spec = importlib.util.spec_from_file_location("temp_gen_parser", parser_path)
        if not (spec and spec.loader):
            raise ImportError("could not create module spec")

        module = importlib.util.module_from_spec(spec)
        sys.modules["temp_gen_parser"] = module
        spec.loader.exec_module(module)

        parser_class = getattr(module, f"{grammar_name}Parser", None)
        if not parser_class:
            for obj in vars(module).values():
                if (
                    isinstance(obj, type)
                    and issubclass(obj, Parser)
                    and obj is not Parser
                ):
                    parser_class = obj
                    break
        if not parser_class:
            raise RuntimeError("could not find a generated parser class in the module.")
        parser = parser_class()

    gen_time = tgen.delta
    return parser, gen_time, parser_path


def _print_run_details(title: str, result: BenchmarkResult, lbl_w: int, num_fmt: str):
    print(f"\n--- {title} ---")
    print(f"typename: {result.typename}")
    print(f"{'one-time setup:':<{lbl_w}}{num_fmt.format(result.setup_time)} s")
    print(
        f"{f'total parsing time ({result.file_count} files):':<{lbl_w}}"
        f"{num_fmt.format(result.total_parsing_time)} s"
    )
    print(
        f"{f'errors ({result.file_count} files):':<{lbl_w}}"
        f"{num_fmt.format(result.error_count)} s"
    )
    print(
        f"{'average parsing time:':<{lbl_w}}{num_fmt.format(result.avg_parsing_time)} s/file"
    )
    print(f"{'average speed:':<{lbl_w}}{num_fmt.format(result.avg_lines_sec)} sloc/sec")


def print_summary(
    grammar: str,
    count: int,
    mem_run: BenchmarkResult,
    gen_run: BenchmarkResult,
):
    relgrammar = Path(grammar).resolve().relative_to(Path.cwd())
    print(f"grammar: {relgrammar}")
    print(f"input files: {count}")

    all_numbers = [
        mem_run.setup_time,
        mem_run.total_parsing_time,
        mem_run.avg_parsing_time,
        mem_run.avg_lines_sec,
        gen_run.setup_time,
        gen_run.total_parsing_time,
        gen_run.avg_parsing_time,
        gen_run.avg_lines_sec,
    ]
    int_width = max(len(str(int(abs(n)))) for n in all_numbers) if all_numbers else 0
    num_width = int_width + 3
    num_fmt = f"{{:>{num_width}.2f}}"

    count_width = len(str(max(mem_run.file_count, gen_run.file_count)))
    longest_label = f"total parsing time ({'9' * count_width} files):"
    labels = [
        "one-time setup:",
        longest_label,
        "average parsing time:",
        "average speed:",
        "in-memory:",
        "generated:",
    ]
    lbl_w = max(len(lbl) for lbl in labels) + 2

    _print_run_details("in-memory model", mem_run, lbl_w, num_fmt)
    _print_run_details("generated python parser", gen_run, lbl_w, num_fmt)

    print("\n--- comparison (average parsing time) ---")
    mem_sloc = mem_run.avg_lines_sec
    gen_sloc = gen_run.avg_lines_sec
    print(f"{'in-memory:':<{lbl_w}}{num_fmt.format(mem_sloc)} sloc/sec")
    print(f"{'generated:':<{lbl_w}}{num_fmt.format(gen_sloc)} sloc/sec")

    if gen_sloc < mem_sloc:
        factor = mem_sloc / gen_sloc
        print(f"generated parser is {factor:.2f}x slower on average")
    else:
        factor = gen_sloc / mem_sloc
        print(f"generated parser is {factor:.2f}x faster on average")


def benchmark(
    grammar: str | Path,
    filenames: Iterable[str | Path],
) -> tuple[BenchmarkResult, BenchmarkResult]:
    oldlimit = sys.getrecursionlimit()
    sys.setrecursionlimit(2**16)
    try:
        grampath = Path(grammar)
        gramsrc = grampath.read_text(encoding="utf-8")

        model, memsetup = _setup_mem_parser(gramsrc)
        gramname = model.name or "Benchmark"
        parser, gensetup, _ = _setup_gen_parser(gramsrc, gramname)

        # Pre-load data to isolate parsing logic from I/O overhead
        filepaths = [Path(f) for f in filenames]
        texts = [try_read(p) for p in filepaths]
        totallines = sum(countlines(t).code for t in texts)
        nfiles = len(texts)

        # --- Loop 1: Memory Parser ---
        memtime = 0.0
        memerrs = 0
        for i, text in enumerate(texts):
            pct = int((i + 1) / nfiles * 100)
            print(f"[Mem {pct:3d}%] Benchmarking memory parser...", end="\r")
            with timer() as t:
                try:
                    model.parse(text, asmodel=True)
                except FailedParse:
                    memerrs += 1
                memtime += t.delta

        # --- Loop 2: Generated Parser ---
        gentime = 0.0
        generrs = 0
        for i, text in enumerate(texts):
            pct = int((i + 1) / nfiles * 100)
            print(f"[Gen {pct:3d}%] Benchmarking generated parser...", end="\r")
            with timer() as t:
                try:
                    parser.parse(text, asmodel=True)
                except FailedParse:
                    generrs += 1
                gentime += t.delta

        print(" " * 75)  # Clear the status line

        memrun = BenchmarkResult(
            typename(model),
            file_count=nfiles,
            error_count=memerrs,
            setup_time=memsetup,
            total_parsing_time=memtime,
            avg_parsing_time=memtime / nfiles if nfiles else 0,
            avg_lines_sec=totallines / memtime if memtime else 0,
        )
        genrun = BenchmarkResult(
            typename(parser),
            file_count=nfiles,
            error_count=generrs,
            setup_time=gensetup,
            total_parsing_time=gentime,
            avg_parsing_time=gentime / nfiles if nfiles else 0,
            avg_lines_sec=totallines / gentime if gentime else 0,
        )
        return memrun, genrun
    finally:
        sys.setrecursionlimit(oldlimit)


def main():
    parser = argparse.ArgumentParser(description="benchmark tatsu parsing methods")
    parser.add_argument("grammar", type=Path, help="path to the grammar file")
    parser.add_argument(
        "inputs", type=Path, nargs='+', help="path to one or more input text files"
    )
    args = parser.parse_args()

    for p in [args.grammar, *args.inputs]:
        if not p.exists():
            print(f"error: file '{p}' not found.")
            sys.exit(1)

    try:
        grammar_path = args.grammar.resolve()
        input_paths = [p.resolve() for p in args.inputs]
        mem_run, gen_run = benchmark(grammar_path, input_paths)
        print_summary(
            str(args.grammar),
            len(args.inputs),
            mem_run,
            gen_run,
        )
    except Exception as e:
        print(f"\nan error occurred: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()

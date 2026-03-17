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
from ..parsing import Parser
from ..tool.api import compile, to_python_sourcecode
from .common import try_read
from .strtools import countlines
from .timetools import timer


@dataclass
class BenchmarkResult:
    file_count: int
    setup_time: float
    total_parsing_time: float
    avg_parsing_time: float
    avg_lines_sec: float


def _setup_memory_parser(grammar_src: str) -> tuple[grammars.Grammar, float]:
    with timer() as t:
        model = compile(grammar_src)
    return model, t.delta


def _setup_generated_parser(
    grammar_src: str, grammar_name: str
) -> tuple[Parser, float, Path]:
    parser_file = f"temp_parser_{int(time.time())}.py"
    parser_path = Path(parser_file).resolve()

    with timer() as tgen:
        python_source = to_python_sourcecode(grammar_src, name=grammar_name)
        parser_path.write_text(python_source, encoding='utf-8')

        spec = importlib.util.spec_from_file_location(
            "temp_generated_parser", parser_path
        )
        if not (spec and spec.loader):
            raise ImportError("could not create module spec")

        module = importlib.util.module_from_spec(spec)
        sys.modules["temp_generated_parser"] = module
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
    print(f"{'one-time setup:':<{lbl_w}}{num_fmt.format(result.setup_time)} s")
    print(
        f"{f'total parsing time ({result.file_count} files):':<{lbl_w}}"
        f"{num_fmt.format(result.total_parsing_time)} s"
    )
    print(
        f"{'average parsing time:':<{lbl_w}}{num_fmt.format(result.avg_parsing_time)} s/file"
    )
    print(f"{'average speed:':<{lbl_w}}{num_fmt.format(result.avg_lines_sec)} sloc/sec")


def print_summary(
    grammar: str,
    count: int,
    memory_run: BenchmarkResult,
    gen_run: BenchmarkResult,
):
    relgrammar = Path(grammar).resolve().relative_to(Path.cwd())
    print(f"grammar: {relgrammar}")
    print(f"input files: {count}")

    all_numbers = [
        memory_run.setup_time,
        memory_run.total_parsing_time,
        memory_run.avg_parsing_time,
        memory_run.avg_lines_sec,
        gen_run.setup_time,
        gen_run.total_parsing_time,
        gen_run.avg_parsing_time,
        gen_run.avg_lines_sec,
    ]
    int_width = max(len(str(int(abs(n)))) for n in all_numbers) if all_numbers else 0
    num_width = int_width + 3
    num_fmt = f"{{:>{num_width}.2f}}"

    count_width = len(str(max(memory_run.file_count, gen_run.file_count)))
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

    _print_run_details("in-memory model", memory_run, lbl_w, num_fmt)
    _print_run_details("generated python parser", gen_run, lbl_w, num_fmt)

    print("\n--- comparison (average parsing time) ---")
    memory_sloc = memory_run.avg_lines_sec
    gen_sloc = gen_run.avg_lines_sec
    print(f"{'in-memory:':<{lbl_w}}{num_fmt.format(memory_sloc)} sloc/sec")
    print(f"{'generated:':<{lbl_w}}{num_fmt.format(gen_sloc)} sloc/sec")

    if gen_sloc < memory_sloc:
        factor = memory_sloc / gen_sloc
        print(f"generated parser is {factor:.2f}x slower on average")
    else:
        factor = gen_sloc / memory_sloc
        print(f"generated parser is {factor:.2f}x faster on average")


def benchmark(
    grammar: str | Path,
    filenames: Iterable[str | Path],
) -> tuple[BenchmarkResult, BenchmarkResult]:
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(2**16)
    try:
        grammar_path = Path(grammar)
        grammar_src = grammar_path.read_text(encoding='utf-8')

        model, compile_time = _setup_memory_parser(grammar_src)
        grammar_name = model.name or 'Benchmark'
        parser, gen_time, parser_path = _setup_generated_parser(
            grammar_src, grammar_name
        )

        try:
            memory_time = 0.0
            gen_time_total = 0.0
            total_lines = 0
            nfiles = 0

            filepaths = [Path(f) for f in filenames]
            for i, path in enumerate(filepaths):
                pct = int((i + 1) / len(filepaths) * 100)
                print(f"[{pct:3d}%] {f'{path.name}...':60}", end='\r')
                text = try_read(path)
                total_lines += countlines(text).code

                with timer() as t:
                    model.parse(text)
                memory_time += t.delta

                with timer() as t:
                    parser.parse(text)
                gen_time_total += t.delta

                nfiles += 1
            print(" " * 70)  # Clear the filename feedback

            memory_run = BenchmarkResult(
                file_count=nfiles,
                setup_time=compile_time,
                total_parsing_time=memory_time,
                avg_parsing_time=memory_time / nfiles if nfiles else 0,
                avg_lines_sec=(total_lines / memory_time if memory_time else 0),
            )
            gen_run = BenchmarkResult(
                file_count=nfiles,
                setup_time=gen_time,
                total_parsing_time=gen_time_total,
                avg_parsing_time=gen_time_total / nfiles if nfiles else 0,
                avg_lines_sec=(total_lines / gen_time_total if gen_time_total else 0),
            )
            return memory_run, gen_run
        finally:
            if parser_path.exists():
                parser_path.unlink()
    finally:
        sys.setrecursionlimit(old_limit)


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
        memory_run, gen_run = benchmark(grammar_path, input_paths)
        print_summary(
            str(args.grammar),
            len(args.inputs),
            memory_run,
            gen_run,
        )
    except Exception as e:
        print(f"\nan error occurred: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()

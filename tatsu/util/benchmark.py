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

from tatsu.util import countlines

from .common import try_read
from .timetools import timer


# Add project root to sys.path to ensure tatsu is importable
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import tatsu
from tatsu.parsing import Parser


@dataclass
class BenchmarkResult:
    file_count: int
    setup_time: float
    total_parsing_time: float
    avg_parsing_time: float
    avg_lines_sec: float


def _setup_in_memory_parser(grammar_text: str) -> tuple[tatsu.grammars.Grammar, float]:
    with timer() as t:
        model = tatsu.compile(grammar_text)
    return model, t.delta


def _setup_generated_parser(grammar_text: str, grammar_name: str) -> tuple[Parser, float, Path]:
    temp_parser_filename = f"temp_parser_{int(time.time())}.py"
    temp_parser_path = Path(temp_parser_filename).resolve()

    with timer() as tgen:
        python_source = tatsu.to_python_sourcecode(grammar_text, name=grammar_name)
        temp_parser_path.write_text(python_source, encoding='utf-8')

        spec = importlib.util.spec_from_file_location("temp_generated_parser", temp_parser_path)
        if not (spec and spec.loader):
            raise ImportError("could not create module spec")

        module = importlib.util.module_from_spec(spec)
        sys.modules["temp_generated_parser"] = module
        spec.loader.exec_module(module)

        parser_class = getattr(module, f"{grammar_name}Parser", None)
        if not parser_class:
            for obj in vars(module).values():
                if isinstance(obj, type) and issubclass(obj, Parser) and obj is not Parser:
                    parser_class = obj
                    break
        if not parser_class:
            raise RuntimeError("could not find a generated parser class in the module.")
        parser_instance = parser_class()

    generation_time = tgen.delta
    return parser_instance, generation_time, temp_parser_path


def _print_run_details(title: str, result: BenchmarkResult, label_width: int, number_format_str: str):
    print(f"\n--- {title} ---")
    print(f"{'one-time setup:':<{label_width}}{number_format_str.format(result.setup_time)} s")
    print(
        f"{f'total parsing time ({result.file_count} files):':<{label_width}}"
        f"{number_format_str.format(result.total_parsing_time)} s"
    )
    print(f"{'average parsing time:':<{label_width}}{number_format_str.format(result.avg_parsing_time)} s/file")
    print(f"{'average speed:':<{label_width}}{number_format_str.format(result.avg_lines_sec)} sloc/sec")


def print_summary(
    grammar: str,
    count: int,
    in_memory_run: BenchmarkResult,
    generated_run: BenchmarkResult,
):
    print(f"grammar: {grammar}")
    print(f"input files: {count}")

    all_numbers = [
        in_memory_run.setup_time,
        in_memory_run.total_parsing_time,
        in_memory_run.avg_parsing_time,
        in_memory_run.avg_lines_sec,
        generated_run.setup_time,
        generated_run.total_parsing_time,
        generated_run.avg_parsing_time,
        generated_run.avg_lines_sec,
    ]
    max_int_len = max(len(str(int(abs(num)))) for num in all_numbers) if all_numbers else 0
    total_num_width = max_int_len + 3
    number_format_str = f"{{:>{total_num_width}.2f}}"

    max_file_count_str_len = len(str(max(in_memory_run.file_count, generated_run.file_count)))
    longest_dynamic_label = f"total parsing time ({'9'*max_file_count_str_len} files):"
    labels = [
        "one-time setup:",
        longest_dynamic_label,
        "average parsing time:",
        "average speed:",
        "in-memory:",
        "generated:",
    ]
    label_width = max(len(label) for label in labels) + 2

    _print_run_details("in-memory model", in_memory_run, label_width, number_format_str)
    _print_run_details("generated python parser", generated_run, label_width, number_format_str)

    print("\n--- comparison (average parsing time) ---")
    model_avg_sloc = in_memory_run.avg_lines_sec
    gen_avg_sloc = generated_run.avg_lines_sec
    print(f"{'in-memory:':<{label_width}}{number_format_str.format(model_avg_sloc)} sloc/sec")
    print(f"{'generated:':<{label_width}}{number_format_str.format(gen_avg_sloc)} sloc/sec")

    if gen_avg_sloc < model_avg_sloc:
        factor = model_avg_sloc / gen_avg_sloc
        print(f"generated parser is {factor:.2f}x slower on average")
    else:
        factor = gen_avg_sloc / model_avg_sloc
        print(f"generated parser is {factor:.2f}x faster on average")


def benchmark(
    grammar: str | Path,
    filenames: Iterable[str | Path],
) -> tuple[BenchmarkResult, BenchmarkResult]:
    prevreclimit = sys.getrecursionlimit()
    sys.setrecursionlimit(2**16)
    try:
        grammar_path = Path(grammar)
        grammar_text = grammar_path.read_text(encoding='utf-8')

        model, compilation_time = _setup_in_memory_parser(grammar_text)
        grammar_name = model.name or 'Benchmark'
        parser_instance, generation_time, temp_parser_path = _setup_generated_parser(grammar_text, grammar_name)

        try:
            total_in_memory_time = 0.0
            total_generated_time = 0.0
            total_lines = 0
            file_count = 0

            filepaths = [Path(f) for f in filenames]
            for input_path in filepaths:
                print(f"{f'{input_path.name}...':60}", end='\r')
                input_text = try_read(input_path)
                total_lines += countlines(input_text).code

                with timer() as t:
                    model.parse(input_text)
                total_in_memory_time += t.delta

                with timer() as t:
                    parser_instance.parse(input_text)
                total_generated_time += t.delta

                file_count += 1
            print(" " * 60) # Clear the filename feedback

            in_memory_run = BenchmarkResult(
                file_count=file_count,
                setup_time=compilation_time,
                total_parsing_time=total_in_memory_time,
                avg_parsing_time=total_in_memory_time / file_count if file_count else 0,
                avg_lines_sec=total_lines / total_in_memory_time if total_in_memory_time else 0,
            )
            generated_run = BenchmarkResult(
                file_count=file_count,
                setup_time=generation_time,
                total_parsing_time=total_generated_time,
                avg_parsing_time=total_generated_time / file_count if file_count else 0,
                avg_lines_sec=total_lines / total_generated_time if total_generated_time else 0,
            )
            return in_memory_run, generated_run
        finally:
            if temp_parser_path.exists():
                temp_parser_path.unlink()
    finally:
        sys.setrecursionlimit(prevreclimit)


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
        print(f"grammar: {grammar_path.relative_to(Path.cwd())}")
        print(f"input files: {len(args.inputs)}")

        in_memory_run, generated_run = benchmark(args.grammar, args.inputs)
        print_summary(
            str(args.grammar),
            len(args.inputs),
            in_memory_run,
            generated_run,
        )
    except Exception as e:
        print(f"\nan error occurred: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()

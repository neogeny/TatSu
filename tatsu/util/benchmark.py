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


def benchmark_in_memory(
    grammar_path: str | Path,
    input_paths: Iterable[Path],
) -> BenchmarkResult:
    grammar_path = Path(grammar_path)
    grammar_text = grammar_path.read_text(encoding='utf-8')

    with timer() as t:
        model = tatsu.compile(grammar_text)
    compilation_time = t.delta

    total_parsing_time = 0.0
    file_count = 0
    lines_sec = 0
    for input_path in input_paths:
        print(f"{f'{input_path.name}...':60}", end='\r')
        input_text = try_read(input_path)
        with timer() as t:
            model.parse(input_text)
        total_parsing_time += t.delta
        lines_sec += countlines(input_text).code / t.delta
        file_count += 1
    print()

    return BenchmarkResult(
        file_count=file_count,
        setup_time=compilation_time,
        total_parsing_time=total_parsing_time,
        avg_parsing_time=total_parsing_time / file_count if file_count else 0,
        avg_lines_sec=lines_sec / file_count if file_count else 0,
    )


def benchmark_generated_parser(
    grammar_path: Path,
    input_paths: Iterable[Path],
) -> BenchmarkResult:
    grammar_name = 'Benchmark'
    grammar_text = grammar_path.read_text(encoding='utf-8')

    # --- One-time setup: Code generation and import ---
    total_parsing_time = 0.0
    file_count = 0
    lines_sec = 0
    temp_parser_filename = f"temp_parser_{int(time.time())}.py"
    temp_parser_path = Path(temp_parser_filename).resolve()
    try:
        with timer() as tgen:
            python_source = tatsu.to_python_sourcecode(grammar_text, name=grammar_name)
            temp_parser_path.write_text(python_source, encoding='utf-8')

            spec = importlib.util.spec_from_file_location(
                "temp_generated_parser", temp_parser_path
            )
            if not (spec and spec.loader):
                raise ImportError("Could not create module spec")

            module = importlib.util.module_from_spec(spec)
            sys.modules["temp_generated_parser"] = module
            spec.loader.exec_module(module)

            expected_class_name = f"{grammar_name}Parser"
            parser_class = getattr(module, expected_class_name, None)

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
                raise RuntimeError(
                    "Could not find a generated Parser class in the module."
                )

            parser_instance = parser_class()
        generation_time = tgen.delta
        # --- End one-time setup ---

        for input_path in input_paths:
            print(f"{f'{input_path.name}...':60}", end='\r')
            input_text = try_read(input_path)
            with timer() as t:
                parser_instance.parse(input_text)
            total_parsing_time += t.delta
            lines_sec += countlines(input_text).code / t.delta
            file_count += 1
        print()
    finally:
        if temp_parser_path.exists():
            temp_parser_path.unlink()

    return BenchmarkResult(
        file_count=file_count,
        setup_time=generation_time,
        total_parsing_time=total_parsing_time,
        avg_parsing_time=total_parsing_time / file_count if file_count else 0,
        avg_lines_sec=lines_sec / file_count if file_count else 0,
    )


def print_summary(
    grammar: str,
    count: int,
    compile_time: float,
    in_memory_run: BenchmarkResult,
    generated_run: BenchmarkResult,
):
    print(f"Grammar: {grammar}")
    print(f"Input files: {count}")

    w = 32
    print()
    print("\n--- One-time Grammar Compilation ---")
    print(f"{'One-time compilation:':{w}}{compile_time:.2f} s")

    print("\n--- In-memory Model ---")
    print(f"{'One-time setup:':{w}}{in_memory_run.setup_time:.2f} s")
    print(
        f"{f'Total parsing time ({in_memory_run.file_count} files):':{w}}"
        f"{in_memory_run.total_parsing_time:.2f} s"
    )
    print(
        f"{'Average parsing time:':{w}}" f"{in_memory_run.avg_parsing_time:.2f} s/file"
    )
    print(f"{'Average speed:':{w - 3}}" f"{in_memory_run.avg_lines_sec:.0f} sloc/sec")

    print("\n--- Generated Python Parser ---")
    print(f"{'One-time code generation:':{w}}" f"{generated_run.setup_time:.2f}")
    print(
        f"{f'Total parsing time ({generated_run.file_count} files):':{w}}"
        f"{generated_run.total_parsing_time:.2f} s"
    )
    print(
        f"{'Average parsing time:':{w}}" f"{generated_run.avg_parsing_time:.2f} s/file"
    )
    print(f"{'Average speed:':{w - 3}}" f"{generated_run.avg_lines_sec:.0f} sloc/sec")

    print("\n--- Comparison (Average Parsing Time) ---")
    model_avg_sloc = in_memory_run.avg_lines_sec
    gen_avg_sloc = generated_run.avg_lines_sec
    print(f"{'In-memory':{w - 3}}{model_avg_sloc:.0f} sloc/sec")
    print(f"{'Generated:':{w - 3}}{gen_avg_sloc:.0f} sloc/sec")

    if gen_avg_sloc < model_avg_sloc:
        factor = model_avg_sloc / gen_avg_sloc
        print(f"Generated parser is {factor:.2f}x SLOWER on average")
    else:
        factor = gen_avg_sloc / model_avg_sloc
        print(f"Generated parser is {factor:.2f}x FASTER on average")


def benchmark(
    grammar: str | Path,
    filenames: Iterable[str | Path],
) -> tuple[BenchmarkResult, BenchmarkResult]:
    grammar = Path(grammar)
    prevreclimit = sys.getrecursionlimit()
    sys.setrecursionlimit(2**16)
    try:
        filepaths = [Path(f) for f in filenames]
        in_memory_run = benchmark_in_memory(grammar, filepaths)
        generated_run = benchmark_generated_parser(grammar, filepaths)
        return in_memory_run, generated_run
    finally:
        sys.setrecursionlimit(prevreclimit)


def main():
    parser = argparse.ArgumentParser(description="Benchmark TatSu parsing methods")
    parser.add_argument("grammar", type=Path, help="Path to the grammar file")
    parser.add_argument(
        "inputs", type=Path, nargs='+', help="Path to one or more input text files"
    )
    args = parser.parse_args()

    for p in [args.grammar, *args.inputs]:
        if not p.exists():
            print(f"Error: File '{p}' not found.")
            sys.exit(1)

    try:
        with timer() as t:
            tatsu.compile(Path(args.grammar).read_text())
        one_time_time = t.delta
        in_memory_run, generated_run = benchmark(args.grammar, args.inputs)
        print_summary(
            args.grammar,
            len(args.inputs),
            one_time_time,
            in_memory_run,
            generated_run,
        )
    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        raise
        sys.exit(1)


if __name__ == "__main__":
    main()

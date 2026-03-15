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
    average_parsing_time: float


def benchmark_in_memory(
    grammar_path: Path, input_paths: Iterable[Path]
) -> BenchmarkResult:
    grammar_text = grammar_path.read_text(encoding='utf-8')

    start_compile = time.time()
    model = tatsu.compile(grammar_text)
    end_compile = time.time()
    compilation_time = end_compile - start_compile

    total_parsing_time = 0.0
    file_count = 0
    for input_path in input_paths:
        print(f"  Parsing {input_path.name} (in-memory)...")
        input_text = input_path.read_text(encoding='utf-8')
        start_parse = time.time()
        model.parse(input_text)
        end_parse = time.time()
        total_parsing_time += end_parse - start_parse
        file_count += 1

    return BenchmarkResult(
        file_count=file_count,
        setup_time=compilation_time,
        total_parsing_time=total_parsing_time,
        average_parsing_time=total_parsing_time / file_count if file_count else 0,
    )


def benchmark_generated_parser(
    grammar_path: Path, input_paths: Iterable[Path]
) -> BenchmarkResult:
    grammar_name = 'Benchmark'
    grammar_text = grammar_path.read_text(encoding='utf-8')

    # --- One-time setup: Code generation and import ---
    start_gen = time.time()
    python_source = tatsu.to_python_sourcecode(grammar_text, name=grammar_name)

    # FIXME
    # We still need the model to get the grammar name for the parser class
    # model = tatsu.compile(grammar_text, name=default_name)
    # grammar_name = model.name or default_name

    temp_parser_filename = f"temp_parser_{int(time.time())}.py"
    temp_parser_path = Path(temp_parser_filename).resolve()
    temp_parser_path.write_text(python_source, encoding='utf-8')

    total_parsing_time = 0.0
    file_count = 0
    try:
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
            raise RuntimeError("Could not find a generated Parser class in the module.")

        parser_instance = parser_class()
        end_gen = time.time()
        generation_time = end_gen - start_gen
        # --- End one-time setup ---

        for input_path in input_paths:
            print(f"  Parsing {input_path.name} (generated)...")
            input_text = input_path.read_text(encoding='utf-8')
            start_parse = time.time()
            parser_instance.parse(input_text)
            end_parse = time.time()
            total_parsing_time += end_parse - start_parse
            file_count += 1

    finally:
        if temp_parser_path.exists():
            temp_parser_path.unlink()

    return BenchmarkResult(
        file_count=file_count,
        setup_time=generation_time,
        total_parsing_time=total_parsing_time,
        average_parsing_time=total_parsing_time / file_count if file_count else 0,
    )


def print_summary(in_memory_run: BenchmarkResult, generated_run: BenchmarkResult):
    print("\n--- In-memory Model ---")
    print(f"One-time compilation: {in_memory_run.setup_time:.4f}s")
    print(
        f"Total parsing time ({in_memory_run.file_count} files): "
        f"{in_memory_run.total_parsing_time:.4f}s"
    )
    print(f"Average parsing time: {in_memory_run.average_parsing_time:.4f}s/file")

    print("\n--- Generated Python Parser ---")
    print(f"One-time code generation: {generated_run.setup_time:.4f}s")
    print(
        f"Total parsing time ({generated_run.file_count} files): "
        f"{generated_run.total_parsing_time:.4f}s"
    )
    print(f"Average parsing time: {generated_run.average_parsing_time:.4f}s/file")

    print("\n--- Comparison (Average Parsing Time) ---")
    model_avg_time = in_memory_run.average_parsing_time
    gen_avg_time = generated_run.average_parsing_time
    print(f"In-memory: {model_avg_time:.4f}s/file")
    print(f"Generated: {gen_avg_time:.4f}s/file")

    if gen_avg_time < model_avg_time:
        factor = model_avg_time / gen_avg_time
        print(f"Generated parser is {factor:.2f}x FASTER on average")
    else:
        factor = gen_avg_time / model_avg_time
        print(f"Generated parser is {factor:.2f}x SLOWER on average")


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

    print(f"Grammar: {args.grammar}")
    print(f"Input files: {len(args.inputs)}")

    try:
        in_memory_run = benchmark_in_memory(args.grammar, args.inputs)
        generated_run = benchmark_generated_parser(args.grammar, args.inputs)
        print_summary(in_memory_run, generated_run)
    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

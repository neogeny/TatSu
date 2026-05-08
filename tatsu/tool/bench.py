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


have_tiexiu: bool = False
try:
    # noinspection PyUnusedImports
    import tiexiu  # type: ignore

    have_tiexiu = True
except ImportError:
    pass

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
    lines_parsed: int
    error_count: int
    failed_files: list[str]  # Added this field
    setup_time: float
    total_parsing_time: float
    avg_parsing_time: float
    avg_lines_sec: float


def _setup_mem_parser(grammar_src: str) -> tuple[grammars.Grammar, float]:
    with timer() as t:
        model = compile(grammar_src)
    return model, t.delta


def _setup_gen_parser(
    grammar_src: str,
    grammar_name: str,
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


def _print_run_details(
    title: str,
    result: BenchmarkResult,
    lbl_w: int,
    num_fmt: str,
    verbose: bool,
):
    print(f"\n--- {title} ---")
    print(f"typename: {result.typename}")
    print(f"{'one-time setup:':<{lbl_w}}{num_fmt.format(result.setup_time)} s")
    print(
        f"{f'total parsing time ({result.file_count} files):':<{lbl_w}}"
        f"{num_fmt.format(result.total_parsing_time)} s",
    )
    err_pct = 100 * result.error_count / result.file_count
    print(
        f"{f'errors ({result.error_count}/{result.file_count} files):':<{lbl_w}}"
        f"{num_fmt.format(err_pct)} %",
    )
    if verbose and result.failed_files:
        print(f"{'failed files:':<{lbl_w}}{', '.join(result.failed_files)}")
    print(
        f"{'average parsing time:':<{lbl_w}}{num_fmt.format(result.avg_parsing_time)} s/file",
    )
    print(f"{'average speed:':<{lbl_w}}{num_fmt.format(result.avg_lines_sec)} sloc/sec")


def print_performance_comparison(results: list[tuple[str, BenchmarkResult]]):
    if not results:
        return

    # Map full names to mnemonics and collect speeds
    mnemonic_map = {
        "in-memory": "mem",
        "generated": "gen",
        "tiexiu": "xiu",
    }

    # Filter out results that don't have a mnemonic mapping
    # and create a list of (mnemonic, speed) tuples
    parsed_results = []
    for name, res in results:
        mnemonic = mnemonic_map.get(name.lower())
        if mnemonic:
            parsed_results.append((mnemonic, res.avg_lines_sec))

    if len(parsed_results) < 2:
        # Not enough results for a comparison table
        return

    # Prepare data for the table
    mnemonics = [r[0] for r in parsed_results]
    _speeds = [r[1] for r in parsed_results]

    # Determine column width for numbers
    max_mnemonic_len = max(len(m) for m in mnemonics)
    col_width = max(
        max_mnemonic_len + 4,
        7,
    )  # Mnemonic (N) + padding, or min width for numbers

    # Print header row
    header = f"{'':<{col_width}}"
    for mnem in mnemonics:
        header += f"{mnem + ' ':>{col_width}}"
    print(header)

    # Print data rows
    for i, (row_mnemonic, row_speed) in enumerate(parsed_results):
        row_str = f"{row_mnemonic}"
        row_str = f"{row_str:>{col_width - 1}}"
        for j, (_col_mnemonic, col_speed) in enumerate(parsed_results):
            if i == j:
                row_str += f"{'-':>{col_width}}"
            else:
                if col_speed == 0:
                    ratio_str = "inf"
                else:
                    ratio = row_speed / col_speed
                    ratio_str = f"{ratio:>{col_width}.2f}"
                row_str += ratio_str
        print(row_str)


def print_summary(
    grammar: str,
    count: int,
    mem_run: BenchmarkResult | None,
    gen_run: BenchmarkResult | None,
    tiexiu_run: BenchmarkResult | None,
    verbose: bool = False,
):
    relgrammar = Path(grammar).resolve().relative_to(Path.cwd())
    print(f"grammar: {relgrammar}")
    print(f"input files: {count}")

    all_runs = [r for r in [mem_run, gen_run, tiexiu_run] if r is not None]
    all_numbers = []
    for r in all_runs:
        all_numbers.extend(
            [
                r.setup_time,
                r.total_parsing_time,
                r.avg_parsing_time,
                r.avg_lines_sec,
            ],
        )

    int_width = max(len(str(int(abs(n)))) for n in all_numbers) if all_numbers else 0
    num_width = int_width + 3
    num_fmt = f"{{:>{num_width}.2f}}"

    count_width = len(str(count))
    longest_label = f"total parsing time ({'9' * count_width} files):"
    labels = [
        "one-time setup:",
        longest_label,
        "average parsing time:",
        "average speed:",
        "in-memory:",
        "generated:",
        "tiexiu:",
        "failed files:",  # Added for label width calculation
    ]
    lbl_w = max(len(lbl) for lbl in labels) + 2

    if mem_run:
        _print_run_details("in-memory model", mem_run, lbl_w, num_fmt, verbose)
    if gen_run:
        _print_run_details("generated python parser", gen_run, lbl_w, num_fmt, verbose)
    if tiexiu_run:
        _print_run_details("tiexiu (rust) parser", tiexiu_run, lbl_w, num_fmt, verbose)

    comparison_results = []
    if mem_run:
        comparison_results.append(("in-memory", mem_run))
    if gen_run:
        comparison_results.append(("generated", gen_run))
    if tiexiu_run:
        comparison_results.append(("tiexiu", tiexiu_run))

    if len(comparison_results) > 1:
        print("\n--- comparison (sloc/sec ratios) ---")
        # The previous verbose comparison printout is removed,
        # and now print_performance_comparison will handle the table.
        print_performance_comparison(comparison_results)


def benchmark(
    grammar: str | Path,
    filenames: Iterable[str | Path],
    mode: str = 'all',
) -> tuple[BenchmarkResult | None, BenchmarkResult | None, BenchmarkResult | None]:
    oldlimit = sys.getrecursionlimit()
    sys.setrecursionlimit(2**16)
    try:
        grampath = Path(grammar)
        gramsrc = grampath.read_text(encoding="utf-8")

        model, memsetup = _setup_mem_parser(gramsrc)
        gramname = model.name or "Benchmark"

        filepaths = [Path(f) for f in filenames]
        texts = [try_read(p) for p in filepaths]
        nfiles = len(texts)

        memrun = None
        if mode in {'mem', 'both', 'all'}:
            memtime = 0.0
            memerrs = 0
            lines_parsed = 0
            mem_failed: list[str] = []
            for i, text in enumerate(texts):
                pct = int((i + 1) / nfiles * 100)
                print(f"[Mem {pct:3d}%] Benchmarking memory parser...", end="\r")
                with timer() as t:
                    try:
                        model.parse(text, asmodel=True)
                        lines_parsed += countlines(text).code
                    except FailedParse:
                        memerrs += 1
                        mem_failed.append(str(filepaths[i]))
                    memtime += t.delta
            memrun = BenchmarkResult(
                typename(model),
                file_count=nfiles,
                error_count=memerrs,
                lines_parsed=lines_parsed,
                failed_files=mem_failed,
                setup_time=memsetup,
                total_parsing_time=memtime,
                avg_parsing_time=memtime / nfiles if nfiles else 0,
                avg_lines_sec=lines_parsed / memtime if memtime else 0,
            )

        # --- Loop 2: Generated Parser ---
        genrun = None
        if mode in {'gen', 'both', 'all'}:
            parser, gensetup, parserpath = _setup_gen_parser(gramsrc, gramname)
            gensetup += memsetup  # Account for initial grammar compilation
            gentime = 0.0
            generrs = 0
            gen_failed: list[str] = []
            lines_parsed = 0
            for i, text in enumerate(texts):
                pct = int((i + 1) / nfiles * 100)
                print(f"[Gen {pct:3d}%] Benchmarking generated parser...", end="\r")
                with timer() as t:
                    try:
                        parser.parse(text, asmodel=True)
                        lines_parsed += countlines(text).code
                    except FailedParse:
                        generrs += 1
                        gen_failed.append(str(filepaths[i]))
                    gentime += t.delta
            genrun = BenchmarkResult(
                typename(parser),
                file_count=nfiles,
                error_count=generrs,
                lines_parsed=lines_parsed,
                failed_files=gen_failed,
                setup_time=gensetup,
                total_parsing_time=gentime,
                avg_parsing_time=gentime / nfiles if nfiles else 0,
                avg_lines_sec=lines_parsed / gentime if gentime else 0,
            )
            parserpath.unlink()

        tiexiu_run = None
        if mode in {'tiexiu', 'all'} and have_tiexiu:
            tiexiu_time = 0.0
            tiexiu_errs = 0
            lines_parsed = 0
            tiexiu_failed: list[str] = []
            # Tiexiu setup is basically zero (it parses the grammar on every call currently)
            # or it might have a one-time overhead for the first call
            peg = tiexiu.pegapi()  # type: ignore
            with timer() as t:
                peg.compile(gramsrc)
                tiesetup = t.delta
            for i, text in enumerate(texts):
                pct = int((i + 1) / nfiles * 100)
                print(f"[Xiu {pct:3d}%] Benchmarking tiexiu parser...", end="\r")
                with timer() as t:
                    try:
                        peg.parse_to_json_string(
                            gramsrc, text, source=str(filepaths[i])
                        )
                        lines_parsed += countlines(text).code
                    except ValueError as e:
                        tiexiu_errs += 1
                        tiexiu_failed.append(f"{filepaths[i]} (Error: {e})")
                    except Exception as e:  # Catching other unexpected errors
                        tiexiu_errs += 1
                        tiexiu_failed.append(
                            f"{filepaths[i]} (Unexpected: {type(e).__name__}: {e})",
                        )
                    tiexiu_time += t.delta
            tiexiu_run = BenchmarkResult(
                "tiexiu.parse",
                file_count=nfiles,
                error_count=tiexiu_errs,
                lines_parsed=lines_parsed,
                failed_files=tiexiu_failed,
                setup_time=tiesetup,
                total_parsing_time=tiexiu_time,
                avg_parsing_time=tiexiu_time / nfiles if nfiles else 0,
                avg_lines_sec=lines_parsed / tiexiu_time if tiexiu_time else 0,
            )

        print(" " * 75)  # Clear the status line

        return memrun, genrun, tiexiu_run
    finally:
        sys.setrecursionlimit(oldlimit)


def main():
    parser = argparse.ArgumentParser(description="benchmark tatsu parsing methods")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        '--all',
        help='benchmark all types of parser (default)',
        dest='mode',
        action='store_const',
        const='all',
        default='all',
    )
    mode.add_argument(
        '--both',
        help='benchmark both tatsu types of parser (mem and gen)',
        dest='mode',
        action='store_const',
        const='both',
    )
    mode.add_argument(
        '--mem',
        help='benchmark in-memory parser',
        dest='mode',
        action='store_const',
        const='mem',
    )
    mode.add_argument(
        '--gen',
        help='benchmark generated parser',
        dest='mode',
        action='store_const',
        const='gen',
    )
    mode.add_argument(
        '--tiexiu',
        help='benchmark tiexiu parser',
        dest='mode',
        action='store_const',
        const='tiexiu',
    )
    parser.add_argument(
        '--verbose',
        help='show error output from failed parses',
        action='store_true',
    )
    parser.add_argument("grammar", type=Path, help="path to the grammar file")
    parser.add_argument(
        "inputs",
        type=Path,
        nargs='+',
        help="path to one or more input text files",
    )
    args = parser.parse_args()

    for p in [args.grammar, *args.inputs]:
        if not p.exists():
            print(f"error: file '{p}' not found.")
            sys.exit(1)

    if args.mode in {'tiexiu', 'all'} and not have_tiexiu:
        print("warning: tiexiu not found, skipping tiexiu benchmark.")
        if args.mode == 'tiexiu':
            sys.exit(1)

    try:
        grammar_path = args.grammar.resolve()
        input_paths = [p.resolve() for p in args.inputs]
        mem_run, gen_run, tiexiu_run = benchmark(
            grammar_path,
            input_paths,
            mode=args.mode,
        )
        print_summary(
            str(args.grammar),
            len(args.inputs),
            mem_run,
            gen_run,
            tiexiu_run,
            verbose=args.verbose,
        )
    except Exception as e:
        print(f"\nan error occurred: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()

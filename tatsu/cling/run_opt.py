# Copyright © 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .global_opt import add_global_options


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
        "-M",
        "--model",
        action="store_true",
        dest="model",
        help="Output a Python model of the output",
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

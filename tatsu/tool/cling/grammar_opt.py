# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from argparse import ArgumentParser


def add_grammar_options(parser: ArgumentParser):
    parser.add_argument(
        "-z",
        "--optimized",
        action="store_true",
        default=False,
        help="Use the optimized version of the grammar",
    )
    format = parser.add_mutually_exclusive_group()
    format.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="json",
        default=True,
        help="Output the grammar in JSON format",
    )
    format.add_argument(
        "-m",
        "--model",
        action="store_true",
        dest="model",
        help="Output the model code according to the grammar",
    )
    format.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        dest="pretty",
        help="Output the grammar in pretty-printed EBNF format",
    )
    format.add_argument(
        "-r",
        "--railroads",
        action="store_true",
        dest="railroads",
        help="Output a railroad diagram of the grammar",
    )

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
        help="output the grammar model in JSON format (default)",
    )
    format.add_argument(
        "-m",
        "--model",
        action="store_true",
        dest="model",
        help="output a Python object model of the grammar",
    )
    format.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        dest="pretty",
        help="output the grammar in pretty-printed EBNF format",
    )
    format.add_argument(
        '-y',
        '--pretty-lean',
        help='like --pretty, but without name= or [Parameter] annotations',
        action='store_true',
    )
    format.add_argument(
        "-r",
        "--railroads",
        action="store_true",
        dest="railroads",
        help="output a railroad diagram of the grammar",
    )
    format.add_argument(
        '-g',
        '--object-model',
        help='an AST model from the class names as rule parameters',
        action='store_true',
    )
    format.add_argument(
        "-e",
        "--generate-parser",
        action="store_true",
        help='generate a procedural parser from the grammar',
    )
    format.add_argument(
        "-x",
        "--parser-model",
        action="store_true",
        help='generate a model-based parser from the grammar',
    )

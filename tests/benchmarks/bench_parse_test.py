# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from pathlib import Path

import pytest

import tatsu
from tatsu.parser import TatSuParserGenerator
from tatsu.tool import to_python_sourcecode

CALC_GRAMMAR = r"""
    @@grammar::CALC

    start: expression $

    expression:
        | expression '+' term
        | expression '-' term
        | term

    term:
        | term '*' factor
        | term '/' factor
        | factor

    factor:
        | '(' expression ')'
        | number

    number: /\d+/
"""

@pytest.mark.benchmark
def test_bench_compile_calc_grammar():
    """Benchmark compiling a simple calculator grammar."""
    tatsu.compile(CALC_GRAMMAR)


@pytest.mark.benchmark
def test_bench_parse_arithmetic_expression():
    """Benchmark parsing an arithmetic expression with a compiled grammar."""
    parser = tatsu.compile(CALC_GRAMMAR)
    parser.parse("3 + 5 * ( 10 - 20 )")


@pytest.mark.benchmark
def test_bench_compile_tatsu_grammar():
    """Benchmark compiling the full TatSu grammar (self-hosting)."""
    text = tatsu.grammar
    g = TatSuParserGenerator("TatSuBootstrap")
    g.parse(text)


@pytest.mark.benchmark
def test_bench_codegen_calc_grammar():
    """Benchmark generating Python source code from a grammar."""
    to_python_sourcecode(CALC_GRAMMAR)


@pytest.mark.benchmark
def test_bench_parse_complex_expression():
    """Benchmark parsing a more complex nested expression."""
    parser = tatsu.compile(CALC_GRAMMAR)
    parser.parse("((1 + 2) * (3 + 4)) + ((5 - 6) * (7 + 8)) - 9 * (10 + 11)")

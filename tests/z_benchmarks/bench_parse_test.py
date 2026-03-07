# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from pathlib import Path

import pytest

import tatsu
from tatsu.parser import TatSuParserGenerator
from tatsu.tool import to_python_sourcecode

from .. import z_bootstrap_test as boottest

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


@pytest.mark.benchmark
def test_bench_bootstrap():
    boottest.test_00_with_boostrap_grammar()
    boottest.test_01_with_parser_generator()
    boottest.test_02_previous_output_generator()
    boottest.test_03_repeat_02()
    boottest.test_04_repeat_03()
    boottest.test_05_parse_with_model()
    boottest.test_06_generate_code()
    boottest.test_07_import_generated_code()
    boottest.test_08_compile_with_generated()
    boottest.test_09_parser_with_semantics()
    boottest.test_10_with_model_and_semantics()
    boottest.test_11_with_pickle_and_retry()
    boottest.test_12_walker()
    boottest.test_13_diagram()

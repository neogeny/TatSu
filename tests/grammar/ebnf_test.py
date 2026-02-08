# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import pytest

import tatsu
from tatsu import grammars

EBNF_CALC_GRAMMAR = r"""
@@grammar :: TatSu

start := expression $
expression := expression '+' term | expression '-' term | term


term := term '*' factor | term '/' factor | factor


factor := '(' expression ')' | number


number := /\d+/
"""


@pytest.mark.skip
def test_parse_ebnf():
    model = tatsu.compile(EBNF_CALC_GRAMMAR, asmodel=True)
    assert isinstance(model, grammars.Grammar)

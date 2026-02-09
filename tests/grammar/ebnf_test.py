# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import tatsu
from tatsu import grammars


def test_parse_ebnf():
    grammar = r"""
        @@grammar :: TatSu

        start := expression $

        expression := expression '+' term | expression '-' term | term

        term := term '*' factor | term '/' factor | factor

        factor := '(' expression ')' | number

        number := /\d+/
    """

    model = tatsu.compile(grammar, asmodel=True)
    assert isinstance(model, grammars.Grammar)

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from tatsu.exceptions import GrammarError
from tatsu.tool import compile
from tatsu.util.asjson import asjsons


def test_missing_rule():
    grammar = """
        @@grammar::TestGrammar
          block = test ;
    """
    try:
        model = compile(grammar)
        print('MODEL', asjsons(model))
        model.parse('abc')
    except GrammarError as e:
        assert str(e) == 'Unknown rules, no parser generated:\ntest'


def test_missing_rules():
    grammar = """
        @@grammar::TestGrammar
          block = test | test2;
    """
    try:
        model = compile(grammar)
        print('MODEL', asjsons(model))
        model.parse('abc')
    except GrammarError as e:
        assert str(e) == 'Unknown rules, no parser generated:\ntest\ntest2'

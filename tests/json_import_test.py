# Copyright (c) 2026 Juancarlo Anez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import json
from pathlib import Path

import pytest  # noqa # type: ignore

from tatsu.grammars import json as json_import


GRAMMAR_DIR = Path() / 'grammar'


def test_grammar_from_json_calc():
    calc_json = GRAMMAR_DIR / 'calc.json'
    grammar = json_import.loads_grammar(calc_json.read_text())
    assert grammar.name == 'CALC'
    assert len(grammar.rules) == 9
    assert grammar.rules[0].name == 'start'


def test_grammar_from_json_tatsu():
    tatsu_json = GRAMMAR_DIR / 'tatsu.json'
    grammar = json_import.loads_grammar(tatsu_json.read_text())
    assert grammar.name == 'TatSu'
    assert len(grammar.rules) > 50


def test_grammar_from_json_value():
    calc_json = GRAMMAR_DIR / 'calc.json'
    value = json.loads(calc_json.read_text())
    grammar = json_import.load_grammar(value)
    assert grammar.name == 'CALC'


def test_rule_from_json_value():
    calc_json = GRAMMAR_DIR / 'calc.json'
    value = json.loads(calc_json.read_text())
    rule_value = value['rules'][0]
    rule = json_import.rule_from_json_value(rule_value)
    assert rule.name == 'start'


def test_exp_from_json_value():
    rule_value = {
        '__class__': 'Rule',
        'name': 'test',
        'exp': {
            '__class__': 'Sequence',
            'sequence': [
                {'__class__': 'Token', 'token': 'hello'},
                {'__class__': 'EOF'},
            ],
        },
        'params': [],
    }
    rule = json_import.rule_from_json_value(rule_value)
    assert rule.name == 'test'


def test_parse_with_imported_calc_grammar():
    calc_json = GRAMMAR_DIR / 'calc.json'
    grammar = json_import.loads_grammar(calc_json.read_text())

    result = grammar.parse('123')
    assert result == '123'

    result = grammar.parse('1 + 2')
    assert 'left' in result
    assert 'right' in result


def test_import_all_expression_types():
    expressions = [
        {
            '__class__': 'Sequence',
            'sequence': [
                {'__class__': 'Void'},
            ],
        },
        {
            '__class__': 'Choice',
            'options': [
                {'__class__': 'Option', 'exp': {'__class__': 'Void'}},
            ],
        },
        {'__class__': 'Option', 'exp': {'__class__': 'Void'}},
        {'__class__': 'Named', 'name': 'test', 'exp': {'__class__': 'Void'}},
        {'__class__': 'NamedList', 'name': 'test', 'exp': {'__class__': 'Void'}},
        {'__class__': 'Call', 'name': 'foo'},
        {'__class__': 'Token', 'token': 'hello'},
        {'__class__': 'Pattern', 'pattern': r'\d+'},
        {'__class__': 'Constant', 'literal': 'test'},
        {'__class__': 'Alert', 'literal': 'warning', 'level': 1},
        {'__class__': 'Group', 'exp': {'__class__': 'Void'}},
        {'__class__': 'Optional', 'exp': {'__class__': 'Void'}},
        {'__class__': 'Closure', 'exp': {'__class__': 'Void'}},
        {'__class__': 'PositiveClosure', 'exp': {'__class__': 'Void'}},
        {'__class__': 'Lookahead', 'exp': {'__class__': 'Void'}},
        {'__class__': 'NegativeLookahead', 'exp': {'__class__': 'Void'}},
        {'__class__': 'SkipGroup', 'exp': {'__class__': 'Void'}},
        {'__class__': 'SkipTo', 'exp': {'__class__': 'Void'}},
        {'__class__': 'Override', 'exp': {'__class__': 'Void'}},
        {'__class__': 'OverrideList', 'exp': {'__class__': 'Void'}},
        {
            '__class__': 'Join',
            'exp': {'__class__': 'Void'},
            'sep': {'__class__': 'Token', 'token': ','},
        },
        {
            '__class__': 'PositiveJoin',
            'exp': {'__class__': 'Void'},
            'sep': {'__class__': 'Token', 'token': ','},
        },
        {
            '__class__': 'Gather',
            'exp': {'__class__': 'Void'},
            'sep': {'__class__': 'Token', 'token': ','},
        },
        {
            '__class__': 'PositiveGather',
            'exp': {'__class__': 'Void'},
            'sep': {'__class__': 'Token', 'token': ','},
        },
        {'__class__': 'RuleInclude', 'name': 'foo'},
        {'__class__': 'Void'},
        {'__class__': 'Cut'},
        {'__class__': 'EOF'},
        {'__class__': 'EOL'},
        {'__class__': 'EmptyClosure'},
    ]

    for expr in expressions:
        result = json_import.exp_from_json_value(expr)
        assert result is not None


def test_import_keywords():
    value = {
        '__class__': 'Grammar',
        'name': 'Test',
        'rules': [
            {
                '__class__': 'Rule',
                'name': 'start',
                'exp': {'__class__': 'Sequence', 'sequence': []},
                'params': [],
            },
        ],
        'keywords': ['if', 'else', 'while'],
    }
    grammar = json_import.load_grammar(value)
    assert grammar.name == 'Test'


def test_roundtrip_calc():
    calc_json = GRAMMAR_DIR / 'calc.json'
    original = json.loads(calc_json.read_text())

    grammar = json_import.load_grammar(original)
    exported = grammar.asjson()

    assert exported['name'] == original['name']
    assert len(exported['rules']) == len(original['rules'])

    reimported = json_import.load_grammar(exported)
    assert reimported.name == grammar.name
    assert len(reimported.rules) == len(grammar.rules)

    result1 = grammar.parse('1 + 2')
    result2 = reimported.parse('1 + 2')
    assert result1 == result2

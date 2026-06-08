# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import math

import pytest

import tatsu
from tatsu.exceptions import FailedParse


def test_name_matches_identifier():
    ast = tatsu.parse('start = @name $ ;', 'hello')
    assert ast == 'hello'


def test_name_matches_underscore_start():
    ast = tatsu.parse('start = @name $ ;', '_hello')
    assert ast == '_hello'


def test_name_rejects_digit_start():
    with pytest.raises(FailedParse):
        tatsu.parse('start = @name $ ;', '1hello')


def test_int_matches_signed():
    ast = tatsu.parse('start = @int $ ;', '+42')
    assert ast == 42
    assert isinstance(ast, int)


def test_int_matches_negative():
    ast = tatsu.parse('start = @int $ ;', '-7')
    assert ast == -7


def test_int_matches_unsigned():
    ast = tatsu.parse('start = @int $ ;', '99')
    assert ast == 99


def test_int_rejects_float():
    with pytest.raises(FailedParse):
        tatsu.parse('start = @int $ ;', '3.14')


def test_int_rejects_empty():
    with pytest.raises(FailedParse):
        tatsu.parse('start = @int $ ;', '')


def test_uint_matches_unsigned():
    ast = tatsu.parse('start = @uint $ ;', '42')
    assert ast == 42
    assert isinstance(ast, int)


def test_uint_rejects_negative():
    with pytest.raises(FailedParse):
        tatsu.parse('start = @uint $ ;', '-5')


def test_uint_rejects_plus():
    with pytest.raises(FailedParse):
        tatsu.parse('start = @uint $ ;', '+5')


def test_uint_with_underscores():
    ast = tatsu.parse('start = @uint $ ;', '1_000_000')
    assert ast == 1000000


def test_float_matches_simple():
    ast = tatsu.parse('start = @float $ ;', str(math.pi))
    assert math.isclose(ast, math.pi)
    assert isinstance(ast, float)


def test_float_matches_negative():
    ast = tatsu.parse('start = @float $ ;', '-2.5')
    assert math.isclose(ast, -2.5)


def test_float_rejects_text():
    with pytest.raises(FailedParse):
        tatsu.parse('start = @float $ ;', 'abc')


def test_bool_matches_true():
    ast = tatsu.parse('start = @bool $ ;', 'true')
    assert ast is True


def test_bool_matches_capitalized_true():
    ast = tatsu.parse('start = @bool $ ;', 'True')
    assert ast is True


def test_meta_in_named():
    ast = tatsu.parse('start = value=@int $ ;', '42')
    assert ast == {'value': 42}


def test_meta_in_sequence():
    ast = tatsu.parse('start = @name "=" @int $ ;', 'x=7')
    assert ast == ['x', '=', 7]


def test_meta_as_atom():
    ast = tatsu.parse('start = @name $ ;', 'hello')
    assert ast == 'hello'

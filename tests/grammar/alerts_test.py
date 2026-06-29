# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from tatsu.api import compile
from tatsu.util.asjson import asjsons  # noqa: F401


def test_alert_interpolation(trace=False):
    input = '42 69'
    grammar = r"""
            start = a:number b: number i:^`"seen: {a}, {b}"` $ ;
            number::int = /\d+/ ;
    """
    model = compile(grammar)
    # print(asjsons(model))
    ast = model.parse(input, trace=trace)
    assert ast == {'a': '42', 'b': '69', 'i': None}
    ast = model.parse(input, asmodel=True, trace=trace)
    assert ast == {'a': 42, 'b': 69, 'i': None}

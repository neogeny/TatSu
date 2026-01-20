from __future__ import annotations

from tatsu.tool import compile
from tatsu.util import asjsons


def test_alert_interpolation(trace=True):
    input = '42 69'
    grammar = r"""
            start = a:number b: number i:^`"seen: {a}, {b}"` $ ;
            number = /\d+/ ;
    """
    model = compile(grammar)
    print(asjsons(model))
    ast = model.parse(input, trace=trace)
    assert ast == {'a': '42', 'b': '69', 'i': 'seen: 42, 69'}

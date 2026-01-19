from __future__ import annotations

from tatsu.tool import compile


def test_alert_interpolation():
    input = '42 69'
    grammar = r"""
            start = a:number b: number i:^`"seen: {a}, {b}"` $ ;
            number = /\d+/ ;
    """
    model = compile(grammar)
    print(model)
    ast = model.parse(input)
    assert ast == {'a': '42', 'b': '69', 'i': 'seen: 42, 69'}

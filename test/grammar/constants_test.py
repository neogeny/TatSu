from __future__ import annotations

from tatsu.tool import parse


def test_constant_interpolation():
    input = '42 69'
    grammar = r'''
            start = a:number b: number i:`"seen: {a}, {b}"` $ ;
            number = /\d+/ ;
    '''
    assert parse(grammar, input) == {'a': '42', 'b': '69', 'i': 'seen: 42, 69'}


def test_constant_interpolation_free():
    input = '42 69'
    grammar = r'''
            start = a:number b: number i:`seen: {a}, {b}` $ ;
            number = /\d+/ ;
    '''
    assert parse(grammar, input) == {'a': '42', 'b': '69', 'i': 'seen: 42, 69'}


def test_constant_interpolation_multiline():
    input = '42 69'
    grammar = r'''
            start = a:number b: number
            i:```
            seen:
            {a}
            {b}
            ``` $ ;
            number = /\d+/ ;
    '''

    result = parse(grammar, input)
    print(result)
    assert result == {'a': '42', 'b': '69', 'i': 'seen:\n42\n69\n'}


def test_evaluate_constant():
    grammar = '''
        @@grammar :: constants
        start = int bool str null 'a' $;

        int = `42` ;
        bool = `True` ;
        str = `Something` ;
        null = `None` ;
    '''

    ast = parse(grammar, 'a')
    assert ast == (42, True, 'Something', None, 'a')

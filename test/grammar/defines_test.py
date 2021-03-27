from __future__ import annotations

import pytest

from tatsu.tool import compile, gencode


# @pytest.mark.skip('working on it')
def test_name_in_option():
    grammar = '''
        start = expr_range ;

        expr_range =
            | [from: expr] '..' [to: expr]
            | expr
            ;

        expr =
            /[\d]+/
        ;
    '''

    model = compile(grammar)

    ast = model.parse('1 .. 10')
    assert ast == {'from': '1', 'to': '10'}

    ast = model.parse('10')
    assert ast == '10'

    ast = model.parse(' .. 10')
    assert ast == {'from': None, 'to': '10'}

    ast = model.parse('1 .. ')
    assert ast == {'from': '1', 'to': None}

    ast = model.parse(' .. ')
    assert ast == '..'

    code = gencode(grammar=grammar)
    print(code)

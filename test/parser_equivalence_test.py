import types

import pytest  # noqa

import tatsu
from tatsu.exceptions import FailedParse

INPUT = """
    1d3
"""
OUTPUT = {'number_of_dice': '1', 'sides': '3'}

GRAMMAR = """
    start = expression $;

    int = /-?\d+/ ;

    dice = number_of_dice:factor /d|D/ sides:factor;

    expression = addition ;

    addition
        =
        | left:dice_expr op:('+' | '-') ~ right:addition
        | dice_expr
        ;

    dice_expr
        =
        | dice
        | factor
        ;

    factor
        =
        | '(' ~ @:expression ')'
        | int
        ;
"""


def generate_and_load_parser(name, grammar):
    code = tatsu.to_python_sourcecode(grammar, name='Test')
    print(code)
    module = types.ModuleType(name)
    module.__file__ = '<generated>'
    exec(compile(code, module.__file__, 'exec'), module.__dict__)  # pylint: disable=exec-used
    return module.TestParser()  # noqa, pylint: disable=no-member


def test_model_parse():
    model = tatsu.compile(name='Test', grammar=GRAMMAR)
    assert OUTPUT == model.parse(INPUT)


def test_codegen_parse():
    parser = generate_and_load_parser('test_codegen_parse', GRAMMAR)
    output = parser.parse(INPUT, parseinfo=False)
    assert output == OUTPUT


# @pytest.mark.skip('work in progress')
def test_error_messages():
    grammar = '''
        @@grammar :: ORDER
        alphabet = a b others $ ;

        a = 'a' ;
        b = 'b' ;
        others = 'c' | 'd' | 'e' | 'f' |'g' | 'h' | 'i' | 'j' | 'k' | 'l' | 'm' | 'n' | 'o';
    '''
    input = 'a b'

    e1 = None
    model = tatsu.compile(grammar)
    try:
        model.parse(input)
    except FailedParse as e:  # noqa
        e1 = str(e)
    assert "expecting one of: 'c' 'd' 'e' 'f' 'g' 'h' 'i' 'j' 'k' 'l' 'm' 'n' 'o'" in e1


# @pytest.mark.skip('work in progress')
def test_name_checked():
    grammar = '''
        @@grammar :: Test
        @@ignorecase :: True
        @@keyword :: if

        start = rule ;
        rule = @:word if_exp $ ;
        if_exp = 'if' digit ;
        @name word = /\w+/ ;
        digit = /\d/ ;
    '''

    def subtest(parser):
        parser.parse('nonIF if 1', trace=False)
        with pytest.raises(FailedParse):
            parser.parse('if if 1', trace=False)
        with pytest.raises(FailedParse):
            parser.parse('IF if 1', trace=False)

    parser = tatsu.compile(grammar, 'Test')
    subtest(parser)
    parser = generate_and_load_parser('test_name_checked', grammar)
    subtest(parser)


def test_first_rule():
    grammar = '''
        @@grammar :: Test

        true = 'test' @: `True` $ ;
        start = 'test' @: `False` $ ;
    '''
    parser = tatsu.compile(grammar, 'Test')
    ast = parser.parse('test')
    assert ast is True
    parser = generate_and_load_parser('test_first_rule', grammar)
    ast = parser.parse('test')
    assert ast is True


def test_dynamic_compiled_ast():
    grammar = '''
        test::Test = 'TEST' ['A' a:number] ['B' b:number] ;
        number::int = /\d+/ ;
    '''

    parser = tatsu.compile(grammar)

    code = tatsu.to_python_sourcecode(grammar, name='Test', filename='test.py')
    module = types.ModuleType('test')
    module.__file__ = 'test.py'
    exec(compile(code, module.__file__, 'exec'), module.__dict__)  # pylint: disable=exec-used

    dynamic_ast = parser.parse('TEST')
    compiled_ast = module.TestParser().parse('TEST', start='test')  # pylint: disable=no-member
    assert dynamic_ast == compiled_ast

    dynamic_ast = parser.parse('TEST A 1')
    compiled_ast = module.TestParser().parse('TEST A 1', start='test')  # pylint: disable=no-member
    assert dynamic_ast == compiled_ast


import subprocess  # noqa
import py_compile  # noqa
from pathlib import Path

import pytest  # noqa

from tatsu.exceptions import FailedParse
from tatsu.tool import compile, gencode

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
        | left:addition op:('+' | '-') ~ right:addition
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


def compile_run(grammar, input, output):
    parser = gencode(name='Test', grammar=grammar)
    parser_filename = Path('./tmp/test_codegen_parser.py')
    with open(parser_filename, 'wt') as f:
        f.write(parser)
    try:
        try:
            from tmp.test_codegen_parser import UnknownParser as Parser  # pylint: disable=all
        except ImportError:
            from tmp.test_codegen_parser import TestParser as Parser  # pylint: disable=all
        output = Parser().parse(input, parseinfo=False)
        assert output == output
    finally:
        pass
        # init_filename.unlink()
        # input_filename.unlink()
        # parser_filename.unlink()


def test_model_parse():
    model = compile(grammar=GRAMMAR)
    assert OUTPUT == model.parse(INPUT)


# @pytest.mark.skip('work in progress')
def test_codegen_parse():
    tmp_dir = Path('./tmp')
    tmp_dir.mkdir(parents=True, exist_ok=True)
    init_filename = Path('./tmp/__init__.py')
    init_filename.touch(exist_ok=True)

    input_filename = Path('./tmp/input.txt')
    with open(input_filename, 'wt') as f:
        f.write(INPUT)

    compile_run(GRAMMAR, INPUT, OUTPUT)


def test_error_messages():
    grammar = '''
        @@grammar :: ORDER
        alphabet = a b others $ ;

        a = 'a' ;
        b = 'b' ;
        others = 'c' | 'd' | 'e' | 'f' |'g' | 'h' | 'i' | 'j' | 'k' | 'l' | 'm' | 'n' | 'o';
    '''
    input = 'a b'

    model = compile(grammar)
    try:
        model.parse(input)
    except FailedParse as e1:  # noqa
        pass

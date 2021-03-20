
import subprocess  # noqa
import py_compile  # noqa
from pathlib import Path

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

def test_model_parse():
    model = compile(grammar=GRAMMAR)
    assert OUTPUT == model.parse(INPUT)


def test_codegen_parse():
    init_filename = Path('./tmp/__init__.py')
    init_filename.touch(exist_ok=True)

    input_filename = Path('./tmp/input.txt')
    with open(input_filename, 'wt') as f:
        f.write(INPUT)

    parser = gencode(name='Test', grammar=GRAMMAR)
    parser_filename = Path('./tmp/parser.py')
    with open(parser_filename, 'wt') as f:
        f.write(parser)

    try:
        # py_compile.compile(parser_filename, doraise=True)
        # output = subprocess.check_output(
        #     ['python3', parser_filename, '-t', input_filename],
        #     env={
        #         'PYTHONPATH': '.',
        #     }
        # ).decode()
        # print(output)
        from tmp.parser import UnknownParser
        output = UnknownParser().parse(INPUT)
        assert output == OUTPUT
    finally:
        init_filename.unlink()
        input_filename.unlink()
        parser_filename.unlink()

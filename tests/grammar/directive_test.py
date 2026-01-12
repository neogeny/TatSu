import pytest

import tatsu
from tatsu.exceptions import FailedParse
from tatsu.ngcodegen import codegen
from tatsu.util import trim

EXEC = 'exec'


def test_whitespace_directive():
    grammar = """
        @@whitespace :: /[\t ]+/

        test = "test" $;
    """
    model = tatsu.compile(grammar, 'test')
    code = codegen(model)
    compile('test.py', code, EXEC)


def test_whitespace_none_directive():
    grammars = [
        """
            @@whitespace :: None
            @@nameguard :: False

            test = {'x'}+ $;
        """,
        """
            @@whitespace :: False
            @@nameguard :: False

            test = {'x'}+ $;
        """,
    ]
    for grammar in grammars:
        model = tatsu.compile(grammar, 'test')
        assert model.parse('xx', trace=True) == ['x', 'x']
        with pytest.raises(FailedParse):
            model.parse('x x', trace=True)


def test_whitespace_escaping():
    grammar = r'''
    @@grammar::Markdown
    @@whitespace :: /[ ]/
    start = pieces $ ;
    text = text:/[a-z]+/ ;
    pieces = {text}* ;
    '''

    with pytest.raises(FailedParse):
        tatsu.parse(grammar, '[]')


def test_default_whitespace():
    grammar = r"""
        start = {'x'}+ $;
    """

    tatsu.parse(grammar, "x x x")


def test_eol_comments_re_directive():
    grammar = """
        @@eol_comments :: /#.*?$/

        test = "test" $;
    """
    model = tatsu.compile(grammar, 'test')
    code = codegen(model)
    compile(code, 'test.py', EXEC)


def test_left_recursion_directive():
    grammar = """
        @@left_recursion :: False

        test = "test" $;
    """
    model = tatsu.compile(grammar, 'test')
    assert not model.directives.get('left_recursion')
    assert not model.config.left_recursion

    code = codegen(model)
    compile('test.py', code, EXEC)


def test_whitespace_no_newlines():
    grammar = """
        @@whitespace :: /[\t ]+/
        # this is just a token with any character but space and newline
        # it should finish before it capture space or newline character
        token = /[^ \n]+/;
        # expect whitespace to capture spaces between tokens, but newline
        # should be captured afterwards
        token2 = {token}* /\n/;
        # document is just list of this strings of tokens
        document = {@+:token2}* $;
    """
    text = trim(
        """\
        a b
        c d
        e f
    """,
    )

    expected = [(['a', 'b'], '\n'), (['c', 'd'], '\n'), (['e', 'f'], '\n')]

    model = tatsu.compile(grammar, 'document')
    ast = model.parse(text, start='document')
    assert expected == ast


def test_grammar_directive():
    grammar = """
        @@grammar :: Test

        start = test $;
        test = "test";
    """
    model = tatsu.compile(grammar)
    assert model.directives.get('grammar') == 'Test'
    assert model.name == 'Test'

    code = codegen(model)
    module = compile(code, 'test.py', EXEC)

    assert 'TestParser' in module.co_names


def test_parseinfo_directive():
    grammar = """
        @@parseinfo
        @@parseinfo :: True

        test = value:"test" $;
    """
    model = tatsu.compile(grammar, 'test')
    ast = model.parse('test')
    assert ast.parseinfo is not None

    code = codegen(model)
    print(code)
    assert 'parseinfo=True' in code
    compile(code, 'test.py', EXEC)

    grammar = """
        @@parseinfo :: False

        test = value:"test" $;
    """
    model = tatsu.compile(grammar, 'test')
    ast = model.parse('test')
    assert ast.parseinfo is None

    code = codegen(model)
    assert 'parseinfo=False' in code
    compile(code, 'test.py', EXEC)


def test_nameguard_directive():
    grammar = """
        @@grammar :: test
        @@nameguard :: False
        @@namechars :: ''

        start = sequence $ ;
        sequence = {digit}+ ;
        digit = 'x' | '1' | '2' | '3' | '4' | '5' ;
    """

    model = tatsu.compile(grammar)
    assert not model.config.nameguard
    assert model.parse('23') == ['2', '3']
    assert model.parse('xx') == ['x', 'x']

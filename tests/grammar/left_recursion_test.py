# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import pytest

from tatsu.exceptions import FailedParse
from tatsu.tool import compile, parse


def test_direct_left_recursion(trace=False):
    grammar = """
        @@left_recursion :: True
        start
            =
            expre $
            ;

        expre
            =
            | expre '+' factor
            | expre '-' factor
            | expre '*' factor
            | expre '/' factor
            | factor
            ;

        factor
            =
            | '(' @:expre ')'
            | number
            ;

        number
            =
            /[0-9]+/
            ;
    """
    model = compile(grammar, 'test')

    ast = model.parse('1*2+3*5', trace=trace, colorize=True)
    assert ast == ((('1', '*', '2'), '+', '3'), '*', '5')

    ast = model.parse('10 - 20', trace=trace, colorize=True)
    assert ast == ('10', '-', '20')

    ast = model.parse('( 10 - 20 )', trace=trace, colorize=True)
    assert ast == ('10', '-', '20')

    ast = model.parse('3 + 5 * ( 10 - 20 )', trace=trace, colorize=True)
    assert ast == (('3', '+', '5'), '*', ('10', '-', '20'))


def test_calc(trace=False):
    grammar = r"""
        @@grammar::CALC


        start
            =
            expression $
            ;


        expression
            =
            | expression '+' term
            | expression '-' term
            | term
            ;


        term
            =
            | term '*' factor
            | term '/' factor
            | factor
            ;


        factor
            =
            | '(' @:expression ')'
            | number
            ;

        number
            =
            /\d+/
            ;
    """
    model = compile(grammar)

    ast = model.parse('10 - 20', trace=trace, colorize=True)
    assert ast == ('10', '-', '20')

    ast = model.parse('( 10 - 20 )', trace=trace, colorize=True)
    assert ast == ('10', '-', '20')

    ast = model.parse('3 + 5 * ( 10 - 20)', trace=trace, colorize=True)
    assert ast == ('3', '+', ('5', '*', ('10', '-', '20')))


def test_calc_indirect(trace=False):
    grammar = r"""
        @@grammar::CALC
        @@left_recursion :: True

        start = expression $;
        number = /\d+/;

        addition = expression '+' number;
        subtraction = expression '-' number;

        expression =
            | addition
            | subtraction
            | number;
    """
    model = compile(grammar)
    ast = model.parse('1-1+1', trace=trace, colorize=True)
    assert ast == (('1', '-', '1'), '+', '1')

    ast = model.parse('1+1-1', trace=trace, colorize=True)
    assert ast == (('1', '+', '1'), '-', '1')

    from tatsu.tool import to_python_sourcecode

    src = to_python_sourcecode(grammar)
    globs = {}
    exec(src, globs)
    parser = globs["CALCParser"]()
    print(parser.parse('1-1+1', trace=trace))


def test_indirect_left_recursion(trace=False):
    grammar = """
        @@left_recursion :: True
        start = x $ ;
        x = expr ;
        expr = x '-' num | num;
        num = /[0-9]+/ ;
    """
    model = compile(grammar, 'test')
    ast = model.parse('5-87-32', trace=trace, colorize=True)
    assert ast == (('5', '-', '87'), '-', '32')


def test_indirect_left_recursion_with_cut(trace=False):
    grammar = """
        @@left_recursion :: True
        start = x $ ;
        x = expr ;
        expr = x '-' ~ num | num;
        num = /[0-9]+/ ;
    """
    model = compile(grammar, 'test')
    ast = model.parse('5-87-32', trace=trace, colorize=True)
    print(ast)
    assert ast == (('5', '-', '87'), '-', '32')


def test_indirect_left_recursion_complex(trace=False):
    grammar = """
        @@left_recursion :: True
        start
            =
            Primary $
            ;

        Primary
            =
            PrimaryNoNewArray
            ;

        PrimaryNoNewArray
            =
            | ClassInstanceCreationExpression
            | MethodInvocation
            | FieldAccess
            | ArrayAccess
            | 'this'
            ;

        ClassInstanceCreationExpression
            =
            | 'new' ClassOrInterfaceType '(' ')'
            | Primary '.new' Identifier '()'
            ;

        MethodInvocation
            =
            | MethodName '()'
            | Primary '.' MethodName '()'
            ;

        FieldAccess
            =
            | Primary '.' Identifier
            | 'super.' Identifier
            ;

        ArrayAccess
            =
            | Primary '[' Expression ']'
            | ExpressionName '[' Expression ']'
            ;

        ClassOrInterfaceType
            =
            | ClassName
            | InterfaceTypeName
            ;

        ClassName
            =
            'C' | 'D'
            ;

        InterfaceTypeName
            =
            'I' | 'J'
            ;

        Identifier
            =
            | 'x' | 'y'
            | ClassOrInterfaceType
            ;

        MethodName = 'm' | 'n' ;

        ExpressionName = Identifier ;

        Expression = 'i' | 'j' ;
    """
    model = compile(grammar, 'test')
    ast = model.parse('this', trace=trace, colorize=True)
    assert ast == 'this'
    ast = model.parse('this.x', trace=trace, colorize=True)
    assert ast == ('this', '.', 'x')
    ast = model.parse('this.x.y', trace=trace, colorize=True)
    assert ast == (('this', '.', 'x'), '.', 'y')
    ast = model.parse('this.x.m()', trace=trace, colorize=True)
    assert ast == (('this', '.', 'x'), '.', 'm', '()')
    ast = model.parse('x[i][j].y', trace=trace, colorize=True)
    assert ast == ((('x', '[', 'i', ']'), '[', 'j', ']'), '.', 'y')


def test_no_left_recursion(trace=False):
    grammar = """
        @@left_recursion :: True
        start
            =
            expre $
            ;

        expre
            =
            expre '+' number
            |
            expre '*' number
            |
            number
            ;

        number
            =
            /[0-9]+/
            ;
    """
    model = compile(grammar, 'test')
    model.parse('1*2+3*5', trace=trace, colorize=True)
    with pytest.raises(FailedParse, match=r'infinite left recursion'):
        model.parse('1*2+3*5', left_recursion=False, trace=trace, colorize=True)


def test_nested_left_recursion(trace=False):
    grammar_a = """
        @@left_recursion :: True
        s = e $ ;
        e = [e '+'] t ;
        t = [t '*'] a ;
        a = /[0-9]/ ;
    """
    grammar_b = """
        @@left_recursion :: True
        s = e $ ;
        e = [e '+'] a ;
        a = n | p ;
        n = /[0-9]/ ;
        p = '(' @:e ')' ;
    """
    model_a = compile(grammar_a, 'test')
    model_b = compile(grammar_b, 'test')
    ast = model_a.parse('1*2+3*4', trace=trace, colorize=True)
    assert ast == (('1', '*', '2'), '+', ('3', '*', '4'))
    ast = model_b.parse('(1+2)+(3+4)', trace=trace, colorize=True)
    assert ast == (('1', '+', '2'), '+', ('3', '+', '4'))
    ast = model_a.parse('1*2*3', trace=trace, colorize=True)
    assert ast == (('1', '*', '2'), '*', '3')
    ast = model_b.parse('(((1+2)))', trace=trace, colorize=True)
    assert ast == ('1', '+', '2')


@pytest.mark.skip('For this the seed growing during left recursion is too primitive')
def test_interlocking_cycles(trace=False):
    # See https://github.com/PhilippeSigaud/Pegged/wiki/Left-Recursion
    grammar = """
        @@left_recursion :: False
        @@nameguard :: False

        s = e $;
        e = f 'n' | 'n';
        f = e '+' {i} | g '-';
        g = h 'm' | e;
        h = g 'l';
        i = '(' {i}+ ')';
        a = 'a';
    """

    model = compile(grammar)
    model.parse('nlm-n+(aaa)n', trace=trace, colorize=True)


@pytest.mark.skip('Similar to the one above')
def test_mutual_left_recursion(trace=False):
    # See https://github.com/PhilippeSigaud/Pegged/wiki/Left-Recursion
    grammar = """
        @@left_recursion :: True
        @@nameguard :: False

        s = l $;
        l = p '.x' | 'x';
        p = p '(n)' | l;
    """

    model = compile(grammar)
    model.parse('x(n).x')


def test_left_recursion_bug(trace=False):
    grammar = """\
        @@grammar :: Minus
        @@left_recursion :: True

        start = expression $ ;

        expression =
            | minus_expression
            | paren_expression
            | value
            ;

        paren_expression
            =
            '(' expression ')'
            ;

        minus_expression
            =
            expression '-' expression
            ;

        value = /[0-9]+/ ;
    """
    model = compile(grammar=grammar)
    model.parse('3', trace=trace, colorize=True)
    model.parse('3 - 2', trace=trace, colorize=True)
    model.parse('(3 - 2)', trace=trace, colorize=True)
    model.parse('(3 - 2) - 1', trace=trace, colorize=True)
    model.parse('3 - 2 - 1', trace=trace, colorize=True)
    model.parse('3 - (2 - 1)', trace=trace, colorize=True)


def test_left_recursion_with_right_associativity(trace=False):
    # by Nicolas LAURENT in eg@lists.csail.mit.edu
    grammar = """
        @@left_recursion :: True

        s = e $ ;
        e = e '+' e | n ;
        n = /[0-9]+/ ;
    """
    model = compile(grammar, 'test')
    ast = model.parse('1+2+3', trace=trace, colorize=True)
    assert ast == ('1', '+', ('2', '+', '3'))


def test_partial_input_bug(trace=False):
    grammar = r"""
        start
            =
            expre
            ;

        expre
            =
            | '{' expre '}'
            | expre '->' identifier
            | identifier
            ;

        identifier
            =
            /\w+/
            ;
    """

    input = """
        { size } test
    """

    model = compile(grammar)
    ast = model.parse(input, trace=trace, colorize=True)
    assert ast == ('{', 'size', '}')


def test_dropped_input_bug(trace=False):
    grammar = r"""
        @@left_recursion :: True

        start = expr;

        expr
            =
            | expr ',' expr
            | identifier
            ;

        identifier
            =
            /\w+/
            ;
    """
    model = compile(grammar)

    ast = model.parse('foo', trace=trace, colorize=True)
    assert ast == 'foo'

    ast = model.parse('foo bar', trace=trace, colorize=True)
    assert ast == 'foo'

    ast = model.parse('foo, bar', trace=trace, colorize=True)
    assert ast == ('foo', ',', 'bar')


def test_change_start_rule(trace=False):
    grammar = r"""
        start = expr ;

        expr
            =
            mul | identifier
            ;

        mul
            =
            expr '*' identifier
            ;

        identifier
            =
            /\w+/
            ;
    """
    model = compile(grammar)

    ast = model.parse('a * b', start='expr', trace=trace, colorize=True)
    assert ast == ('a', '*', 'b')

    with pytest.raises(FailedParse, match=r'infinite left recursion'):
        model.parse('a * b', start='mul', trace=trace, colorize=True)


def test_with_gather(trace=False):
    grammar = r"""
        identifier = /\w+/ ;
        expr = mul | tmp ;
        mul = expr '*' tmp ;
        tmp = call | identifier ;
        call = identifier '(' ','.{expr} ')' ;
    """
    model = compile(grammar)

    ast = model.parse('a(b, c)', start='expr', trace=trace, colorize=True)
    assert ast == ('a', '(', ['b', 'c'], ')')


def test_not_at_top_level():
    grammar = r"""
        identifier = /\w+/ ;

        type = (vector_type | leaf_type) ;
        vector_type = base:type '[]' ;
        leaf_type = id:identifier ;

        decl = type:type name:identifier ;
    """
    assert parse(grammar, 'int x', start='decl').asjson() == {
        'type': {'id': 'int'},
        'name': 'x',
    }


def test_peg_associativity():
    left_grammar = """
        @@left_recursion :: True
        @@nameguard :: False

        start = A $ ;
        A = | A 'a' | 'a' ;
    """

    assert parse(left_grammar, 'aaa') == (('a', 'a'), 'a')

    right_grammar = """
        @@left_recursion :: True
        @@nameguard :: False

        start = A $ ;
        A = | 'a' A | 'a' ;
    """

    assert parse(right_grammar, 'aaa') == ('a', ('a', 'a'))

    mixed_grammar = """
        @@left_recursion :: True
        @@nameguard :: False

        start = A $ ;
        A = | A 'a' | 'a' A | 'a' ;
    """

    assert parse(mixed_grammar, 'aaa') == ('a', ('a', 'a'))  # associated RIGHT


def test_nullable_void():
    left_grammar = """
        @@left_recursion :: True
        @@nameguard :: False

        start = A $ ;
        A = | A 'a' | () ;
    """

    assert parse(left_grammar, 'aaa') == (('a', 'a'), 'a')


def test_leftrec_with_void():
    left_grammar = """
        @@left_recursion :: True
        @@nameguard :: False

        start = A | () ;
        A = | A 'a' | 'a' ;
    """

    assert parse(left_grammar, 'aaa') == (('a', 'a'), 'a')
    assert parse(left_grammar, '') is None

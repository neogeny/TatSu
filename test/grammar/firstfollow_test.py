# -*- coding: utf-8 -*-
from __future__ import generator_stop

import unittest

from tatsu.tool import compile
from tatsu import grammars
from tatsu.grammars import ref


class FirstFollowTests(unittest.TestCase):
    def test_direct_left_recursion(self, trace=False):
        grammar = '''
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
                ?/[0-9]+/?
                ;
        '''
        model = compile(grammar, "test")
        expre = model.rulemap['expre']
        factor = model.rulemap['factor']
        number = model.rulemap['number']

        assert isinstance(expre.exp, grammars.Choice)

        assert expre.is_leftrec

        assert ref('expre') in expre.lookahead()

        assert ref('factor') in expre.lookahead()
        assert ref('factor') not in factor.lookahead()

        assert ref('number') in expre.lookahead()
        assert ref('number') in factor.lookahead()
        assert ref('number') not in number.lookahead()

    def test_indirect_left_recursion(self, trace=False):
        grammar = '''
            @@left_recursion :: True
            start = x $ ;
            x = expr ;
            expr = x '-' num | num;
            num = ?/[0-9]+/? ;
        '''
        model = compile(grammar, "test")
        x = model.rulemap['x']
        expr = model.rulemap['expr']
        num = model.rulemap['num']

        assert x.is_leftrec
        assert not expr.is_leftrec
        assert not num.is_leftrec

        assert not x.is_memoizable
        assert not expr.is_memoizable
        assert num.is_memoizable

        print('x', x.lookahead())
        print('expr', expr.lookahead())

        assert ref('x') in x.lookahead()
        assert ref('expr') in expr.lookahead()

    def test_nullability(self):
        grammar = '''
            start = e;
            e = p f;
            p = [e '+'] ;
            f = '0';
        '''
        model = compile(grammar, "test")
        e = model.rulemap['e']
        p = model.rulemap['p']
        f = model.rulemap['f']
        assert f  # to avoid linters

        assert e.is_leftrec
        assert not p.is_leftrec
        assert p.is_nullable()
        assert not p.is_memoizable  # it is part of a recursive loop

        assert ref('e') in e.lookahead()
        assert ref('p') in p.lookahead()

        print(p.lookahead())
        print(p.exp.lookahead())
        assert () in p.exp.lookahead()  # nullable

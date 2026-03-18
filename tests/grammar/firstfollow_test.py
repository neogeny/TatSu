# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import unittest

from tatsu import grammars as g
from tatsu.tool import compile


class FirstFollowTests(unittest.TestCase):
    def test_direct_left_recursion(self, trace=False):
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
        expre = model.rulemap['expre']
        factor = model.rulemap['factor']
        number = model.rulemap['number']

        assert isinstance(expre.exp, g.Choice)

        assert expre.is_leftrec

        assert g.ref('expre') in expre.lookahead()

        assert g.ref('factor') in expre.lookahead()
        assert g.ref('factor') not in factor.lookahead()

        assert g.ref('number') in expre.lookahead()
        assert g.ref('number') in factor.lookahead()
        assert g.ref('number') not in number.lookahead()

    def test_indirect_left_recursion(self, trace=False):
        grammar = """
            @@left_recursion :: True
            start = x $ ;
            x = expr ;
            expr = x '-' num | num;
            num = /[0-9]+/ ;
        """
        model = compile(grammar, 'test')
        start = model.rulemap['start']
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

        assert g.ref('x') in x.lookahead()
        assert g.ref('expr') in expr.lookahead()

        assert g.ref('start') not in start.lookahead()

    def test_nullability(self):
        grammar = """
            start = e;
            e = p f;
            p = [e '+'] ;
            f = '0';
        """
        model = compile(grammar, 'test')
        e = model.rulemap['e']
        p = model.rulemap['p']
        f = model.rulemap['f']
        assert f  # to avoid linters

        assert e.is_leftrec
        assert not p.is_leftrec
        assert p.is_nullable()
        assert not p.is_memoizable  # it is part of a recursive loop

        assert g.ref('e') in e.lookahead()
        assert g.ref('p') in p.lookahead()

        print(p.lookahead())
        print(p.exp.lookahead())
        assert () in p.exp.lookahead()  # nullable

# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

from tatsu.exceptions import FailedParse
from tatsu.tool import compile


class LeftRecursionTests(unittest.TestCase):

    def test_direct_left_recursion(self, trace=False):
        grammar = '''
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
                ?/[0-9]+/?
                ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("1*2+3*5", trace=trace, colorize=True)
        self.assertEqual([[['1', '*', '2'], '+', '3'], '*', '5'], ast)

    def test_indirect_left_recursion(self, trace=False):
        grammar = '''
            @@left_recursion :: True
            start = x $ ;
            x = expr ;
            expr = x '-' num | num;
            num = ?/[0-9]+/? ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("5-87-32", trace=trace, colorize=True)
        self.assertEqual([['5', '-', '87'], '-', '32'], ast)

    def test_indirect_left_recursion_with_cut(self, trace=False):
        grammar = '''
            @@left_recursion :: True
            start = x $ ;
            x = expr ;
            expr = x '-' ~ num | num;
            num = ?/[0-9]+/? ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("5-87-32", trace=trace, colorize=True)
        print(ast)
        self.assertEqual([['5', '-', '87'], '-', '32'], ast)

    @unittest.skip('uncertain if grammar is correct')
    def test_indirect_left_recursion_complex(self, trace=False):
        grammar = '''
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
        '''
        model = compile(grammar, "test")
        ast = model.parse("this", trace=trace, colorize=True)
        self.assertEqual('this', ast)
        ast = model.parse("this.x", trace=True, colorize=True)
        self.assertEqual(['this', '.', 'x'], ast)
        ast = model.parse("this.x.y", trace=trace, colorize=True)
        self.assertEqual([['this', '.', 'x'], '.', 'y'], ast)
        ast = model.parse("this.x.m()", trace=trace, colorize=True)
        self.assertEqual([['this', '.', 'x'], '.', 'm', '()'], ast)
        ast = model.parse("x[i][j].y", trace=trace, colorize=True)
        print(ast)
        self.assertEqual([[['x', '[', 'i', ']'], '[', 'j', ']'], '.', 'y'], ast)

    def test_no_left_recursion(self, trace=False):
        grammar = '''
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
                ?/[0-9]+/?
                ;
        '''
        model = compile(grammar, "test")
        model.parse("1*2+3*5", trace=trace, colorize=True)
        try:
            model.parse("1*2+3*5", left_recursion=False, trace=trace, colorize=True)
            self.fail('expected left recursion failure')
        except FailedParse:
            pass

    def test_nested_left_recursion(self, trace=False):
        grammar_a = '''
            @@left_recursion :: True
            s = e $ ;
            e = [e '+'] t ;
            t = [t '*'] a ;
            a = ?/[0-9]/? ;
        '''
        grammar_b = '''
            @@left_recursion :: True
            s = e $ ;
            e = [e '+'] a ;
            a = n | p ;
            n = ?/[0-9]/? ;
            p = '(' @:e ')' ;
        '''
        model_a = compile(grammar_a, "test")
        model_b = compile(grammar_b, "test")
        ast = model_a.parse("1*2+3*4", trace=trace, colorize=True)
        self.assertEqual([['1', '*', '2'], '+', ['3', '*', '4']], ast)
        ast = model_b.parse("(1+2)+(3+4)", trace=trace, colorize=True)
        self.assertEqual([['1', '+', '2'], '+', ['3', '+', '4']], ast)
        ast = model_a.parse("1*2*3", trace=trace, colorize=True)
        self.assertEqual([['1', '*', '2'], '*', '3'], ast)
        ast = model_b.parse("(((1+2)))", trace=trace, colorize=True)
        self.assertEqual(['1', '+', '2'], ast)

    def test_left_recursion_bug(self, trace=False):
        grammar = '''\
            @@grammar :: Minus
            @@left_recursion :: True

            start = expression $ ;

            expression =
                | paren_expression
                | minus_expression
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
        '''
        model = compile(grammar=grammar)
        model.parse('3', trace=trace, colorize=True)
        model.parse('3 - 2', trace=True, colorize=True)
        model.parse('(3 - 2)', trace=trace, colorize=True)
        model.parse('(3 - 2) - 1', trace=trace, colorize=True)
        model.parse('3 - 2 - 1', trace=trace, colorize=True)
        model.parse('3 - (2 - 1)', trace=trace, colorize=True)

    def test_left_recursion_with_right_associativity(self, trace=False):
        # by Nicolas LAURENT in eg@lists.csail.mit.edu
        grammar = '''
            @@left_recursion :: True

            s = e $ ;
            e = e '+' e | n ;
            n = /[0-9]+/ ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("1+2+3", trace=trace, colorize=True)
        self.assertEqual(['1', '+', ['2', '+', '3']], ast)

    def test_partial_input_bug(self, trace=False):
        grammar = '''
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
        '''

        input = '''
            { size } test
        '''

        model = compile(grammar)
        ast = model.parse(input, trace=trace, colorize=True)
        assert ['{', 'size', '}'] == ast

    def test_dropped_input_bug(self, trace=False):
        grammar = '''
            @@left_recursion :: True

            start
                =
                expr
                ;

            expr
                =
                | expr ',' expr
                | identifier
                ;

            identifier
                =
                /\w+/
                ;
        '''
        model = compile(grammar)

        ast = model.parse('foo', trace=trace, colorize=True)
        self.assertEqual('foo', ast)

        ast = model.parse('foo bar', trace=trace, colorize=True)
        self.assertEqual('foo', ast)

        ast = model.parse('foo, bar', trace=trace, colorize=True)
        self.assertEqual(['foo', ',', 'bar'], ast)

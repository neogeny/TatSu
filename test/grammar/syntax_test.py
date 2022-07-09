# -*- coding: utf-8 -*-
import unittest

from tatsu.exceptions import FailedParse
from tatsu.tool import compile
from tatsu.util import trim
from tatsu.codegen import codegen
from tatsu.grammars import EBNFBuffer


class SyntaxTests(unittest.TestCase):
    def test_update_ast(self):
        grammar = '''
            foo = name:"1" [ name: bar ] ;
            bar = { "2" } * ;
        '''
        m = compile(grammar, 'Keywords')
        ast = m.parse('1 2')
        self.assertEqual(['1', ['2']], ast.name)

        grammar = '''
            start = items: { item } * $ ;
            item = @:{ subitem } * "0" ;
            subitem = ?/1+/? ;
        '''
        m = compile(grammar, 'Update')
        ast = m.parse("1101110100", nameguard=False)
        self.assertEqual([['11'], ['111'], ['1'], []], ast.items_)

    def test_include_and_override(self):
        gr = 'included_grammar'
        included_grammar = "plu = 'aaaa';"

        overridden = "%s@override\nplu = 'plu';"
        inclusion = '#include :: %s.ebnf\n' % gr

        including_grammar = overridden % (inclusion)
        whole_grammar = overridden % (included_grammar)

        class FakeIncludesBuffer(EBNFBuffer):
            def get_include(self, source, filename):
                return included_grammar, source + '/' + filename

        compile(FakeIncludesBuffer(whole_grammar), "test")
        compile(FakeIncludesBuffer(including_grammar), "test")

    def test_ast_assignment(self):
        grammar = '''
            n  = @: {"a"}* $ ;
            f  = @+: {"a"}* $ ;
            nn = @: {"a"}*  @: {"b"}* $ ;
            nf = @: {"a"}*  @+: {"b"}* $ ;
            fn = @+: {"a"}* @: {"b"}* $ ;
            ff = @+: {"a"}* @+: {"b"}* $ ;
        '''

        model = compile(grammar, "test")

        def p(input, rule):
            return model.parse(input, start=rule, whitespace='')

        e = self.assertEqual

        e([], p('', 'n'))
        e(['a'], p('a', 'n'))
        e(['a', 'a'], p('aa', 'n'))

        e([[]], p('', 'f'))
        e([['a']], p('a', 'f'))
        e([['a', 'a']], p('aa', 'f'))

        for r in ('nn', 'nf', 'fn', 'ff'):
            e([[], []], p('', r))
            e([['a'], []], p('a', r))
            e([[], ['b']], p('b', r))
            e([['a', 'a'], []], p('aa', r))
            e([[], ['b', 'b']], p('bb', r))
            e([['a', 'a'], ['b']], p('aab', r))

    def test_optional_closure(self):
        grammar = 'start = foo+:"x" foo:{"y"}* {foo:"z"}* ;'
        model = compile(grammar, "test")
        ast = model.parse("xyyzz", nameguard=False)
        self.assertEqual(['x', ['y', 'y'], 'z', 'z'], ast.foo)

        grammar = 'start = foo+:"x" [foo+:{"y"}*] {foo:"z"}* ;'
        model = compile(grammar, "test")
        ast = model.parse("xyyzz", nameguard=False)
        self.assertEqual(['x', ['y', 'y'], 'z', 'z'], ast.foo)

        grammar = 'start = foo+:"x" foo:[{"y"}*] {foo:"z"}* ;'
        model = compile(grammar, "test")
        ast = model.parse("xyyzz", nameguard=False)
        self.assertEqual(['x', ['y', 'y'], 'z', 'z'], ast.foo)

        grammar = 'start = foo+:"x" [foo:{"y"}*] {foo:"z"}* ;'
        model = compile(grammar, "test")
        ast = model.parse("xyyzz", nameguard=False)
        self.assertEqual(['x', ['y', 'y'], 'z', 'z'], ast.foo)

    def test_optional_sequence(self):
        grammar = '''
            start = '1' ['2' '3'] '4' $ ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("1234", nameguard=False)
        self.assertEqual(('1', '2', '3', '4'), ast)

        grammar = '''
            start = '1' foo:['2' '3'] '4' $ ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("1234", nameguard=False)
        self.assertEqual(['2', '3'], ast.foo)

    def test_group_ast(self):
        grammar = '''
            start = '1' ('2' '3') '4' $ ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("1234", nameguard=False)
        self.assertEqual(('1', '2', '3', '4'), ast)

    def test_partial_options(self):
        grammar = '''
            start
                =
                [a]
                [
                    'A' 'A'
                |
                    'A' 'B'
                ]
                $
                ;
            a
                =
                'A' !('A'|'B')
                ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("AB", nameguard=False)
        self.assertEqual(('A', 'B'), ast)

    def test_partial_choice(self):
        grammar = '''
            start
                =
                o:[o]
                x:'A'
                $
                ;
            o
                =
                'A' a:'A'
                |
                'A' b:'B'
                ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("A", nameguard=False)
        self.assertEqual({'x': 'A', 'o': None}, ast)

    def test_new_override(self):
        grammar = '''
            start
                =
                @:'a' {@:'b'}
                $
                ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("abb", nameguard=False)
        self.assertEqual(['a', 'b', 'b'], ast)

    def test_list_override(self):
        grammar = '''
            start
                =
                @+:'a' {@:'b'}
                $
                ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("a", nameguard=False)
        self.assertEqual(['a'], ast)

        grammar = '''
            start
                =
                @:'a' {@:'b'}
                $
                ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("a", nameguard=False)
        self.assertEqual('a', ast)

    def test_based_rule(self):
        grammar = '''\
            start
                =
                b $
                ;


            a
                =
                @:'a'
                ;


            b < a
                =
                {@:'b'}
                ;
            '''
        model = compile(grammar, "test")
        ast = model.parse("abb", nameguard=False)
        self.assertEqual(('a', 'b', 'b'), ast)
        self.assertEqual(trim(grammar), str(model))

    def test_rule_include(self):
        grammar = '''
            start = b $;

            a = @:'a' ;
            b = >a {@:'b'} ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("abb", nameguard=False)
        self.assertEqual(('a', 'b', 'b'), ast)

    def test_48_rule_override(self):
        grammar = '''
            start = ab $;

            ab = 'xyz' ;

            @override
            ab = @:'a' {@:'b'} ;
        '''
        model = compile(grammar, "test")
        ast = model.parse("abb", nameguard=False)
        self.assertEqual(('a', 'b', 'b'), ast)

    def test_failed_ref(self):
        grammar = r"""
            final = object;
            type = /[^\s=()]+/;
            object = '('type')' '{' @:{pair} {',' @:{pair}}* [','] '}';
            pair = key '=' value;
            list = '('type')' '[' @:{object} {',' @:{object}}* [','] ']';
            key = /[^\s=]+/;
            value = @:(string|list|object|unset|boolean|number|null) [','];
            null = '('type')' @:{ 'null' };
            boolean = /(true|false)/;
            unset = '<unset>';
            string = '"' @:/[^"]*/ '"';
            number = /-?[0-9]+/;
        """

        model = compile(grammar, "final")
        codegen(model)
        model.parse('(sometype){boolean = true}')

    def test_empty_match_token(self):
        grammar = """
            table = { row }+ ;
            row = (cell1:cell "|" cell2:cell) "\n";
            cell = /[a-z]+/ ;
        """
        try:
            compile(grammar, "model")
            self.fail('allowed empty token')
        except FailedParse:
            pass

    def test_empty_closure(self):
        grammar = '''
            start = {'x'}+ {} 'y'$;
        '''
        model = compile(grammar, "test")
        codegen(model)
        ast = model.parse("xxxy", nameguard=False)
        self.assertEqual((['x', 'x', 'x'], [], 'y'), ast)

    def test_parseinfo(self):
        grammar = '''
            start = head:{'x'}+ {} tail:'y'$;
        '''
        model = compile(grammar, "test")
        ast = model.parse("xxxy", nameguard=False, parseinfo=True)
        self.assertIsNotNone(ast)
        self.assertIsNotNone(ast.head)
        self.assertIsNotNone(ast.tail)
        self.assertIsNotNone(ast.parseinfo)

    def test_raw_string(self):
        grammar = r'''
            start = r'am\nraw' ;
        '''
        pretty = r'''
            start
                =
                'am\\nraw'
                ;
        '''
        model = compile(grammar, "start")
        print(model.pretty())
        self.assertEqual(trim(pretty), model.pretty())

    def test_any(self):
        grammar = '''
            start = /./ 'xx' /./ /./ 'yy' $;
        '''
        model = compile(grammar, "start")
        ast = model.parse("1xx 2 yy")
        self.assertEqual(('1', 'xx', ' ', '2', 'yy'), ast)

    def test_constant(self):
        grammar = '''
            start = ()
                _0:`0` _1:`+1` _n123:`-123`
                _xF:`0xF`
                _string:`string`
                _string_space:`'string space'`
                _true:`True` _false:`False`
                $;
        '''

        model = compile(grammar)
        ast = model.parse("")

        self.assertEqual(ast._0, 0)
        self.assertEqual(ast._1, 1)
        self.assertEqual(ast._n123, -123)
        self.assertEqual(ast._xF, 0xF)
        self.assertEqual(ast._string, "string")
        self.assertEqual(ast._string_space, "string space")
        self.assertEqual(ast._true, True)
        self.assertEqual(ast._false, False)

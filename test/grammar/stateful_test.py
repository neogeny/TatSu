# -*- coding: utf-8 -*-
from __future__ import generator_stop

import unittest

from tatsu.exceptions import FailedSemantics
from tatsu.grammars import ModelContext
from tatsu.tool import compile


class StatefulTests(unittest.TestCase):

    def test_stateful(self):
        # Parser for mediawiki-style unordered lists.
        grammar = r'''
            document = @:ul [ nl ] $ ;
            ul = "*" ul_start el+:li { nl el:li } * ul_end ;
            li = ul | li_text ;
            (* Quirk: If a text line is followed by a sublist, the sublist does not get its own li. *)
            li_text = text:text [ ul:li_followed_by_ul ] ;
            li_followed_by_ul = nl @:ul ;
            text = ?/.*/? ;
            nl = ?/\n/? ul_marker ;
            (* The following rules are placeholders for state transitions. *)
            ul_start = () ;
            ul_end = () ;
            (* The following rules are placeholders for state validations and grammar rules. *)
            ul_marker = () ;
            '''

        class StatefulSemantics:
            def __init__(self, parser):
                self._context = parser

            def ul_start(self, ast):
                ctx = self._context
                ctx.substate = 1 if ctx.substate is None else ctx.substate + 1
                return ast

            def ul_end(self, ast):
                ctx = self._context
                ctx.substate = None if ctx.substate is None or ctx.substate <= 1 else ctx.substate - 1
                return ast

            def ul_marker(self, ast):
                ctx = self._context
                if ctx.substate is not None and not ctx.tokenizer.match("*" * ctx.substate):
                    raise FailedSemantics("not at correct level")
                return ast

            def ul(self, ast):
                return "<ul>" + "".join(ast.el) + "</ul>"

            def li(self, ast):
                return "<li>" + ast + "</li>"

            def li_text(self, ast):
                return ast.text if ast.ul is None else ast.text + ast.ul

        model = compile(grammar, "test")
        context = ModelContext(model.rules, whitespace='', nameguard=False)

        ast = model.parse(
            '*abc', "document",
            context=context,
            semantics=StatefulSemantics(context),
            whitespace='',
            nameguard=False
        )
        self.assertEqual(ast, "<ul><li>abc</li></ul>")

        ast = model.parse(
            '*abc\n',
            "document",
            context=context,
            semantics=StatefulSemantics(context),
            whitespace='',
            nameguard=False
        )
        self.assertEqual("<ul><li>abc</li></ul>", ast)

        ast = model.parse(
            '*abc\n*def\n',
            "document",
            context=context,
            semantics=StatefulSemantics(context),
            whitespace='',
            nameguard=False
        )
        self.assertEqual("<ul><li>abc</li><li>def</li></ul>", ast)

        ast = model.parse(
            '**abc',
            "document",
            context=context,
            semantics=StatefulSemantics(context),
            whitespace='',
            nameguard=False
        )
        self.assertEqual("<ul><li><ul><li>abc</li></ul></li></ul>", ast)

        ast = model.parse(
            '*abc\n**def\n',
            "document",
            context=context,
            semantics=StatefulSemantics(context),
            whitespace='',
            nameguard=False
        )
        self.assertEqual("<ul><li>abc<ul><li>def</li></ul></li></ul>", ast)

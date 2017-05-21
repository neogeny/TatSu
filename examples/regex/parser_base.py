#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CAVEAT UTILITOR
#
# This file was automatically generated by TatSu.
#
#    https://pypi.python.org/pypi/tatsu/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.


from __future__ import print_function, division, absolute_import, unicode_literals

from tatsu.buffering import Buffer
from tatsu.parsing import Parser
from tatsu.parsing import tatsumasu
from tatsu.util import re, generic_main  # noqa


KEYWORDS = {}


class RegexBuffer(Buffer):
    def __init__(
        self,
        text,
        whitespace=None,
        nameguard=None,
        comments_re=None,
        eol_comments_re=None,
        ignorecase=None,
        namechars='',
        **kwargs
    ):
        super(RegexBuffer, self).__init__(
            text,
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            namechars=namechars,
            **kwargs
        )


class RegexParser(Parser):
    def __init__(
        self,
        whitespace=None,
        nameguard=None,
        comments_re=None,
        eol_comments_re=None,
        ignorecase=None,
        left_recursion=True,
        parseinfo=True,
        keywords=None,
        namechars='',
        buffer_class=RegexBuffer,
        **kwargs
    ):
        if keywords is None:
            keywords = KEYWORDS
        super(RegexParser, self).__init__(
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            left_recursion=left_recursion,
            parseinfo=parseinfo,
            keywords=keywords,
            namechars=namechars,
            buffer_class=buffer_class,
            **kwargs
        )

    @tatsumasu()
    def _START_(self):  # noqa
        self._EXPRE_()
        self._check_eof()

    @tatsumasu()
    def _EXPRE_(self):  # noqa
        with self._choice():
            with self._option():
                self._CHOICE_()
            with self._option():
                self._SEQUENCE_()
            self._error('no available options')

    @tatsumasu()
    def _CHOICE_(self):  # noqa
        self._SEQUENCE_()
        self.add_last_node_to_name('opts')

        def block1():
            self._token('|')
            self._cut()
            self._SEQUENCE_()
            self.add_last_node_to_name('opts')
        self._positive_closure(block1)
        self.ast._define(
            [],
            ['opts']
        )

    @tatsumasu()
    def _SEQUENCE_(self):  # noqa

        def block1():
            self._TERM_()
        self._positive_closure(block1)
        self.name_last_node('terms')
        self.ast._define(
            ['terms'],
            []
        )

    @tatsumasu()
    def _TERM_(self):  # noqa
        with self._choice():
            with self._option():
                self._CLOSURE_()
            with self._option():
                self._ATOM_()
            self._error('no available options')

    @tatsumasu()
    def _CLOSURE_(self):  # noqa
        self._ATOM_()
        self.name_last_node('@')
        self._token('*')
        self._cut()

    @tatsumasu()
    def _ATOM_(self):  # noqa
        with self._choice():
            with self._option():
                self._SUBEXP_()
            with self._option():
                self._LITERAL_()
            self._error('no available options')

    @tatsumasu()
    def _SUBEXP_(self):  # noqa
        self._token('(')
        self._cut()
        self._EXPRE_()
        self.name_last_node('@')
        self._token(')')

    @tatsumasu()
    def _LITERAL_(self):  # noqa
        self._pattern(r'(?:\\;|[^|*\\()])+')


class RegexSemantics(object):
    def START(self, ast):
        return ast

    def EXPRE(self, ast):
        return ast

    def CHOICE(self, ast):
        return ast

    def SEQUENCE(self, ast):
        return ast

    def TERM(self, ast):
        return ast

    def CLOSURE(self, ast):
        return ast

    def ATOM(self, ast):
        return ast

    def SUBEXP(self, ast):
        return ast

    def LITERAL(self, ast):
        return ast


def main(filename, startrule, **kwargs):
    with open(filename) as f:
        text = f.read()
    parser = RegexParser()
    return parser.parse(text, startrule, filename=filename, **kwargs)


if __name__ == '__main__':
    import json
    from tatsu.util import asjson

    ast = generic_main(main, RegexParser, name='Regex')
    print('AST:')
    print(ast)
    print()
    print('JSON:')
    print(json.dumps(asjson(ast), indent=2))
    print()

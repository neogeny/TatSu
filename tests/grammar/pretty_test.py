# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import unittest

import pytest

from tatsu.api import compile
from tatsu.util import asjson, trim


class PrettyTests(unittest.TestCase):
    def test_pretty(self):
        grammar = r"""
            start = lisp ;
            lisp = sexp | list | symbol;
            sexp[SExp]: '(' cons:lisp '.' ~ cdr:lisp ')' ;
            list[List]: '(' @:{lisp}* ')' ;
            symbol[Symbol]: /[^\s().]+/ ;
        """

        pretty = trim(r"""
            start: lisp

            lisp: sexp | list | symbol

            sexp[SExp]: '(' cons=lisp '.' ~ cdr=lisp ')'

            list[List]: '(' ={lisp} ')'

            symbol[Symbol]: /[^\s().]+/

        """)

        pretty_lean = trim(r"""
            start: lisp

            lisp: sexp | list | symbol

            sexp: '(' lisp '.' ~ lisp ')'

            list: '(' {lisp} ')'

            symbol: /[^\s().]+/

        """)

        model = compile(grammar=grammar)

        self.assertEqual(pretty, model.pretty())

        self.assertEqual(pretty_lean, model.pretty_lean())

    def test_slashed_pattern(self):
        grammar = """
            start: ?"[a-z]+/[0-9]+" $

        """
        model = compile(grammar=grammar)
        ast = model.parse('abc/123')
        self.assertEqual('abc/123', ast)
        print(model.pretty())
        self.assertEqual(trim(grammar), model.pretty())


def assert_pretty_roundtrip(grammar):
    """The output of pretty() must compile back to an identical model."""
    model = compile(grammar)
    pretty = model.pretty()
    reparsed = compile(pretty)  # pretty output must still be valid grammar
    assert asjson(reparsed) == asjson(model)
    assert reparsed.pretty() == pretty  # pretty() is a fixpoint
    return pretty


CONSTANT_ROUNDTRIP_GRAMMARS = [
    # bare constants that were already stable
    'start = `plain` $ ;',
    'start = `two words` $ ;',
    'start = ` padded out ` $ ;',
    "start = `r'raw'` $ ;",
    # non-string literal constants
    'start = `42` $ ;',
    'start = `-42` $ ;',
    'start = `4.5` $ ;',
    'start = `True` $ ;',
    'start = `False` $ ;',
    'start = `None` $ ;',
    # backticks and line breaks in the value used to break the reparse
    'start = ```a`b``` $ ;',
    'start = ```a\nb``` $ ;',
    "start = `'a\\nb'` $ ;",
    "start = `'a\\rb'` $ ;",
    "start = `'a\\tb'` $ ;",
    "start = `'ab`'` $ ;",
    "start = `'a```b'` $ ;",
    # string values that used to be re-read as other literal types
    "start = `'42'` $ ;",
    "start = `'4.5'` $ ;",
    "start = `'1e5'` $ ;",
    "start = `'-7'` $ ;",
    "start = `'True'` $ ;",
    "start = `'None'` $ ;",
    "start = `'true'` $ ;",
    "start = `'null'` $ ;",
    "start = `' x'` $ ;",
    "start = `'0x1f'` $ ;",
    # values holding both kinds of quotes need the multiline string form
    'start = `\'\'\'it\\\'s "quoted"\'\'\'` $ ;',
    'start = `\'\'\'it\\\'s "q"\\nnext\'\'\'` $ ;',
    'start = \'x\' `\'\'\'it\\\'s "q"\\nnext\'\'\'` \'y\' $ ;',
    'start = `\'\'\'a\\\'\\\'\\\'b "q" `x\'\'\'` $ ;',
    'start = `\'\'\'back\\\\slash \\\'n\\\' "q" `t\'\'\'` $ ;',
    # a value that itself looks like a quoted string
    "start = `'\\x27abc\\x27'` $ ;",
    # both quotes with whitespace at the ends, which trim() would eat
    'start = `\'\'\'\\u0020it\\\'s "q"\\u0020\'\'\'` $ ;',
    # both quotes with an indented continuation line
    'start = `\'\'\'it\\\'s "q"\\n  indented\'\'\'` $ ;',
    # both quotes, a backtick, and whitespace at the ends
    'start = `\'\'\'\\u0020it\\\'s "q" `t\\u0020\'\'\'` $ ;',
    # alerts share the constant rendering
    'start = ^`warning` $ ;',
    'start = ^^```w`x``` $ ;',
    'start = ^```a\nb``` $ ;',
]


@pytest.mark.parametrize('grammar', CONSTANT_ROUNDTRIP_GRAMMARS)
def test_constant_pretty_roundtrip(grammar):
    assert_pretty_roundtrip(grammar)


def test_constant_pretty_value_survives():
    grammar = "start = c:`'it is\\n42'` $ ;"
    model = compile(grammar)
    reparsed = compile(model.pretty())
    assert model.parse('') == reparsed.parse('')
    assert reparsed.parse('')['c'] == 'it is\n42'


def test_constant_pretty_stays_bare_for_plain_literals():
    assert '`plain`' in compile('start = `plain` $ ;').pretty()
    assert '`two words`' in compile('start = `two words` $ ;').pretty()
    assert '`42`' in compile('start = `42` $ ;').pretty()
    assert '`True`' in compile('start = `True` $ ;').pretty()

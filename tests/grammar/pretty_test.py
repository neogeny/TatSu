# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import unittest

import pytest

from tatsu.api import compile
from tatsu.exceptions import FailedParse
from tatsu.util import trim


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


def assert_pattern_roundtrip(regex, matches=(), rejects=()):
    """The output of pretty() must match the same input as the grammar."""
    model = compile(f'start = {regex} $ ;')
    pretty = model.pretty()
    reparsed = compile(pretty)  # pretty output must still be a valid grammar
    assert reparsed.pretty() == pretty  # pretty() is a fixpoint
    for text in matches:
        assert model.parse(text) == text
        assert reparsed.parse(text) == text
    for text in rejects:
        for grammar in (model, reparsed):
            with pytest.raises(FailedParse):
                grammar.parse(text)


NL = '\n'

PATTERN_ROUNDTRIPS = [
    # patterns that were already stable
    ('/abc/', ['abc'], ['abd']),
    (r'/a\/b/', ['a/b'], ['ab']),
    ('/a"b/', ['a"b'], ['ab']),
    (r'/a\\b/', ['a\\b'], ['ab']),
    ('?"[a-z]+/[0-9]+"', ['abc/123'], ['abc']),
    # the indentation pretty() adds used to end up inside the regex
    (f'/line1{NL}  line2/', [f'line1{NL}  line2'], [f'line1{NL}    line2']),
    (f'/line1{NL}    line2/', [f'line1{NL}    line2'], [f'line1{NL}  line2']),
    (rf'/line1\/{NL}line2/', [f'line1/{NL}line2'], ['line1/line2']),
    (f'/a {NL}b/', [f'a {NL}b'], [f'a{NL}b']),
    # trim() used to expand tabs in the regex
    ('/a\tb/', ['a\tb'], ['a    b']),
    # the ?"..." form holds neither a double quote nor a line break
    (r'/a"b\/c/', ['a"b/c'], ['a"bc']),
    # `//` would open an end-of-line comment
    ('?""', [], []),
]

# every character str.splitlines() breaks on used to split the regex in two
PATTERN_ROUNDTRIPS += [
    (f'/a{char}b/', [f'a{char}b'], ['ab'])
    for char in (
        '\r',
        '\v',
        '\f',
        '\x1c',
        '\x1d',
        '\x1e',
        '\x85',
        '\u2028',
        '\u2029',
    )
]


@pytest.mark.parametrize(('regex', 'matches', 'rejects'), PATTERN_ROUNDTRIPS)
def test_pattern_pretty_roundtrip(regex, matches, rejects):
    assert_pattern_roundtrip(regex, matches, rejects)


def test_pattern_pretty_roundtrip_when_nested():
    model = compile(f'start = {{/a{NL}  b/}}+ $ ;')  # indented twice over
    reparsed = compile(model.pretty())
    assert model.parse(f'a{NL}  b') == reparsed.parse(f'a{NL}  b')
    with pytest.raises(FailedParse):
        reparsed.parse(f'a{NL}    b')


@pytest.mark.parametrize(
    ('regex', 'text'),
    [
        (f'(?x){NL}  foo{NL}  bar{NL}', 'foobar'),
        (rf'(?x){NL}  foo{NL}  \/bar', 'foo/bar'),  # a slash rules out ?"..."
    ],
)
def test_verbose_pattern_layout_is_not_escaped(regex, text):
    # whitespace is not significant under (?x), where an escape would be
    model = compile(f'start = /{regex}/ $ ;')
    reparsed = compile(model.pretty())
    assert model.parse(text) == reparsed.parse(text) == text
    assert reparsed.pretty() == model.pretty()


def test_regex_directive_pretty_roundtrip():
    grammar = NL.join(
        [
            """@@comments :: ?'/[*].*?[*]/|"[^"]*"'""",
            'start = /a/ $ ;',
        ]
    )
    model = compile(grammar)
    reparsed = compile(model.pretty())  # used to print an unescaped quote
    assert model.parse('/* c */ a') == reparsed.parse('/* c */ a') == 'a'


def test_pattern_pretty_keeps_the_ends_of_the_regex():
    # trim() used to strip whitespace off both ends of the pattern
    for regex in (' ab', 'ab '):
        model = compile(f'start = /{regex}/ $ ;')
        reparsed = compile(model.pretty())
        assert reparsed.rules[0].exp.sequence[0].pattern == regex

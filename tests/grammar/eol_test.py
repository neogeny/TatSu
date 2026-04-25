# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import pytest

from tatsu import compile
from tatsu.exceptions import FailedParse


def test_basic_eol():
    grammar = r"""
        start = 'hello' $-> 'world' ;
    """
    model = compile(grammar)
    ast = model.parse('hello\nworld')
    assert ast == ['hello', 'world']

    ast = model.parse('hello  \nworld')
    assert ast == ['hello', 'world']

    with pytest.raises(FailedParse):
        model.parse('hello world')  # No line break

    with pytest.raises(FailedParse):
        model.parse('helloX\nworld')  # Non-whitespace before EOL


def test_eol_at_end_of_text():
    grammar = r"""
        start = 'hello' $-> $ ;
    """
    model = compile(grammar)
    ast = model.parse('hello\n')
    assert ast == 'hello'

    ast = model.parse('hello  \n')
    assert ast == 'hello'

    with pytest.raises(FailedParse):
        model.parse('hello world')  # No line break at end


def test_multiple_eols():
    grammar = r"""
        start = 'line1' $-> 'line2' $-> 'line3' ;
    """
    model = compile(grammar)
    ast = model.parse('line1\nline2\nline3')
    assert ast == ['line1', 'line2', 'line3']

    ast = model.parse('line1  \nline2\n  line3')
    assert ast == ['line1', 'line2', 'line3']


def test_eol_with_indentation():
    grammar = r"""
        start = 'start' $-> 'indented' $-> 'end' ;
    """
    model = compile(grammar)
    ast = model.parse('start\n  indented\nend')
    assert ast == ['start', 'indented', 'end']

    model.parse('start\nindented\nend')  # Missing indentation
    assert ast == ['start', 'indented', 'end']


def test_eol_in_closure():
    grammar = r"""
        start = { item $-> }* 'end' ;
        item = 'item' ;
    """
    model = compile(grammar)
    ast = model.parse('item\nitem\nend')
    assert ast == [['item', 'item'], 'end']

    ast = model.parse('item  \nitem\nend')
    assert ast == [['item', 'item'], 'end']

    ast = model.parse('end')
    assert ast == [[], 'end']


def test_eol_with_comments():
    grammar = r"""
        @@eol_comments :: /(?m)#.*$/
        start = 'hello' $-> 'world' ;
    """
    model = compile(grammar)

    ast = model.parse('hello # comment\nworld')
    assert ast == ['hello', 'world']

    ast = model.parse("""
        hello   # another comment

        world
        """)
    assert ast == ['hello', 'world']

    ast = model.parse('hello # comment\n# another comment\nworld')
    assert ast == ['hello', 'world']

    ast = model.parse('hello \n  # another comment\n\nworld')
    assert ast == ['hello', 'world']


def test_eol_with_mixed_whitespace():
    grammar = r"""
        start = 'start' $-> 'next' ;
    """
    model = compile(grammar)
    # Test with spaces and tabs
    ast = model.parse('start \t \nnext')
    assert ast == ['start', 'next']

    # Test with only spaces
    ast = model.parse('start   \nnext')
    assert ast == ['start', 'next']

    # Test with only tabs
    ast = model.parse('start\t\nnext')
    assert ast == ['start', 'next']


def test_eol_no_whitespace_before_linebreak():
    grammar = r"""
        start = 'start' $-> 'next' ;
    """
    model = compile(grammar)
    ast = model.parse('start\nnext')
    assert ast == ['start', 'next']


def test_eol_followed_by_non_whitespace():
    grammar = r"""
        start = 'start' $-> 'next' ;
    """
    model = compile(grammar)
    with pytest.raises(FailedParse):
        model.parse('startX\nnext')


def test_eol_followed_by_non_linebreak():
    grammar = r"""
        start = 'start' $-> 'next' ;
    """
    model = compile(grammar)
    with pytest.raises(FailedParse):
        model.parse('start next')


# This test attempts to reproduce the issue with ENDRULE in tatsu.ebnf
# The actual tatsu.ebnf grammar is complex, so we'll simplify it
# to focus on the $-> behavior within a rule definition context.
# This assumes that the problem is with the $-> expression itself
# and not other parts of the tatsu.ebnf grammar.


# Simplified grammar that mimics the structure of ENDRULE
# ENDRULE in tatsu.ebnf is defined as:
# ENDRULE = (';' | $->) ;
# This means it should match either a semicolon or an EOL.
def test_eol_in_tatsu_ebnf_endrule():
    grammar = r"""
        start = { +=definition ENDRULE }+  $ ;
        definition = name ;
        name = /\w+/ ;
        ENDRULE = $-> $-> | $ | ';' ;
    """
    model = compile(grammar)

    # Test with semicolon
    ast = model.parse('rule_name \n\nsome_definition ; next_rule')
    assert ast == ['rule_name', 'some_definition', 'next_rule']

    # Test with EOL
    ast = model.parse('rule_name ; some_definition \n\nnext_rule')
    assert ast == ['rule_name', 'some_definition', 'next_rule']

    ast = model.parse('rule_name \n\nsome_definition   \n\nnext_rule')
    assert ast == ['rule_name', 'some_definition', 'next_rule']

    # Test failure if neither matches
    with pytest.raises(FailedParse):
        model.parse('rule_name some_definition next_rule')

    # Test with a more complex scenario where $-> is part of a choice
    grammar_complex_endrule = r"""
        start = 'rule_name' definition (';' | $->) 'next_rule' ;
        definition = 'some_definition' ;
    """
    model_complex = compile(grammar_complex_endrule)

    ast = model_complex.parse('rule_name some_definition \nnext_rule')
    assert ast == ['rule_name', 'some_definition', 'next_rule']

    ast = model_complex.parse('rule_name some_definition ; next_rule')
    assert ast == ['rule_name', 'some_definition', ';', 'next_rule']

    # If the problem persists with the actual tatsu.ebnf, it might be due to
    # interaction with other rules or whitespace handling in the main grammar.
    # This test confirms the basic functionality of $-> within a choice.

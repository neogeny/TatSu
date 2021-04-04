from __future__ import annotations

from tatsu.tool import parse
from tatsu.exceptions import GrammarError


def test_missing_rule():
    grammar = '''
        @@grammar::TestGrammar
          block = test ;
    '''
    try:
        parse(grammar, 'abc')
    except GrammarError as e:
        assert str(e) == 'Unknown rules, no parser generated:\ntest'


def test_missing_rules():
    grammar = '''
        @@grammar::TestGrammar
          block = test | test2;
    '''
    try:
        parse(grammar, 'abc')
    except GrammarError as e:
        assert str(e) == 'Unknown rules, no parser generated:\ntest\ntest2'

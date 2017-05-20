# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from tatsu.bootstrap import EBNFBootstrapParser
from tatsu.semantics import ASTSemantics
from tatsu.parser_semantics import EBNFGrammarSemantics


class EBNFParser(EBNFBootstrapParser):
    def __init__(self, semantics=None, **kwargs):
        if semantics is None:
            semantics = ASTSemantics()
        super(EBNFParser, self).__init__(semantics=semantics, **kwargs)


class GrammarGenerator(EBNFBootstrapParser):
    def __init__(self, grammar_name=None, semantics=None, parseinfo=True, **kwargs):
        if semantics is None:
            semantics = EBNFGrammarSemantics(grammar_name)
        super(GrammarGenerator, self).__init__(
            semantics=semantics,
            parseinfo=parseinfo,
            **kwargs
        )

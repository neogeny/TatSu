from __future__ import annotations

from tatsu.bootstrap import EBNFBootstrapParser
from tatsu.semantics import ASTSemantics
from tatsu.parser_semantics import EBNFGrammarSemantics
from tatsu.grammars import EBNFBuffer


class EBNFParser(EBNFBootstrapParser):
    def __init__(self, semantics=None, **kwargs):
        if semantics is None:
            semantics = ASTSemantics()
        super().__init__(semantics=semantics, **kwargs)


class GrammarGenerator(EBNFBootstrapParser):
    def __init__(self, grammar_name=None, semantics=None, parseinfo=True, **kwargs):
        if semantics is None:
            semantics = EBNFGrammarSemantics(grammar_name)
        super().__init__(
            semantics=semantics,
            parseinfo=parseinfo,
            tokenizercls=EBNFBuffer,
            **kwargs
        )

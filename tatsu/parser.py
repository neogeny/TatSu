from __future__ import annotations

import re

from .buffering import Buffer
from .grammars import PRAGMA_RE
from .semantics import ASTSemantics
from .parser_semantics import EBNFGrammarSemantics
from .bootstrap import EBNFBootstrapParser


class EBNFBuffer(Buffer):
    def __init__(
            self, text, filename=None, comments_re=None, eol_comments_re=None, **kwargs):
        super().__init__(
            text,
            filename=filename,
            memoize_lookaheads=False,
            comment_recovery=True,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            **kwargs
        )

    def process_block(self, name, lines, index, **kwargs):
        i = 0
        while i < len(lines):
            line = lines[i]
            if re.match(PRAGMA_RE, line):
                directive, arg = line.split('#', 1)[1], ''
                if '::' in directive:
                    directive, arg = directive.split('::', 1)
                directive, arg = directive.strip(), arg.strip()
                i = self.pragma(name, directive, arg, lines, index, i)
            else:
                i += 1
        return lines, index

    def pragma(self, source, name, arg, lines, index, i):
        # we only recognize the 'include' pragama
        if name == 'include':
            filename = arg.strip('\'"')
            return self.include_file(source, filename, lines, index, i, i + 1)
        else:
            return i + 1  # will be treated as a directive by the parser


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

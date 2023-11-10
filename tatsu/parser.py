import re
from typing import Any

from .bootstrap import EBNFBootstrapParser
from .buffering import Buffer
from .grammars import PRAGMA_RE
from .infos import ParserConfig
from .parser_semantics import EBNFGrammarSemantics
from .semantics import ASTSemantics


class EBNFBuffer(Buffer):
    def __init__(
        self,
        text,
        /,
        filename=None,
        config: ParserConfig | None = None,
        **settings: Any,
    ):
        config = ParserConfig.new(
            config=config, owner=self, filename=filename, **settings,
        )
        super().__init__(text, config=config)

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
    def __init__(
        self,
        name: str | None = None,
        config: ParserConfig | None = None,
        semantics=None,
        **settings: Any,
    ):
        if semantics is None:
            semantics = ASTSemantics()
        config = ParserConfig.new(
            config=config,
            name=name,
            semantics=semantics,
            tokenizercls=EBNFBuffer,
            **settings,
        )
        super().__init__(config)


class GrammarGenerator(EBNFBootstrapParser):
    def __init__(
        self,
        name: str | None = None,
        config: ParserConfig | None = None,
        semantics=None,
        **settings: Any,
    ):
        if semantics is None:
            semantics = EBNFGrammarSemantics(name)
        config = ParserConfig.new(
            config=config,
            name=name,
            semantics=semantics,
            tokenizercls=EBNFBuffer,
            **settings,
        )
        super().__init__(config)

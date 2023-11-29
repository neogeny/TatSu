from __future__ import annotations

import itertools
from collections.abc import Iterator
from typing import Any

from .. import grammars
from ..collections import OrderedSet as oset
from ..mixins.indent import IndentPrintMixin
from ..util import compress_seq, safe_name, trim
from ..walkers import NodeWalker

HEADER = """\
    #!/usr/bin/env python

    # WARNING: CAVEAT UTILITOR
    #
    #  This file was automatically generated by TatSu.
    #
    #     https://pypi.python.org/pypi/tatsu/
    #
    #  Any changes you make to it will be overwritten the next time
    #  the file is generated.

    # ruff: noqa: C405, I001, F401, SIM117

    import sys
    from pathlib import Path

    from tatsu.buffering import Buffer
    from tatsu.parsing import Parser
    from tatsu.parsing import tatsumasu
    from tatsu.parsing import leftrec, nomemo, isname
    from tatsu.infos import ParserConfig
    from tatsu.util import re, generic_main
"""

FOOTER = """\
def main(filename, **kwargs):
    if not filename or filename == '-':
        text = sys.stdin.read()
    else:
        text = Path(filename).read_text()
    parser = {name}Parser()
    return parser.parse(
        text,
        filename=filename,
        **kwargs,
    )


if __name__ == '__main__':
    import json
    from tatsu.util import asjson

    ast = generic_main(main, {name}Parser, name='{name}')
    data = asjson(ast)
    print(json.dumps(data, indent=2))
"""



class PythonCodeGenerator(IndentPrintMixin, NodeWalker):
    _counter: Iterator[int] = itertools.count()

    def __init__(self, parser_name: str = ''):
        super().__init__()
        self.parser_name = parser_name

    @classmethod
    def counter(cls):
        return next(cls._counter)

    @classmethod
    def reset_counter(cls):
        cls._counter = itertools.count()

    def print(self, *args, **kwargs):
        args = [trim(str(arg)) for arg in args]
        super().print(*args, **kwargs)

    def walk_default(self, node: Any):
        return node

    def walk_Grammar(self, grammar: grammars.Grammar):
        self.parser_name = self.parser_name or grammar.name
        self.print(HEADER)
        self.print()
        self.print()

        self._gen_keywords(grammar)
        self._gen_buffering(grammar)
        self._gen_parsing(grammar)

        self.print()
        self.print(FOOTER)

    def walk_Rule(self, rule: grammars.Rule):
        def param_repr(p):
            if isinstance(p, int | float):
                return str(p)
            else:
                return repr(p.split('::')[0])

        params = kwparams = ''
        if rule.params:
            params = ', '.join(
                param_repr(self.walk(p)) for p in rule.params
            )
        if rule.kwparams:
            kwparams = ', '.join(
                f'{k}={param_repr(self.walk(v))}'
                for k, v in rule.kwparams.items()
            )

        if params and kwparams:
            params = params + ', ' + kwparams
        elif kwparams:
            params = kwparams

        # sdefines = ''
        # if not isinstance(rule.exp, grammars.Choice):
        #     sdefines = self._make_defines_declaration(rule)

        leftrec = '\n@leftrec' if rule.is_leftrec else ''
        nomemo = (
            '\n@nomemo'
            if not rule.is_memoizable and not leftrec
            else ''
        )
        isname = '\n@isname' if rule.is_name else ''

        self.print(
            f"""
            @tatsumasu({params})\
            {leftrec}\
            {nomemo}\
            {isname}
            def _{rule.name}_(self):
            """,
        )
        with self.indent():
            self.print(self.walk(rule.exp))
        self.print()

    def _gen_keywords(self, grammar: grammars.Grammar):
        keywords = [str(k) for k in grammar.keywords if k is not None]
        if not keywords:
            self.print('KEYWORDS: set[str] = set()')
        else:
            keywords_str = '\n'.join(f'    {k!r},' for k in keywords)
            keywords_str = '{\n%s\n}' % keywords_str
            self.print(f'KEYWORDS: set[str] = {keywords_str}')

        self.print()
        self.print()


    def _gen_init(self, grammar: grammars.Grammar):
        start = grammar.config.start or grammar.rules[0].name
        self.print(
            f'''
                    config = ParserConfig.new(
                        config,
                        owner=self,
                        whitespace={grammar.config.whitespace},
                        nameguard={grammar.config.nameguard},
                        ignorecase={grammar.config.ignorecase},
                        namechars={grammar.config.namechars or None},
                        parseinfo={grammar.config.parseinfo},
                        comments_re={grammar.config.comments_re!r},
                        eol_comments_re={grammar.config.eol_comments_re!r},
                        keywords=KEYWORDS,
                        start={start!r},
                    )
                    config = config.replace(**settings)
                    super().__init__(text, config=config)
                    ''',
        )
        self.print()

    def _gen_buffering(self, grammar: grammars.Grammar):
        self.print(f'class {self.parser_name}Buffer(Buffer):')

        with self.indent():
            self.print('def __init__(self, text, /, config: ParserConfig | None = None, **settings):')
            with self.indent():
                self._gen_init(grammar)
        self.print()


    def _gen_parsing(self, grammar: grammars.Grammar):
        self.print(f'class {self.parser_name}Parser(Parser):')
        with self.indent():
            self.print('def __init__(self, /, config: ParserConfig | None = None, **settings):')
            with self.indent():
                self._gen_init(grammar)
            self.walk(grammar.rules)

    def _make_defines_declaration(self, node: grammars.Model):
        defines = compress_seq(node.defines())
        ldefs = oset(safe_name(d) for d, value in defines if value)
        sdefs = oset(
            safe_name(d)
            for d, value in defines
            if not value and d not in ldefs
        )

        if not (sdefs or ldefs):
            return ''
        else:
            sdefs_str = '[%s]' % ', '.join(sorted(repr(d) for d in sdefs))
            ldefs_str = '[%s]' % ', '.join(sorted(repr(d) for d in ldefs))
            if not ldefs:
                return f'\n\n    self._define({sdefs_str}, {ldefs_str})'
            else:
                return '\n' + trim(self.define_template % (sdefs_str, ldefs_str))

    define_template = """\
            self._define(
                %s,
                %s,
            )\
        """

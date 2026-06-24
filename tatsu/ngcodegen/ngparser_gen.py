# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import itertools
import string
import types
from collections.abc import Callable, Iterator
from typing import Any

from .. import peg as g
from ..config import ParserConfig
from ..contexts.ctx import Ctx
from ..exceptions import CodegenError
from ..objectmodel import Node
from ..util import Undefined, regexpp, safe_name, typename
from ..util.indent import IndentPrintMixin
from ..walkers import NodeWalker
from .boilerplt import FOOTER, HEADER, IMPORTS, PARSER_BODY


GREEKTOME = "αβδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
ANON = '_'


def pythongen(model: Node, parser_name: str = '') -> str:
    if isinstance(model, g.Model):
        model = model.optimized()
    generator = PythonParserGenerator(parser_name=parser_name)
    generator.walk(model)
    return generator.printed_text()


def textinputgen(model: g.Grammar, basename: str) -> str:
    generator = PythonParserGenerator(parser_name=basename)
    generator.gen_buffering(model, basename)
    return generator.printed_text()


def keywordsgen(model: g.Grammar) -> str:
    generator = PythonParserGenerator()
    generator.gen_keywords(model)
    return generator.printed_text()


class PythonParserGenerator(IndentPrintMixin, NodeWalker):
    def __init__(self, parser_name: str = ''):
        super().__init__()
        self.parser_name = parser_name
        self._block_counter: Iterator[int] = itertools.count()
        self._choice_number: int = 0
        self.ctx_stack: list[str] = ['ctx']

    def new_choice_number(self) -> int:
        n = self._choice_number
        self._choice_number += 1
        return n

    def prev_choice_number(self):
        self._choice_number -= 1

    @property
    def blockn(self) -> int:
        return next(self._block_counter)

    @property
    def loopn(self) -> str:
        n = self.blockn
        # a = GREEKTOME[n]
        a = string.ascii_letters[n]
        return f'cl{a}' if n > 0 else 'cl'

    def push_ctx(self, ctx: str):
        self.ctx_stack.append(ctx)

    def pop_ctx(self):
        self.ctx_stack.pop()

    @property
    def ctx(self):
        return self.ctx_stack[-1]

    def reset_counters(self):
        self._block_counter = itertools.count()
        self._choice_number = 0

    def walk_default(self, node: Any) -> Any:
        raise RuntimeError(f'Unknown node type: {typename(node)}')

    def walk_NIL(self, _node: g.NIL) -> Any:
        return ""

    def walk_Grammar(self, grammar: g.Grammar):
        basename = self.parser_name or grammar.name
        self.print(HEADER)
        self.print()
        self.print(IMPORTS)
        self.print()

        self.gen_keywords(grammar)
        self.gen_buffering(grammar, basename)
        self._gen_parsing(grammar, basename)

        self.print(FOOTER(name=basename))

    def walk_Rule(self, rule: g.Rule):
        def param_repr(p):
            if isinstance(p, int | float):
                return str(p)
            else:
                return repr(p.split('::')[0])

        self.reset_counters()
        params = kwparams = ''
        if rule.params:
            params = ', '.join(param_repr(p) for p in rule.params)
        if rule.kwparams:
            assert isinstance(rule.kwparams, dict)
            kwparams = ', '.join(
                f'{k}={param_repr(v)}' for k, v in rule.kwparams.items()
            )

        if params and kwparams:
            params = params + ', ' + kwparams
        elif kwparams:
            params = kwparams
        if params:
            params = f'({params})'

        # note: remove the leftrec decorator and lieave it to the analyzer
        islrec = '\n@tatsu.leftrec' if rule.is_lrec else ''
        nomemo = '\n@tatsu.nomemo' if not rule.memoizable else ''

        isname = '\n@tatsu.name' if rule.is_name else ''
        istokn = '\n@tatsu.token' if rule.is_tokn else ''

        name = safe_name(rule.name)
        self.print(f"""
                @tatsu.rule{params}\
                {islrec}\
                {nomemo}\
                {isname}\
                {istokn}\
                \ndef {name}(self, {self.ctx_stack[0]}: Ctx) -> Any:
            """)
        with self.indent():
            self.print(self.walk(rule.exp))

    def walk_BasedRule(self, rule: g.BasedRule):
        self.walk_Rule(rule)

    def walk_Call(self, call: g.Call):
        name = safe_name(call.name)
        self.print(f'self.{name}({self.ctx})')

    def walk_RuleInclude(self, include: g.RuleInclude):
        assert include.exp is not None
        self.walk(include.exp)

    def walk_Void(self, _void: g.Void):
        self.print(f'{self.ctx}.void()')

    def walk_Dot(self, _dot: g.Dot):
        self.print(f'{self.ctx}.dot()')

    def walk_Fail(self, _fail: g.Fail):
        self.print(f'{self.ctx}.fail()')

    def walk_Cut(self, _cut: g.Cut):
        self.print(f'{self.ctx}.cut()')

    def walk_Comment(self, comment: g.Comment):
        lines = '\n'.join(f'# {c!s}' for c in comment.comment.splitlines())
        self.print(f'\n{lines}\n')

    def walk_EOLComment(self, comment: g.EOLComment):
        self.walk_Comment(comment)

    def walk_EOF(self, _eof: g.EOF):
        self.print(f'{self.ctx}.eofcheck()')

    def walk_EOL(self, _eol: g.EOL):
        self.print(f'{self.ctx}.eolcheck()')

    def walk_Group(self, group: g.Group):
        # NOTE skip the group as enclosure in this representation
        # self._gen_decor(Ctx.group, exp=group.exp)
        self.walk(group.exp)

    def walk_SkipGroup(self, skip: g.SkipGroup):
        self._gen_decor(Ctx.skipgroup, exp=skip.exp)

    def walk_Token(self, token: g.Token):
        self.print(f'{self.ctx}.token({token.token!r})')

    def walk_Constant(self, constant: g.Constant):
        self.print(f'{self.ctx}.constant({constant.literal!r})')

    def walk_Alert(self, alert: g.Alert):
        self.print(f'{self.ctx}.alert({alert.literal!r}, {alert.level})')

    def walk_Pattern(self, pattern: g.Pattern):
        self.print(f'{self.ctx}.pattern({regexpp(pattern.pattern)})')

    def walk_Lookahead(self, lookahead: g.Lookahead):
        self._gen_decor(Ctx.if_, exp=lookahead.exp)

    def walk_NegativeLookahead(self, lookahead: g.NegativeLookahead):
        self._gen_decor(Ctx.ifnot_, exp=lookahead.exp)

    def walk_Sequence(self, seq: g.Sequence):
        self._gen_defines_declaration(seq)
        self.walk(seq.sequence)

    def walk_Choice(self, choice: g.Choice):
        n = self.new_choice_number()
        var = GREEKTOME[n]
        outerctx = self.ctx
        # self.push_ctx(f'ctx{a}')
        try:
            self._gen_decor(Ctx.choice, ctx=outerctx, var=f'{var}')
            with self.indent():
                elements = choice.lookaheadlist
                self.pfold(f'{var}.expecting', tuple(elements))
                self.print()

                for opt in choice.options:
                    exp: g.Model = opt
                    if isinstance(exp, g.Option):
                        exp = exp.exp
                    self._gen_anon_block(exp, ctx=self.ctx, decor=f'{var}.option')
        finally:
            # self.pop_ctx()
            self.prev_choice_number()

    def walk_Option(self, _option: g.Option):
        pass  # handled by walk_Choice

    def walk_Optional(self, optional: g.Optional):
        self._gen_decor(Ctx.optional, exp=optional.exp)

    def walk_EmptyClosure(self, _closure: g.EmptyClosure):
        self.print(f'{self.ctx}.empty()')

    def walk_Closure(self, closure: g.Closure):
        self._gen_decor(Ctx.loopopt, exp=closure.exp, var=f'{self.loopn}')

    def walk_PositiveClosure(self, closure: g.PositiveClosure):
        self._gen_decor(Ctx.loopplus, exp=closure.exp, var=f'{self.loopn}')

    def walk_Join(self, join: g.Join):
        self._gen_decor(Ctx.joinopt, exp=join.exp, sep=join.sep, var=f'{self.loopn}')

    def walk_PositiveJoin(self, join: g.PositiveJoin):
        self._gen_decor(Ctx.joinplus, exp=join.exp, sep=join.sep, var=f'{self.loopn}')

    def walk_LeftJoin(self, join: g.LeftJoin):
        self._gen_decor(Ctx.joinleft, exp=join.exp, sep=join.sep, var=f'{self.loopn}')

    def walk_RightJoin(self, join: g.RightJoin):
        self._gen_decor(Ctx.joinright, exp=join.exp, sep=join.sep, var=f'{self.loopn}')

    def walk_Gather(self, gather: g.Gather):
        self._gen_decor(Ctx.gatheropt, exp=gather.exp, sep=gather.sep, var='g')

    def walk_PositiveGather(self, gather: g.PositiveGather):
        self._gen_decor(Ctx.gatherplus, exp=gather.exp, sep=gather.sep, var='g')

    def walk_SkipTo(self, skipto: g.SkipTo):
        self._gen_decor(Ctx.skipto, exp=skipto.exp)

    def walk_Named(self, named: g.Named):
        self._gen_decor(Ctx.nameset, exp=named.exp, arg=repr(named.name))

    def walk_NamedList(self, named: g.Named):
        self._gen_decor(Ctx.nameadd, exp=named.exp, arg=repr(named.name))

    def walk_Override(self, o: g.Override):
        self._gen_decor(Ctx.result, exp=o.exp)

    def walk_OverrideList(self, override: g.OverrideList):
        self._gen_decor(Ctx.resultadd, exp=override.exp)

    def gen_keywords(self, grammar: g.Grammar):
        keywords = [str(k) for k in grammar.keywords if k is not None]
        if not keywords:
            self.print('KEYWORDS = ()')
        else:
            self.print('KEYWORDS = (')
            with self.indent():
                keywords_str = '\n'.join(f'    {k!r},' for k in sorted(keywords))
                self.print(keywords_str)
            self.print(')')

        self.print()
        self.print()

    def walk_Meta(self, meta: g.Meta):
        name = meta.pretty()[1:]
        self.print(f'{self.ctx}.match{name!s}()')

    def _gen_init(self, grammar: g.Grammar):
        assert isinstance(grammar.config, ParserConfig)
        start = grammar.config.start or grammar.rules[0].name

        whitespace = grammar.config.whitespace
        if whitespace is Undefined:  # the default value
            whitespace = None
        elif whitespace is not None:
            whitespace = regexpp(whitespace)

        self.print(f'''
                config = ParserConfig.new(
                    config=config,
                    whitespace={whitespace},
                    nameguard={grammar.config.nameguard},
                    ignorecase={grammar.config.ignorecase or False},
                    namechars={grammar.config.namechars or ""!r},
                    parseinfo={grammar.config.parseinfo},
                    comments={regexpp(grammar.config.comments)},
                    eol_comments={regexpp(grammar.config.eol_comments)},
                    keywords=KEYWORDS,
                    start={start!r},
                )
                assert isinstance(config, ParserConfig)
                config = config.override(**settings)
            ''')

    def _input_name(self, basename) -> str:
        return f'{basename}Text'

    def _legacy_input_name(self, basename) -> str:
        return f'{basename}Tokenizer'

    def _buffer_name(self, basename) -> str:
        return f'{basename}Buffer'

    def _parser_name(self, basename: str) -> str:
        return f'{basename}Parser'

    def _rules_name(self, basename: str) -> str:
        return f'{basename}Rules'

    def _gen_buffering_init(self, grammar: g.Grammar):
        with self.indent():
            self.print('def __init__(')
            with self.indent():
                self.print(
                    """
                    self,
                    text,
                    /,
                    config: ParserConfig | None = None,
                    **settings,
                    """,
                )
            self.print(') -> None:')
            with self.indent():
                self._gen_init(grammar)
                self.print()
                self.print('super().__init__(text, config=config)')
        self.print()

    def gen_buffering(self, grammar: g.Grammar, basename: str):
        self.print(f'class {self._input_name(basename)}(TextLines):')
        self._gen_buffering_init(grammar)
        self.print(
            f'{self._legacy_input_name(basename)} = {self._input_name(basename)}'
        )
        self.print()

        self.print()
        self.print(
            f'class {self._buffer_name(basename)}(Buffer):  # NOTE: backwards compatibility'
        )
        self._gen_buffering_init(grammar)
        self.print()

    def _gen_parsing(self, grammar: g.Grammar, basename: str):
        self.print(f'class {self._parser_name(basename)}(Parser):')
        with self.indent():
            self.print(
                'def __init__(self, /, config: ParserConfig | None = None, **settings):'
            )
            with self.indent():
                self.print('\n' + PARSER_BODY(rules_name=self._rules_name(basename)))
        self.print()
        self.print()

        self.print(f'class {self._rules_name(basename)}:')
        with self.indent():
            self.print(
                'def __init__(self, /, config: ParserConfig | None = None, **settings):',
            )
            with self.indent():
                self._gen_init(grammar)
                self.print('self._config = config')
                self.print()
            # self.print("""
            #     @property
            #     def config(self) -> ParserConfig:
            #         assert isinstance(self._config, ParserConfig)
            #         return self._config
            #     """)
            self.print()
            self.walk(grammar.rules)
        self.print()

    def _gen_defines_declaration(self, node: g.Model):
        sdefs = node.defines_single
        ldefs = node.defines_list

        if not (sdefs or ldefs):
            return

        sdefs_str = ', '.join(sorted(repr(d) for d in sdefs))
        ldefs_str = ', '.join(sorted(repr(d) for d in ldefs))

        definestr = f'{self.ctx}.define([{sdefs_str}], [{ldefs_str}])'
        if not ldefs or self.fitsfmt(definestr, 1):
            self.print(definestr)
        else:
            self.print(f'{self.ctx}.define(')
            with self.indent():
                self.print(f'[{sdefs_str}],')
                self.print(f'[{ldefs_str}],')
            self.print(')')

    def _gen_block(self, exp: g.Model, name='block'):
        if () in exp.lookaheadlist:
            raise CodegenError(
                f'{exp!r} may repeat empty sequence @{exp.line} {exp.lookahead!r}',
            )

        n = self.blockn
        self.print()
        self.print(f'def {name}{n}():')
        with self.indent():
            self.walk(exp)

        return n

    def _gen_anon_block(
        self,
        exp: g.Model,
        decor: str = '',
        echeck: bool = False,
        ctx: str | None = None,
    ):
        ctx = ctx or self.ctx
        if echeck and () in exp.lookaheadlist:
            raise CodegenError(
                f'{exp!r} may repeat empty sequence @{exp.line} {exp.lookahead!r}',
            )

        if decor:
            self.print(f'@{decor}')
        if ctx:
            self.print(f'def {ANON}({ctx}: Ctx) -> Any:')
        else:
            self.print(f'def {ANON}() -> Any:')
        with self.indent():
            self.walk(exp)

    def _gen_decor(
        self,
        mgr: Callable[..., Any],
        /,
        *,
        exp: g.Model | None = None,
        sep: g.Model | None = None,
        var: str = '',
        arg: str = '',
        ctx: str | None = None,
        echeck: bool = True,
    ):
        assert isinstance(mgr, types.FunctionType)
        name = mgr.__name__
        if var:
            self.print(f'with ctx.{name}({arg}) as {var}:')
        else:
            self.print(f'with ctx.{name}({arg}):')
        with self.indent():
            # FIXME: only generated for Choice
            # if var and exp and (elements := exp.lookaheadlist):
            #     self.pfold(f'{var}.expecting', tuple(elements))
            #     self.print()
            if sep:
                self._gen_anon_block(sep, decor=f'{var}.sep', ctx=ctx, echeck=echeck)
                self.print()
            if exp and var:
                self._gen_anon_block(exp, decor=f'{var}.exp', ctx=ctx, echeck=echeck)
            elif exp:
                self.walk(exp)

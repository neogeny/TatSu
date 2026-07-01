# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any

from tatsu.input.cursor import Text

from ..contexts import Ctx, Func, RuleInfo
from ..contexts.cst import cstmerge
from ..contexts.state import _AT_
from ..exceptions import FailedParse, FailedUnlinkedRule, ParseError
from ..util.common import typename
from .base import NIL, Grammar, Model, Rule, Void
from .basic import (
    EOF,
    EOL,
    Alert,
    Constant,
    Cut,
    Dot,
    Fail,
    Token,
)
from .choice import Choice, Option
from .closure import (
    Closure,
    EmptyClosure,
    Gather,
    Join,
    PositiveClosure,
    PositiveGather,
    PositiveJoin,
)
from .deprecated import LeftJoin, RightJoin
from .meta import BoolMeta, FloatMeta, IntMeta, NameMeta, UIntMeta
from .named import Named, NamedList, Override, OverrideList
from .pattern import Pattern
from .rulelike import BasedRule, RuleInclude
from .syntax import (
    Box,
    Call,
    Group,
    Lookahead,
    NegativeLookahead,
    Optional,
    Sequence,
    SkipGroup,
    SkipTo,
)


class FatParser:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.ruleinfos: dict[str, RuleInfo] = {
            name: RuleInfo.bind(
                rule.ruleinfo,
                instance=self,
                func=self._parse_fn(exp=rule.exp),
            )
            for name, rule in grammar.rulemap.items()
        }

    def parse(
        self,
        text: str | Text,
        /,
        *,
        start: str | None = None,
        config: Any = None,
        asmodel: bool = False,
        **settings: Any,
    ) -> Any:
        g = self.grammar.optimized()
        config = g.new_parse_config(start=start, config=config, **settings)
        ctx = g.newctx(asmodel=asmodel)
        ri = self.get_ruleinfo(config.start)

        with ctx.bound(
            text, start=start, config=config, asmodel=asmodel, **settings
        ) as bound:
            return bound.call(ri)

    def get_ruleinfo(self, name: str) -> RuleInfo:
        if (ri := self.ruleinfos.get(name, None)) is None:
            raise ParseError(f"rule not found: {name}")
        return ri

    def _parse_fn(self, *, exp: Model) -> Func:
        def _(ctx: Ctx) -> Any:
            return self.parse_exp(ctx, exp)

        return _

    def parse_exp(self, ctx: Ctx, exp: Model) -> Any:
        assert isinstance(exp, Model)
        match exp:
            case Call(name=_):
                ri = self.ruleinfos.get(exp.name, None)
                if ri is None:
                    raise ctx.newexcept(f"unknown rule {exp.name}")
                return ctx.call(ri)
            case NIL():
                return ctx.fail() or ()
            case Void():
                return ctx.void()
            case Dot():
                return ctx.dot()
            case Fail():
                return ctx.fail()
            case EOF():
                return ctx.eofcheck()
            case EOL():
                return ctx.eolcheck()
            case Token():
                return ctx.token(exp.token)
            case Constant():
                return ctx.constant(exp.literal)
            case Alert():
                return ctx.alert(message=exp.literal, level=exp.level)
            case Cut():
                return ctx.cut()
            case Pattern():
                return ctx.pattern(exp.pattern or r'\\')
            case EmptyClosure():
                return ctx.empty()

            case NameMeta():
                return ctx.matchname()
            case IntMeta():
                return ctx.matchint()
            case UIntMeta():
                return ctx.matchuint()
            case FloatMeta():
                return ctx.matchfloat()
            case BoolMeta():
                return ctx.matchbool()

            case Group():
                e = exp.exp
                while isinstance(e, Group):
                    e = e.exp
                return self.parse_exp(ctx, e)
            case SkipGroup():
                with ctx.skipgroup():
                    self.parse_exp(ctx, exp.exp)
                    return None
            case Lookahead():
                with ctx.if_():
                    return self.parse_exp(ctx, exp.exp)
            case NegativeLookahead():
                with ctx.ifnot_():
                    return self.parse_exp(ctx, exp.exp)
            case Named():
                value = self.parse_exp(ctx, exp.exp)
                ctx.ast[exp.name] = value
                return value
            case NamedList():
                value = self.parse_exp(ctx, exp.exp)
                ctx.ast._setlist(exp.name, value)
                return value
            case Override():
                value = self.parse_exp(ctx, exp.exp)
                ctx.ast[_AT_] = value
                return {_AT_: value}
            case OverrideList():
                value = self.parse_exp(ctx, exp.exp)
                if _AT_ not in ctx.ast:
                    value = [value]
                ctx.ast[_AT_] = value
                return {_AT_: value}

            case Choice():
                for o in exp.options:
                    ctx.states.push()
                    o._add_defined(ctx)
                    target = o.exp if isinstance(o, Option) else o
                    try:
                        value = self.parse_exp(ctx, target)
                        ctx.states.merge()
                        return value
                    except FailedParse:
                        if ctx.states.undo().cutseen:
                            raise
                raise ctx.newexcept(exp.expectingstr)
            case Option():
                return self.parse_exp(ctx, exp.exp)

            case Closure():
                with ctx.loopopt() as cl:
                    return cl.exp(self._parse_fn(exp=exp.exp))
            case PositiveClosure():
                with ctx.loopplus() as cl:
                    return cl.exp(self._parse_fn(exp=exp.exp))
            case Join():
                with ctx.joinopt() as cl:
                    cl.exp(self._parse_fn(exp=exp.exp))
                    cl.sep(self._parse_fn(exp=exp.sep))
                return ctx.last_node
            case PositiveJoin():
                with ctx.joinplus() as cl:
                    cl.exp(self._parse_fn(exp=exp.exp))
                    cl.sep(self._parse_fn(exp=exp.sep))
                return ctx.last_node
            case Gather():
                with ctx.gatheropt() as cl:
                    cl.exp(self._parse_fn(exp=exp.exp))
                    cl.sep(self._parse_fn(exp=exp.sep))
                return ctx.last_node
            case PositiveGather():
                with ctx.gatherplus() as cl:
                    cl.exp(self._parse_fn(exp=exp.exp))
                    cl.sep(self._parse_fn(exp=exp.sep))
                return ctx.last_node
            case LeftJoin():
                with ctx.joinleft() as cl:
                    cl.exp(self._parse_fn(exp=exp.exp))
                    cl.sep(self._parse_fn(exp=exp.sep))
                return ctx.last_node
            case RightJoin():
                with ctx.joinright() as cl:
                    cl.exp(self._parse_fn(exp=exp.exp))
                    cl.sep(self._parse_fn(exp=exp.sep))
                return ctx.last_node
            case SkipTo():
                with ctx.skipto() as cl:
                    cl.exp(self._parse_fn(exp=exp.exp))
                return ctx.last_node
            case Sequence():
                exp._add_defined(ctx)
                out = None
                for s in exp.sequence:
                    e = s
                    while isinstance(e, Group):
                        e = e.exp
                    r = self.parse_exp(ctx, e)
                    if r is None:
                        continue
                    out = cstmerge(out, r)
                return out
            case Optional():
                with ctx.optional():
                    return self.parse_exp(ctx, exp.exp)
                return ctx.last_node
            case Rule():
                ri = RuleInfo.bind(self.ruleinfos[exp.name], ctx)
                return ctx.call(ri)
            case BasedRule():
                ri = RuleInfo.bind(
                    self.ruleinfos[exp.name],
                    ctx,
                    func=self._parse_fn(exp=exp.rhs),
                )
                return ctx.call(ri)
            case RuleInclude():
                if exp._exp is None:
                    raise ctx.newexcept(
                        f'Unlinked rule {exp.name!r}',
                        FailedUnlinkedRule,
                    )
                return self.parse_exp(ctx, exp._exp)

            case Box():
                return self.parse_exp(ctx, exp.exp)
            case _:
                raise RuntimeError(f"unkown model type {typename(exp)}\n{exp!r}")
        raise RuntimeError(f"THIS CANNOT HAPPEN WITH {exp!r}")

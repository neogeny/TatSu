# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import field
from functools import cached_property
from typing import Any

from ..contexts import Ctx
from ..exceptions import FailedParse
from ..objectmodel import nodedataclass
from .math import ffset
from .model import PEP8_LLEN, Box, Model


@nodedataclass
class Option(Box):
    def _parse(self, ctx: Ctx) -> Any:
        result = self.exp._parse(ctx)
        return result

    def optimized(self) -> Model:
        return self.exp.optimized()


@nodedataclass
class Choice(Model):
    options: list[Option] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.options = self.options or self.ast
        assert isinstance(self.options, list), repr(self.options)
        assert self.options, repr(self.options)

    def _parse(self, ctx: Ctx) -> Any:
        # ctx.expecting(*self.expecting)
        for o in self.options:
            ctx.states.push()
            try:
                value = o._parse(ctx)
                ctx.states.merge()
                return value
            except FailedParse:
                if ctx.states.undo().cutseen:
                    raise
        raise ctx.newexcept(self.expectingstr)

    @cached_property
    def defines_single(self) -> list[str]:
        return list(set().union(*(o.defines_single for o in self.options)))

    @cached_property
    def defines_list(self) -> list[str]:
        return list(set().union(*(o.defines_list for o in self.options)))

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return set().union(*[o.missing_rules(rulenames) for o in self.options])

    def _used_rule_names(self):
        return set().union(*[o._used_rule_names() for o in self.options])

    def _first(self, k, f) -> ffset:
        result = set()
        for o in self.options:
            result |= o._first(k, f)
        self._firstset = result
        return result

    def _follow(self, k, fl, a):
        for o in self.options:
            o._follow(k, fl, a)
        return a

    def nodecount(self) -> int:
        return 1 + sum(o.nodecount() for o in self.options)

    def _pretty(self, lean=False):
        options = [str(o._pretty(lean=lean)) for o in self.options]

        multi = options and any(len(o.splitlines()) > 1 for o in options)
        single = ' | '.join(o for o in options)
        multi = multi or len(single) > PEP8_LLEN * 0.6  # WARNING: magic number !

        if multi:
            return '| ' + '\n| '.join(o for o in options)
        else:
            return single

    @cached_property
    def _nullable(self) -> bool:
        return any(o._nullable for o in self.options)

    def optimized(self) -> Model | Choice:
        opt = [o.optimized() for o in self.options]
        for o in opt:
            assert isinstance(o, Model)
        if len(opt) == 1:
            return opt[0]
        return Choice(options=opt)

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import field
from typing import Any

from ..contexts import Ctx
from ..objectmodel import nodedataclass
from ..util import cast, indent
from ._core import PEP8_LLEN, Box, Model
from .math import ffset


@nodedataclass
class Option(Box):
    def _parse(self, ctx: Ctx) -> Any:
        result = super()._parse(ctx)
        self._add_defined_attributes(ctx, result)
        return result


@nodedataclass
class FirstOption(Option):
    pass


@nodedataclass
class Choice(Model):
    options: list[Option] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.options = self.options or self.ast
        assert isinstance(self.options, list), repr(self.options)

    def _parse(self, ctx: Ctx) -> Any:
        with ctx.choice() as ch:

            def wrap(o) -> Any:
                assert isinstance(ctx, Ctx) and isinstance(o, Option)
                return o._parse

            ch.options = [wrap(o) for o in self.options]

            ch.expecting(*self.expecting())
        return ch.result

    def defines(self):
        return [d for o in self.options for d in o.defines()]

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

        multi = any(len(o.splitlines()) > 1 for o in options)
        single = ' | '.join(o for o in options)

        if multi:
            return '\n|\n'.join(indent(o) for o in options)
        elif options and len(single) > PEP8_LLEN:
            return '| ' + '\n| '.join(o for o in options)
        else:
            return single

    def _nullable(self) -> bool:
        return any(o._nullable() for o in self.options)

    def callable_at_same_pos(self) -> list[Model]:
        return cast(list[Model], self.options)


@nodedataclass
class FirstChoice(Choice):
    pass

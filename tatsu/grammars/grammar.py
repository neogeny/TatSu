# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections import defaultdict
from copy import copy
from dataclasses import field
from pathlib import Path
from typing import Any

from ..contexts import Ctx, ParseContext
from ..exceptions import GrammarError
from ..objectmodel import tatsudataclass
from ..parserconfig import ParserConfig
from ..util import chunks
from .math import ffset
from ._core import ModelContext, Model, Rule
from .leftrec import mark_left_recursion


@tatsudataclass
class Grammar(Model):
    name: str = 'MyTest'
    directives: dict[str, Any] | None = field(default_factory=dict)
    config: ParserConfig | None = None
    rules: list[Rule] = field(default_factory=list)
    rulemap: dict[str, Rule] = field(default_factory=dict)

    def __init__(
        self,
        name,
        rules,
        /,
        config: ParserConfig | None = None,
        directives: dict | None = None,
        **settings,
    ):
        super().__init__()
        assert isinstance(rules, list), f'{type(rules)!r} {rules!r}'
        directives = directives or {}
        self.directives = directives

        config = ParserConfig.new(config=config, **settings)
        config = config.hard_override(**directives)
        self.config = config

        self.rules = rules
        self.rulemap = {rule.name: rule for rule in rules}

        if name is None:
            name = self.directives.get('grammar')
        if name is None:
            name = self.config.name
        if name is None and config.filename is not None:
            name = Path(config.filename).stem
        if name is None:
            name = 'My'
        self.name = name

        missing: set[str] = self.missing_rules(set(self.rulemap))
        if missing:
            msg = '\n'.join(['', *sorted(missing)])
            raise GrammarError('Unknown rules, no parser generated:' + msg)

        self._calc_lookahead_sets()
        leftrect_rules = mark_left_recursion(self.rulemap)
        if leftrect_rules and not config.left_recursion:
            raise GrammarError(
                f'{config.left_recursion=}'
                f' but found left-recursive rules'
                f' {', '.join(repr(r.name) for r in leftrect_rules)}!'
            )

    @property
    def keywords(self) -> set[str]:
        return self.config.keywords

    @property
    def semantics(self) -> Any:
        return self.config.semantics

    @semantics.setter
    def semantics(self, value: Any):
        self.config.semantics = value  # type: ignore

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return set().union(*[rule.missing_rules(rulenames) for rule in self.rules])

    def _used_rule_names(self) -> set[str]:
        if not self.rules:
            return set()

        used = {'start', self.rules[0].name}
        prev: set[str] = set()
        while used != prev:
            prev = used
            used |= set().union(
                *[rule._used_rule_names() for rule in self.rules if rule.name in used],
            )
        return used

    def used_rules(self) -> list[Rule]:
        used = self._used_rule_names()
        return [rule for rule in self.rules if rule.name in used]

    @property
    def first_sets(self):
        return self._firstset

    def _calc_lookahead_sets(self, k: int = 1):
        self._calc_first_sets(k=k)
        self._calc_follow_sets(k=k)

    def _calc_first_sets(self, k: int = 1):
        f: dict[str, ffset] = defaultdict(set)
        f1 = None
        while f1 != f:
            f1 = copy(f)
            for rule in self.rules:
                f[rule.name] |= rule._first(k, f)

        # cache results
        for rule in self.rules:
            rule._firstset = f[rule.name]

    def _calc_follow_sets(self, k: int = 1):
        fl: dict[str, ffset] = defaultdict(set)
        fl1 = None
        while fl1 != fl:
            fl1 = copy(fl)
            for rule in self.rules:
                rule._follow(k, fl, set())

        # cache results
        for rule in self.rules:
            rule._follow_set = fl[rule.name]

    def parse(
        self,
        text: str,
        /,
        *,
        ctx: ParseContext | None = None,
        config: ParserConfig | None = None,
        **settings,
    ):
        config = self.config.override_config(config)
        # note: bw-comp: allow overriding directives
        config = config.override(**settings)

        if isinstance(config.semantics, type):
            raise TypeError(
                'semantics must be an object instance or None, '
                f'not class {config.semantics!r}',
            )

        start = config.effective_start_rule_name()
        if start is None:
            start = self.rules[0].name
            config.start = start
            config.start_rule = None
            config.rule_name = None

        if ctx is None:
            ctx = ModelContext(self.rules, config=config)
        assert isinstance(ctx, Ctx)
        return ctx.parse(text, config=config)

    def nodecount(self) -> int:
        return 1 + sum(r.nodecount() for r in self.rules)

    def _pretty(self, lean: bool = False) -> str:
        regex_directives = {'comments', 'eol_comments', 'whitespace'}
        str_directives = {'comments', 'grammar'}
        string_directives = {'namechars'}

        directives = ''
        for directive, value in self.directives.items():
            fmt = dict(  # noqa: C408
                name=directive,
                frame='/' if directive in regex_directives else '',
                value=(
                    repr(value)
                    if directive in string_directives
                    else str(value) if directive in str_directives else value
                ),
            )
            directives += '@@{name} :: {frame}{value}{frame}\n'.format(**fmt)
        if directives:
            directives += '\n'

        keywords = '\n'.join(
            '@@keyword :: ' + ' '.join(repr(k) for k in c if k is not None)
            for c in chunks(sorted(self.keywords), 8)
        ).strip()
        keywords = '\n\n' + keywords + '\n' if keywords else ''

        rules = (
            '\n\n'.join(str(rule._pretty(lean=lean)) for rule in self.rules)
        ).rstrip() + '\n\n'
        return directives + keywords + rules

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import weakref
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from copy import copy
from dataclasses import field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, override

from ..ast import AST
from ..contexts import Ctx, ParseContext
from ..contexts.infos import RuleInfo
from ..exceptions import GrammarError
from ..objectmodel import Node, nodedataclass
from ..parserconfig import ParserConfig
from ..util import chunks, compress_seq, indent, trim, typename
from .builder import ModelBuilderSemantics
from .math import ffset, kdot

PEP8_LLEN = 72

_model_classes: list[type[Model]] = []

type Func = Callable[[], Any]
# type Result = str | Model | AST | list[Result] | tuple[Result, ...]
type Result = Any


def model_classes() -> list[type[Model]]:
    return _model_classes


class ModelContext(ParseContext):
    def __init__(
        self,
        rules,
        /,
        start: str | None = None,
        config: ParserConfig | None = None,
        asmodel: bool = False,
        **settings,
    ):
        config = ParserConfig.new(config, **settings)
        assert isinstance(config, ParserConfig)
        config = config.override(start=start)

        super().__init__(config=config)
        if not self.config.semantics and asmodel:
            self.config.semantics = ModelBuilderSemantics()

        self._rulemap: dict[str, Rule] = {rule.name: rule for rule in rules}

    @property
    def rulemap(self) -> dict[str, Rule]:
        return self._rulemap

    def find_rule(self, name: str) -> Callable:
        return self.rulemap[name]._parse


@nodedataclass
class Model(Node):
    _lookahead: ffset = field(init=False, default_factory=set)
    _firstset: ffset = field(init=False, default_factory=set)
    _follow_set: ffset = field(init=False, default_factory=set)
    _grammar_ref: weakref.ref[Model] | None = field(init=False, default=None)

    def __init_subclass__(cls: type[Model], **kwargs):
        super().__init_subclass__(**kwargs)
        _model_classes.append(cls)

    @staticmethod
    def model_classes() -> list[type[Model]]:
        return _model_classes

    def follow_ref(self) -> Model:
        return self

    def _parse(self, ctx: ParseContext) -> Result:
        return ()

    def defines(self):
        return []

    @property
    def grammar(self) -> Grammar:
        if self._grammar_ref is None:
            raise RuntimeError(f'{typename(self)} not fully initialized')
        grammar = self._grammar_ref()
        if not isinstance(grammar, Grammar):
            raise TypeError(f'{typename(self)} incorrectly initialized {grammar}')
        return grammar

    def parse(self, text: str, /, **settings) -> Result:
        grammar = self.grammar
        assert isinstance(grammar, Grammar)
        return grammar.parse(text, **settings)

    def _set_grammar(self, grammar: Grammar):
        assert isinstance(grammar, Grammar)

        self._grammar_ref = weakref.ref(grammar)
        for child in self.children():
            assert isinstance(child, Model)
            child._set_grammar(grammar)

    def _add_defined_attributes(self, ctx: ParseContext, ast: Any | None = None):
        if ast is None:
            return
        if not hasattr(ast, '_define'):
            return

        defines = dict(compress_seq(self.defines()))

        keys = [k for k, ll in defines.items() if not ll]
        list_keys = [k for k, ll in defines.items() if ll]
        ctx.define(keys, list_keys)
        if isinstance(ast, AST):
            ast._define(keys, list_keys)

    def lookahead(self, k: int = 1) -> ffset:
        if not self._lookahead:
            self._lookahead = kdot(self.firstset(k), self.followset(k), k)
        return self._lookahead

    def lookaheadlist(self, k: int = 1) -> list[str]:
        return sorted(repr(fl[0]) if fl else repr(fl) for fl in self.lookahead(k=k))

    def firstset(self, k: int = 1) -> ffset:
        if not self._firstset:
            self._firstset = self._first(k, defaultdict(set))
        return self._firstset

    def followset(self, _k: int = 1) -> ffset:
        return self._follow_set

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return set()

    def _used_rule_names(self):
        return set()

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        return set()

    def _follow(self, k, fl, a):
        return a

    def is_nullable(self) -> bool:
        return self._nullable()

    def _nullable(self) -> bool:
        return False

    # list of Model that can be invoked at the same position
    def callable_at_same_pos(self) -> list[Model]:
        return []

    def nodecount(self) -> int:
        return 1

    def pretty(self, lean: bool = False) -> str:
        return self._pretty(lean=lean)

    def pretty_lean(self):
        return self._pretty(lean=True)

    def _pretty(self, lean=False):
        return f'{typename(self)}: {id(self)}'

    def railroads(self) -> str:
        from .. import railroads

        return railroads.text(self)


@nodedataclass
class NULL(Model):
    def _parse(self, ctx: ParseContext) -> Result:
        return ctx.fail() or ()

    def _pretty(self, lean=False):
        return NULL.__name__

    def _nullable(self) -> bool:
        return False


@nodedataclass
class Void(Model):
    def _parse(self, ctx: ParseContext) -> Result:
        return ctx.void()

    def _pretty(self, lean=False):
        return '()'

    def _nullable(self) -> bool:
        return True


@nodedataclass
class Box(Model):
    name: str | None = field(init=False, default=None)
    exp: Model = field(default_factory=NULL)

    def __post_init__(self):
        noexp = not self.exp or isinstance(self.exp, NULL)
        if noexp and not isinstance(self.ast, AST):
            self.exp = self.ast
        super().__post_init__()
        if isinstance(self.ast, AST):
            assert self.exp == self.ast.exp
        # assert not isinstance(self.exp, NULL), self.ast
        self.exp = self.exp if self.exp is not None else NULL()
        assert self.exp is not None, f'{typename(self)}({self.exp})'
        assert self.exp, repr(self)

    def _parse(self, ctx: ParseContext) -> Result:
        return self.exp._parse(ctx)

    def defines(self):
        return self.exp.defines()

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        assert isinstance(self.exp, Model), f'{self!r}:{self.exp=!r}'
        return self.exp.missing_rules(rulenames)

    def _used_rule_names(self):
        return self.exp._used_rule_names()

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        return self.exp._first(k, f)

    def _follow(self, k, fl, a):
        return self.exp._follow(k, fl, a)

    def nodecount(self) -> int:
        return 1 + self.exp.nodecount()

    def _pretty(self, lean=False):
        return self.exp._pretty(lean=lean)

    def _nullable(self) -> bool:
        return self.exp._nullable()

    def callable_at_same_pos(
        self,
        rulemap: Mapping[str, Rule] | None = None,
    ) -> list[Model]:
        return [self.exp]


@nodedataclass
class NamedBox(Box):
    name: str = field(default='')  # pyright: ignore[reportIncompatibleVariableOverride]


@nodedataclass
class Rule(NamedBox):
    params: tuple[str, ...] = field(default_factory=tuple)
    kwparams: dict[str, Any] = field(default_factory=dict)
    decorators: list[str] = field(default_factory=list)
    base: str | None = None
    is_name: bool = False
    is_leftrec: bool = False
    is_memoizable: bool = True

    def __post_init__(self):
        super().__post_init__()
        self.params = self.params or ()
        self.kwparams = self.kwparams or {}
        self.decorators = self.decorators or []

        self.is_name = bool(self.is_name) or 'name' in self.decorators
        self.is_name = bool(self.is_name) or 'isname' in self.decorators

        if not self.kwparams:
            self.kwparams = {}
        elif not isinstance(self.kwparams, dict):
            self.kwparams = dict(self.kwparams)
        assert isinstance(self.kwparams, dict), f'{typename(self)}: {self.kwparams=!r}'

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return self.exp.missing_rules(rulenames)

    def _parse(self, ctx: ParseContext) -> Any:
        return self._parse_rhs(ctx, self.exp)

    def _parse_rhs(self, ctx: ParseContext, exp: Model) -> Result:
        ruleinfo = RuleInfo(
            name=self.name,
            instance=exp,
            func=exp._parse,
            is_lrec=self.is_leftrec,
            is_memo=self.is_memoizable,
            is_name=self.is_name,
            params=self.params,
            kwparams=self.kwparams,
        )
        return ctx.call(ruleinfo)

    def _first(self, k, f) -> ffset:
        self._firstset = self.exp._first(k, f) | f[self.name]
        return self._firstset

    def _follow(self, k, fl, a):
        return self.exp._follow(k, fl, fl[self.name])

    def _nullable(self) -> bool:
        return self.exp._nullable()

    @staticmethod
    def param_repr(p):
        if isinstance(p, int | float) or (isinstance(p, str) and p.isalnum()):
            return str(p)
        else:
            return repr(p)

    def _pretty(self, lean=False):
        str_template = "{is_name}{name}{base}{params}: {exp}"

        if lean:
            params = ''
        else:
            params = (
                ', '.join(self.param_repr(p) for p in self.params)
                if self.params
                else ''
            )

            skwparams = ''
            if self.kwparams:
                skwparams = ', '.join(
                    f'{k}={self.param_repr(v)}' for (k, v) in self.kwparams.items()
                )

            if params and skwparams:
                params = f'[{params}, {skwparams}]'
            elif skwparams:
                params = f'[{skwparams}]'
            elif params:
                params = f'[{params}]'

        base = f' < {self.base!s}' if self.base else ''

        exp = self.exp._pretty(lean=lean)
        if len(exp.splitlines()) > 1:
            exp = '\n' + indent(exp)

        return trim(str_template).format(
            name=self.name,
            base=base,
            params=params,
            exp=exp,
            is_name='@name\n' if self.is_name else '',
        )


@nodedataclass
class Grammar(Model):
    name: str = 'MyTest'
    directives: dict[str, Any] = field(default_factory=dict)
    rules: tuple[Rule, ...] = field(default_factory=tuple)

    def __init__(
        self,
        name=None,
        rules: Iterable | None = None,
        *,
        config: ParserConfig | None = None,
        directives: dict | None = None,
        **settings,
    ):
        super().__init__()
        assert isinstance(rules, Iterable), f'{type(rules)!r} {rules!r}'
        directives = directives or {}
        assert isinstance(directives, dict)
        self.directives = directives

        config = ParserConfig.new(config=config, **settings)
        config = config.hard_override(**directives)
        self._config: ParserConfig = config

        self.rules = tuple(rules)  # type: ignore
        rulemap = {rule.name: rule for rule in rules}
        self._rule = SimpleNamespace(**rulemap)
        self._rulemap = self._rule.__dict__

        self.name = self._resolve_name(name)

        for rule in self.rules:
            rule._set_grammar(self)

        missing: set[str] = self.missing_rules(set(self.rulemap))
        if missing:
            msg = '\n'.join(['', *sorted(missing)])
            raise GrammarError('Unknown rules, no parser generated:' + msg)

        self._calc_lookahead_sets()
        self._mark_left_recursion()

    @property
    def config(self) -> ParserConfig:
        return self._config

    @property
    def rulemap(self) -> dict[str, Rule]:
        return self._rulemap

    @property
    def rule(self) -> SimpleNamespace:
        return self._rule

    @property
    def keywords(self) -> set[str]:
        return self.config.keywords

    @property
    def semantics(self) -> Any:
        return self.config.semantics

    @semantics.setter
    def semantics(self, value: Any):
        self.config.semantics = value  # type: ignore

    @property
    def first_sets(self):
        return self._firstset

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return set().union(*[rule.missing_rules(rulenames) for rule in self.rules])

    def used_rules(self) -> list[Rule]:
        used = self._used_rule_names()
        return [rule for rule in self.rules if rule.name in used]

    def _resolve_name(self, name: str | None) -> str:
        if name is None:
            name = self.directives.get('grammar')
        if name is None:
            name = self.config.name
        if name is None and self.config.filename is not None:
            name = Path(self.config.filename).stem
        if name is None:
            name = 'My'
        return name

    def _mark_left_recursion(self):
        from .leftrec import mark_left_recursion

        leftrect_rules = mark_left_recursion(self.rules)
        if leftrect_rules and not self.config.left_recursion:
            config = self.config
            raise GrammarError(
                f'{config.left_recursion=}'
                f' but found left-recursive rules'
                f' {', '.join(repr(r.name) for r in leftrect_rules)}!'
            )

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

    @override
    def parse(
        self,
        text: str,
        /,
        *,
        start: str | None = None,
        ctx: Ctx | None = None,
        config: ParserConfig | None = None,
        asmodel: bool = False,
        **settings,
    ) -> Result:
        config = self.config.override_config(config)
        assert isinstance(config, ParserConfig)
        # note: bw-comp: allow overriding directives
        config = config.override(start=start, **settings)

        if isinstance(config.semantics, type):
            raise TypeError(
                'semantics must be an object instance or None, '
                f'not class {config.semantics!r}',
            )

        start = config.effective_start_rule_name()
        if start is None:
            start = self.rules[0].name
            config = config.override(
                start=start,
                start_rule=None,
                rule_name=None,
            )

        self._config = config
        ctx = ctx or self.newctx(asmodel=asmodel)
        assert isinstance(ctx, Ctx)
        return ctx.parse(text, config=config)

    def newctx(self, asmodel: bool = True) -> Ctx:
        return ModelContext(self.rules, config=self.config, asmodel=asmodel)

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

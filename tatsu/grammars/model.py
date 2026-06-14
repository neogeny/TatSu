# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import weakref
from collections import defaultdict
from collections.abc import Iterable, Mapping
from copy import copy
from dataclasses import field
from functools import cached_property
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Self

from ..config import ParserConfig
from ..contexts import AST, CanParse, Ctx, Func, ParseContext, RuleInfo
from ..exceptions import GrammarError
from ..input import Text
from ..objectmodel import ModelBuilderSemantics, Node, nodedataclass
from ..util import indent, trim, typename
from .math import ffset, kdot


PEP8_LLEN = 72

_model_classes: list[type[Model]] = []


def model_classes() -> list[type[Model]]:
    return _model_classes


@nodedataclass
class Model(Node, CanParse):
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

    @cached_property
    def defines_single(self) -> list[str]:
        return []

    @cached_property
    def defines_list(self) -> list[str]:
        return []

    @property
    def grammar(self) -> Grammar:
        if self._grammar_ref is None:
            raise RuntimeError(f'{typename(self)} not fully initialized')
        grammar = self._grammar_ref()
        if not isinstance(grammar, Grammar):
            raise TypeError(f'{typename(self)} incorrectly initialized {grammar}')
        return grammar

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
        grammar = self.grammar
        assert isinstance(grammar, Grammar)
        return grammar.parse(
            text,
            start=start,
            config=config,
            asmodel=asmodel,
            **settings,
        )

    def _parse(self, ctx: Ctx) -> Any:
        return ()

    def link(self, grammar: Grammar):
        assert isinstance(grammar, Grammar)

        self._grammar_ref = weakref.ref(grammar)
        for child in self.children():
            assert isinstance(child, Model)
            child.link(grammar)

    def _add_defined(self, ctx: Ctx):
        keys_single = self.defines_single
        keys_list = self.defines_list
        ctx.define(keys_single, keys_list)

    def lookahead(self, k: int = 1) -> ffset:
        if not getattr(self, '_lookahead', None):
            self._lookahead = kdot(self.firstset(k), self.followset(k), k)
        return self._lookahead

    @cached_property
    def lookaheadlist(self) -> list[Any]:
        return sorted(fl[0] for fl in self.lookahead(1) if fl)

    @cached_property
    def expecting(self) -> list[str]:
        return sorted(str(la) for la in self.lookaheadlist)

    @cached_property
    def expectingstr(self) -> str:
        return f'Expected one of: {' '.join(repr(s) for s in self.expecting)}'

    def firstset(self, k: int = 1) -> ffset:
        if not getattr(self, '_firstset', None):
            self._firstset = self._first(k, defaultdict(set))
        return self._firstset

    def followset(self, _k: int = 1) -> ffset:
        if not getattr(self, '_follow_set', None):
            self._follow_set = set()
        return self._follow_set

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        assert rulenames
        return set()

    def _used_rule_names(self):
        return set()

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:  # pyright: ignore[reportUnusedParameter]
        return set()

    def _follow(self, k, fl, a):
        return a

    def is_nullable(self) -> bool:
        return self._nullable

    @cached_property
    def _nullable(self) -> bool:
        return False

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

    def optimized(self) -> Model:
        return copy(self)


@nodedataclass
class NIL(Model):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.fail() or ()

    def _pretty(self, lean=False):
        return typename(self)

    @cached_property
    def _nullable(self) -> bool:
        return True


@nodedataclass
class Void(Model):
    def __post_init__(self):
        super().__post_init__()
        self.ast = None

    def _parse(self, ctx: Ctx) -> Any:
        return ctx.void()

    def _pretty(self, lean=False):
        return '()'

    @cached_property
    def _nullable(self) -> bool:
        return True


@nodedataclass
class Box(Model):
    name: str | None = field(init=False, default=None)
    exp: Model = field(default_factory=NIL)

    def __post_init__(self):
        noexp = not self.exp or isinstance(self.exp, NIL)
        if noexp and not isinstance(self.ast, AST):
            self.exp = self.ast
        super().__post_init__()
        if isinstance(self.ast, AST):
            assert self.exp == self.ast.exp
        # assert not isinstance(self.exp, NIL), self.ast
        self.exp = self.exp if self.exp is not None else NIL()
        assert self.exp is not None, f'{typename(self)}({self.exp})'
        assert self.exp, repr(self)

    def _parse(self, ctx: Ctx) -> Any:
        return self.exp._parse(ctx)

    @cached_property
    def defines_single(self) -> list[str]:
        return self.exp.defines_single

    @cached_property
    def defines_list(self) -> list[str]:
        return self.exp.defines_list

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

    @cached_property
    def _nullable(self) -> bool:
        return self.exp._nullable

    def optimized(self) -> Self | Model:
        exp = self.exp.optimized()
        new = copy(self)
        new.exp = exp
        return new


@nodedataclass
class Synth(Box):
    """A synthetic placeholder for an unresolved rule."""

    pass


@nodedataclass
class NamedBox(Box):
    name: str = field(default='')  # type: ignore

    def optimized(self) -> Self | Model:
        exp = self.exp.optimized()
        new = copy(self)
        new.exp = exp
        return new


@nodedataclass
class Rule(NamedBox):
    params: tuple[str, ...] = field(default_factory=tuple)
    kwparams: dict[str, Any] = field(default_factory=dict)
    decorators: list[str] = field(default_factory=list)
    base: str | None = None

    # these come from parsing a grammar
    is_name: bool = False
    is_tokn: bool = False
    no_memo: bool = False
    no_stak: bool = False

    # these are used by left recursion analisis
    is_memo: bool = True
    is_lrec: bool = False

    def __post_init__(self):
        super().__post_init__()
        self.params = self.params or ()
        self.kwparams = self.kwparams or {}
        self.decorators = self.decorators or []

        # pyrefly: ignore [unnecessary-type-conversion]
        self.is_name = bool(self.is_name) or 'name' in self.decorators
        # pyrefly: ignore [unnecessary-type-conversion]
        self.is_name = bool(self.is_name) or 'isname' in self.decorators

        if not self.kwparams:
            self.kwparams = {}
        elif not isinstance(self.kwparams, dict):
            self.kwparams = dict(self.kwparams)
        assert isinstance(self.kwparams, dict), f'{typename(self)}: {self.kwparams=!r}'
        self.is_tokn = self.is_tokn or self.name.lstrip('_')[:1].isupper()

    def __pub__(self, sunderok: bool = False) -> dict[str, Any]:
        pub = super().__pub__()
        del pub['exp']
        pub['exp'] = self.exp
        return pub

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return self.exp.missing_rules(rulenames)

    def _parse(self, ctx: Ctx) -> Any:
        return self._parse_rhs(ctx, self.exp)

    def _parse_rhs(self, ctx: Ctx, exp: Model) -> Any:
        # NOTE: BasedRule._parse() calls _parse_rhs() so ruleinfo is a mix
        ruleinfo = RuleInfo(
            name=self.name,
            instance=exp,
            func=exp._parse,
            no_memo=self.no_memo,
            no_stak=self.no_stak,
            is_name=self.is_name,
            is_tokn=self.is_tokn,
            params=self.params,
            kwparams=self.kwparams,
            is_lrec=self.is_lrec,
            is_memo=self.memoizable,
        )
        return ctx.call(ruleinfo)

    def _first(self, k, f) -> ffset:
        self._firstset = self.exp._first(k, f) | f[self.name]
        return self._firstset

    def _follow(self, k, fl, a):
        return self.exp._follow(k, fl, fl[self.name])

    @cached_property
    def _nullable(self) -> bool:
        return self.exp._nullable

    @property
    def memoizable(self):
        return self.is_memo and not self.no_memo and not self.is_lrec

    @property
    def should_trace(self) -> bool:
        return not self.no_stak

    @staticmethod
    def param_repr(p):
        if isinstance(p, int | float) or (isinstance(p, str) and p.isalnum()):
            return str(p)
        else:
            return repr(p)

    def _pretty(self, lean=False):
        str_template = "{is_name}{no_memo}{name}{base}{params}:{exp}"

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
                    (f'{k}={self.param_repr(v)}' for (k, v) in self.kwparams.items()),
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
        else:
            exp = ' ' + exp

        return trim(str_template).format(
            name=self.name,
            base=base,
            params=params,
            exp=exp,
            no_memo='@nomemo\n' if self.no_memo else '',
            is_name='@name\n' if self.is_name else '',
        )

    def optimized(self) -> Rule:
        from .syntax import Call, Sequence

        assert isinstance(self.exp, Model)
        exp = self.exp.optimized()
        while isinstance(exp, Sequence) and len(exp.sequence) == 1:
            exp = exp.sequence[0]
        if isinstance(exp, Call) and exp._rule:
            exp = exp._rule.exp.optimized()
        new = copy(self)
        new.exp = exp
        new._lookahead = self.lookahead()
        return new


@nodedataclass
class Patterns(Model):
    whitespace: str | None = None
    comments: str | None = None
    eol_comments: str | None = None


@nodedataclass
class Grammar(Model):
    name: str = 'MyTest'
    directives: dict[str, Any] = field(default_factory=dict)
    keywords: tuple[str, ...] = field(default_factory=tuple)
    rules: tuple[Rule, ...] = field(default_factory=tuple)
    _optimized: Grammar | None = None

    def __init__(
        self,
        name=None,
        rules: Iterable[Rule] | None = None,
        *,
        config: Any = None,
        directives: dict | None = None,
        keywords: tuple[str, ...] | None = None,
        **settings: Any,
    ):
        super().__init__()
        config = config if isinstance(config, ParserConfig) else ParserConfig()
        assert isinstance(rules, Iterable), f'{type(rules)!r} {rules!r}'

        directives = directives or {}
        assert isinstance(directives, dict)
        self.directives = directives

        config = ParserConfig.new(config=config, **settings)
        config = config.hard_override(**directives)
        self._config: ParserConfig = config

        keywords = keywords or config.keywords or ()
        keywords = tuple(k for k in keywords or () if k)
        assert isinstance(keywords, tuple)
        if self.config.ignorecase:
            keywords = tuple(k.upper() for k in keywords if k)
        keywords = tuple(sorted(set(keywords)))
        assert isinstance(keywords, tuple)
        self.keywords = keywords

        # NOTE Ctx needs keywords in config
        self._config = self._config.override(keywords=self.keywords)

        self.rules = tuple(rules)  # type: ignore

        self.name = self._resolve_name(name)
        self.initialize()

    def initialize(self) -> None:
        rulemap = {rule.name: rule for rule in self.rules}
        self._rule = SimpleNamespace(**rulemap)
        self._rulemap = self._rule.__dict__
        self.link(self)
        self._calc_lookahead_sets()
        self._mark_left_recursion()

        missing: set[str] = self.missing_rules(set(self.rulemap))
        if missing:
            msg = '\n'.join(['', *sorted(missing)])
            raise GrammarError('Unknown rules, no parser generated:' + msg)

    def configure(self, config: ParserConfig | None = None, **settings: Any):
        self._config.merge_config(config)
        self._config.merge(**settings)

    def _update_patterns(self):
        if not hasattr(self, 'patterns'):
            self.patterns = Patterns()
        self.patterns.whitespace = (
            self.patterns.whitespace
            or self.config.whitespace
            or self.directives.get('whitespace')
        )
        self.patterns.comments = (
            self.patterns.comments
            or self.config.comments
            or self.directives.get('comments')
        )
        self.patterns.eol_comments = (
            self.patterns.eol_comments
            or self.config.eol_comments
            or self.directives.get('eol_comments')
        )

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
        if name is None and self.config.source is not None:
            name = Path(self.config.source).stem
        if name is None:
            name = 'My'
        return name

    def _mark_left_recursion(self):
        # from .leftrec.depthf import mark_left_recursion
        # from .leftrec.autumn import mark_left_recursion
        from .leftrec.pegen import mark_left_recursion

        leftrect_rules = mark_left_recursion(self.rules)
        if leftrect_rules and not self.config.left_recursion:
            config = self.config
            raise GrammarError(
                f'{config.left_recursion=}'
                f' but found left-recursive rules'
                f' {', '.join(repr(r.name) for r in leftrect_rules)}!',
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
        for rule in self.rules:
            if rule.lookaheadlist is None:
                raise GrammarError(f'Impossible lookahead in rule {rule.name}')

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
        text: str | Text,
        /,
        *,
        start: str | None = None,
        config: Any = None,
        asmodel: bool = False,
        **settings: Any,
    ) -> Any:
        self = self.optimized()  # noqa: PLW0642
        return self._do_parse(
            text, start=start, config=config, asmodel=asmodel, **settings
        )

    def _do_parse(
        self,
        text: str | Text,
        /,
        *,
        start: str | None = None,
        config: Any = None,
        asmodel: bool = False,
        **settings: Any,
    ) -> Any:
        config = self.config.override_config(config)
        assert isinstance(config, ParserConfig)
        # NOTE: bw-comp: allow overriding directives
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
        ctx = self.newctx(asmodel=asmodel)
        assert isinstance(ctx, Ctx)
        return ctx.parse(text, config=config)

    def newctx(self, asmodel: bool = True) -> Ctx:
        return ModelContext(self.rules, config=self.config, asmodel=asmodel)

    def nodecount(self) -> int:
        return 1 + sum(r.nodecount() for r in self.rules)

    def _pretty(self, lean: bool = False) -> str:
        regex_directives = {'comments', 'eol_comments', 'whitespace'}
        string_directives = {'namechars'}

        directives = ''
        # noinspection PyUnresolvedReferences
        for name, value in self.directives.items():
            if name in regex_directives:
                if '/' in value:
                    directives += f'@@{name} :: ?"{value}"\n'
                else:
                    directives += f'@@{name} :: /{value}/\n'
            elif name in string_directives:
                directives += f'@@{name} :: {value!r}\n'
            else:
                directives += f'@@{name} :: {value}\n'
        if directives:
            directives += '\n'

        keywordsets = []
        batch: list[str] = []
        bfmt: str = ""
        for k in sorted(repr(k) for k in self.keywords):
            batch += [k]
            bfmt = f"@@keyword :: {' '.join(batch)}"
            if len(bfmt) >= PEP8_LLEN - 8:
                keywordsets += [bfmt]
                batch = []
        if batch:
            keywordsets += [bfmt]

        keywords = f"\n\n{'\n'.join(keywordsets)}\n\n" if keywordsets else ""

        rules = (
            '\n\n'.join(str(rule._pretty(lean=lean)) for rule in self.rules)
        ).rstrip() + '\n\n'
        return f"{directives}{keywords}{rules}"

    def optimized(self) -> Grammar:
        if isinstance(self._optimized, Grammar):
            return self._optimized

        optrules: tuple[Rule, ...] = tuple(r.optimized() for r in self.rules)
        new = copy(self)
        new.rules = optrules
        new.initialize()

        self._optimized = new  # NOTE cache optimized grammar
        new._optimized = new  # NOTE circular reference as cached

        return new

    @classmethod
    def __from_json__(cls: type[Self], data: Mapping[str, Any]) -> Grammar:
        g = super().__from_json__(data)
        # NOTE got a Grammar that used Grammar.__init__()
        #
        # NOTE
        #   Copy the grammar so the configuration is unique
        # HACK
        return Grammar(
            name=g.name,
            rules=g.rules,
            directives=g.directives,
            keywords=g.keywords,
        )


class ModelContext(ParseContext):
    def __init__(
        self,
        rules: Iterable[Rule],
        /,
        start: str | None = None,
        config: ParserConfig | None = None,
        asmodel: bool = False,
        **settings: Any,
    ):
        config = ParserConfig.new(config, **settings)
        assert isinstance(config, ParserConfig)
        super().__init__(start=start, config=config, asmodel=asmodel)
        if not self.config.semantics and asmodel:
            self.config.semantics = ModelBuilderSemantics()

        self._rulemap: dict[str, Rule] = {rule.name: rule for rule in rules}

    @property
    def rulemap(self) -> dict[str, Rule]:
        return self._rulemap

    def find_rule(self, name: str) -> Func:
        return self.rulemap[name]._parse

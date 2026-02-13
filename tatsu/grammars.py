# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import functools
from collections import defaultdict
from collections.abc import Callable, Collection, Mapping
from copy import copy
from dataclasses import field
from itertools import takewhile
from pathlib import Path
from typing import Any

from .ast import AST
from .contexts import ParseContext
from .exceptions import FailedRef, GrammarError
from .infos import ParserConfig, RuleInfo
from .objectmodel import Node, tatsudataclass
from .util import indent, re, regexp, trim
from .util.abctools import chunks, compress_seq
from .util.typing import typename

PEP8_LLEN = 72
PRAGMA_RE = r'^\s*#include.*$'

type ffset = set[tuple[str, ...]]


class _ref(str):
    def __repr__(self) -> str:
        return f'<{self}>'


def ref(name: str) -> tuple[str]:
    return (_ref(name),)


def kdot(x: ffset, y: ffset, k: int) -> ffset:
    if not y:
        return {a[:k] for a in x}
    elif not x:
        return {b[:k] for b in y}
    else:
        return {(a + b)[:k] for a in x for b in y}


class ModelContext(ParseContext):
    def __init__(
        self,
        rules,
        /,
        start: str | None = None,
        config: ParserConfig | None = None,
        **settings,
    ):
        config = ParserConfig.new(config, **settings)
        config = config.override(start=start)

        super().__init__(config=config)

        self._rulemap: dict[str, Rule] = {rule.name: rule for rule in rules}

    @property
    def rulemap(self) -> dict[str, Rule]:
        return self._rulemap

    @property
    def pos(self) -> int:
        return self._tokenizer.pos

    def _find_rule(self, name: str) -> Callable:
        return functools.partial(self.rulemap[name]._parse, self)


@tatsudataclass
class Model(Node):
    _lookahead: ffset = field(init=False, default_factory=set)
    _firstset: ffset = field(init=False, default_factory=set)
    _follow_set: ffset = field(init=False, default_factory=set)

    @staticmethod
    def classes() -> list[type]:
        return [
            c
            # Copy globals() before iterating to be thread-safe.
            for c in globals().copy().values()
            if isinstance(c, type) and issubclass(c, Model)
        ]

    def follow_ref(self, rulemap: Mapping[str, Rule]) -> Model:
        return self

    def _parse(self, ctx: ModelContext) -> Any | None:
        ctx.last_node = None
        return None

    def defines(self):
        return []

    def _add_defined_attributes(self, ctx: ModelContext, ast: Any | None = None):
        if ast is None:
            return
        if not hasattr(ast, '_define'):
            return

        defines = dict(compress_seq(self.defines()))

        keys = [k for k, list in defines.items() if not list]
        list_keys = [k for k, list in defines.items() if list]
        ctx._define(keys, list_keys)
        if isinstance(ast, AST):
            ast._define(keys, list_keys)

    def lookahead(self, k: int = 1) -> ffset:
        if not self._lookahead:
            self._lookahead = kdot(self.firstset(k), self.followset(k), k)
        return self._lookahead

    def lookahead_str(self) -> str:
        return ' '.join(sorted(repr(f[0]) for f in self.lookahead() if f))

    def firstset(self, k: int = 1) -> ffset:
        if not self._firstset:
            self._firstset = self._first(k, defaultdict(set))
        return self._firstset

    def followset(self, k: int = 1) -> ffset:
        return self._follow_set

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return set()

    def _used_rule_names(self):
        return set()

    def _first(self, k: int, f: Mapping[str, ffset]) -> ffset:
        return set()

    def _follow(self, k, fl, a):
        return a

    def is_nullable(self, rulemap: Mapping[str, Rule] | None = None) -> bool:
        return self._nullable()

    def _nullable(self) -> bool:
        return False

    # list of Model that can be invoked at the same position
    def callable_at_same_pos(self, rulemap: Mapping[str, Rule] | None = None) -> list[Model]:
        return []

    def nodecount(self) -> int:
        return 1

    def pretty(self, lean: bool = False) -> str:
        return self._pretty(lean=lean)

    def pretty_lean(self):
        return self._pretty(lean=True)

    def _pretty(self, lean=False):
        return f'{typename(self)}: {id(self)}'

    def __repr__(self):
        return f'{typename(self)}()'

    def __str__(self):
        return self.pretty()


@tatsudataclass
class Void(Model):
    def _parse(self, ctx):
        return ctx._void()

    def _pretty(self, lean=False):
        return '()'

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class Dot(Model):
    def _parse(self, ctx):
        return ctx._dot()

    def _pretty(self, lean=False):
        return '/./'

    def _first(self, k: int, f: Mapping[str, ffset]) -> ffset:
        return {('.',)}


@tatsudataclass
class Fail(Model):
    def _parse(self, ctx):
        return ctx._fail()

    def _pretty(self, lean=False):
        return '!()'


@tatsudataclass
class Comment(Model):
    def __post_init__(self):
        super().__post_init__()
        self.comment = self.ast.comment

    def _pretty(self, lean: bool = False):
        return f'(* {self.comment} *)'


@tatsudataclass
class EOLComment(Comment):
    def _pretty(self, lean=False):
        return f'  # {self.comment}\n'


@tatsudataclass
class EOF(Model):
    def _parse(self, ctx):
        ctx._check_eof()

    def _pretty(self, lean=False):
        return '$'


@tatsudataclass
class Decorator(Model):
    exp: Model = field(init=False, default_factory=Model)

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.ast, AST):
            self.exp = self.ast
        # else: allow for subclasses to use self.exp

    def _parse(self, ctx) -> Any | None:
        return self.exp._parse(ctx)

    def defines(self):
        return self.exp.defines()

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        assert isinstance(self.exp, Model), f'{self!r}:{self.exp=!r}'
        return self.exp.missing_rules(rulenames)

    def _used_rule_names(self):
        return self.exp._used_rule_names()

    def _first(self, k: int, f: Mapping[str, ffset]) -> ffset:
        return self.exp._first(k, f)

    def _follow(self, k, fl, a):
        return self.exp._follow(k, fl, a)

    def nodecount(self) -> int:
        return 1 + self.exp.nodecount()

    def _pretty(self, lean=False):
        return self.exp._pretty(lean=lean)

    def _nullable(self) -> bool:
        return self.exp._nullable()

    def callable_at_same_pos(self, rulemap: Mapping[str, Rule] | None = None) -> list[Model]:
        return [self.exp]

    def __repr__(self):
        return f'{type(self).__name__}({self.exp!r})'


# NOTE: backwards compatibility
_Decorator = Decorator


@tatsudataclass
class Group(Decorator):
    def _parse(self, ctx):
        with ctx._group():
            self.exp._parse(ctx)
            return ctx.last_node

    def _pretty(self, lean=False):
        exp = self.exp._pretty(lean=lean)
        if len(exp.splitlines()) <= 1:
            return f'({trim(exp)})'
        return f'(\n{indent(exp)}\n)'


@tatsudataclass
class Token(Model):
    def __post_init__(self):
        super().__post_init__()
        self.token = self.ast

    def _parse(self, ctx):
        return ctx._token(self.token)

    def _first(self, k, f) -> ffset:
        return {(self.token,)}

    def _pretty(self, lean=False):
        return repr(self.token)

    def __repr__(self):
        return f'{type(self).__name__}({self.token!r})'


@tatsudataclass
class Constant(Model):
    def __post_init__(self):
        super().__post_init__()
        self.literal = self.ast

    def _parse(self, ctx):
        return ctx._constant(self.literal)

    def _first(self, k, f) -> ffset:
        return {()}

    def _pretty(self, lean=False):
        return f'`{self.literal!r}`'

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class Alert(Constant):
    def __post_init__(self):
        super().__post_init__()
        self.literal = self.ast.message.literal
        self.level = len(self.ast.level)

    def _parse(self, ctx):
        return super()._parse(ctx)

    def _pretty(self, lean=False):
        return f'{"^" * self.level}{super()._pretty()}'


@tatsudataclass
class Pattern(Model):
    def __post_init__(self):
        super().__post_init__()
        self.patterns = self.ast
        self.regex = re.compile(self.pattern)

    @property
    def pattern(self) -> str:
        return ''.join(list(self.patterns))

    def _parse(self, ctx):
        return ctx._pattern(self.pattern)

    def _first(self, k, f) -> ffset:
        x = str(self)
        if bool(self.regex.match('')):
            return {(), (x,)}
        else:
            return {(x,)}

    def _pretty(self, lean=False):
        parts = []
        for pat in (str(p) for p in self.patterns):
            if '/' in pat:
                newpat = pat.replace('"', r'\"')
                regex = f'?"{newpat}"'
            else:
                regex = f'/{pat}/'
            parts.append(regex)
        return '\n+ '.join(parts)

    def _nullable(self) -> bool:
        return bool(self.regex.match(''))

    def __repr__(self):
        return f'{type(self).__name__}({regexp(self.pattern)})'

    def __str__(self):
        return self.pattern


@tatsudataclass
class Lookahead(Decorator):
    def _parse(self, ctx):
        with ctx._if():
            return super()._parse(ctx)

    def _pretty(self, lean=False):
        return '&' + self.exp._pretty(lean=lean)

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class NegativeLookahead(Decorator):
    def _parse(self, ctx):
        with ctx._ifnot():
            return super()._parse(ctx)

    def _pretty(self, lean=False):
        return '!' + str(self.exp._pretty(lean=lean))

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class SkipTo(Decorator):
    def _parse(self, ctx):
        super_parse = super()._parse
        return ctx._skip_to(lambda: super_parse(ctx))

    def _first(self, k, f) -> ffset:
        return {('.',)} | super()._first(k, f)

    def _pretty(self, lean=False):
        return '->' + self.exp._pretty(lean=lean)


@tatsudataclass
class Sequence(Model):
    @property
    def sequence(self) -> list[Model]:
        return self.ast

    def _parse(self, ctx):
        ctx.last_node = [s._parse(ctx) for s in self.sequence]
        return ctx.last_node

    def defines(self):
        return [d for s in self.sequence for d in s.defines()]

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return set().union(
            *[s.missing_rules(rulenames) for s in self.sequence],
        )

    def _used_rule_names(self):
        return set().union(*[s._used_rule_names() for s in self.sequence])

    def _first(self, k, f) -> ffset:
        result = {()}
        for s in self.sequence:
            x = s._first(k, f)
            result = kdot(result, x, k)
        self._firstset = result
        return result

    def _follow(self, k, fl, a):
        fs = a
        for x in reversed(self.sequence):
            if isinstance(x, Call):
                fl[x.name] |= fs
            x._follow(k, fl, fs)
            fs = kdot(x.firstset(k=k), fs, k)
        return a

    def nodecount(self) -> int:
        return 1 + sum(s.nodecount() for s in self.sequence)

    def _pretty(self, lean=False):
        seq = [str(s._pretty(lean=lean)) for s in self.sequence]
        single = ' '.join(seq)
        if len(single) <= PEP8_LLEN and len(single.splitlines()) <= 1:
            return single
        else:
            return '\n'.join(seq)

    def _nullable(self) -> bool:
        return all(s._nullable() for s in self.sequence)

    def callable_at_same_pos(self, rulemap: Mapping[str, Rule] | None = None) -> list[Model]:
        head = list(takewhile(lambda c: c.is_nullable(rulemap), self.sequence))
        if len(head) < len(self.sequence):
            head.append(self.sequence[len(head)])
        return head


@tatsudataclass
class Choice(Model):
    def __post_init__(self):
        super().__post_init__()
        self.options = self.ast
        assert isinstance(self.options, list), repr(self.options)

    def _parse(self, ctx):
        with ctx._choice():
            for o in self.options:
                with ctx._option():
                    ctx.last_node = o._parse(ctx)
                    return ctx.last_node

            lookahead = self.lookahead_str()
            if lookahead:
                raise ctx.newexcept(f'expecting one of: {lookahead}:')
            raise ctx.newexcept('no available options')

    def defines(self):
        return [d for o in self.options for d in o.defines()]

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return set().union(
            *[o.missing_rules(rulenames) for o in self.options],
        )

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

    def callable_at_same_pos(self, rulemap: Mapping[str, Rule] | None = None) -> list[Model]:
        return self.options


@tatsudataclass
class Option(Decorator):
    def _parse(self, ctx):
        result = super()._parse(ctx)
        self._add_defined_attributes(ctx, result)
        return result


@tatsudataclass
class Closure(Decorator):
    def _parse(self, ctx):
        return ctx._closure(lambda: self.exp._parse(ctx))

    def _first(self, k, f) -> ffset:
        efirst = self.exp._first(k, f)
        result = {()}
        for _i in range(k):
            result = kdot(result, efirst, k)
        return {()} | result

    def _pretty(self, lean=False):
        sexp = str(self.exp._pretty(lean=lean))
        if len(sexp.splitlines()) <= 1:
            return f'{{{sexp}}}'
        else:
            return f'{{\n{indent(sexp)}\n}}'

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class PositiveClosure(Closure):
    def _parse(self, ctx):
        return ctx._positive_closure(lambda: self.exp._parse(ctx))

    def _first(self, k, f) -> ffset:
        return self.exp._first(k, f)

    def _pretty(self, lean=False):
        return super()._pretty(lean=lean) + '+'

    def _nullable(self) -> bool:
        return self.exp._nullable()


@tatsudataclass
class Join(Decorator):
    JOINOP = '%'

    sep: Model = Model()

    def __post_init__(self):
        super().__post_init__()
        assert self.sep == self.ast.sep, self.sep

    def _parse(self, ctx):
        def sep():
            return self.sep._parse(ctx)

        def exp():
            return self.exp._parse(ctx)

        return self._do_parse(ctx, exp, sep)

    def _do_parse(self, ctx, exp, sep):
        return ctx._join(exp, sep)

    def _pretty(self, lean=False):
        ssep = self.sep._pretty(lean=lean)
        sexp = str(self.exp._pretty(lean=lean))
        if len(sexp.splitlines()) <= 1:
            return f'{ssep}{self.JOINOP}{{{sexp}}}'
        else:
            return f'{ssep}{self.JOINOP}{{\n{sexp}\n}}'

    def _nullable(self) -> bool:
        return True


class PositiveJoin(Join):
    def _first(self, k, f) -> ffset:
        return self.exp._first(k, f)

    def _do_parse(self, ctx, exp, sep):
        return ctx._positive_join(exp, sep)

    def _pretty(self, lean=False):
        return super()._pretty(lean=lean) + '+'

    def _nullable(self) -> bool:
        return self.exp._nullable()


class LeftJoin(PositiveJoin):
    JOINOP = '<'

    def _do_parse(self, ctx, exp, sep):
        return ctx._left_join(exp, sep)


class RightJoin(PositiveJoin):
    JOINOP = '>'

    def _do_parse(self, ctx, exp, sep):
        return ctx._right_join(exp, sep)


class Gather(Join):
    JOINOP = '.'

    def _do_parse(self, ctx, exp, sep):
        return ctx._gather(exp, sep)


class PositiveGather(Gather):
    def _first(self, k, f) -> ffset:
        return self.exp._first(k, f)

    def _do_parse(self, ctx, exp, sep):
        return ctx._positive_gather(exp, sep)

    def _pretty(self, lean=False):
        return super()._pretty(lean=lean) + '+'

    def _nullable(self) -> bool:
        return self.exp._nullable()


@tatsudataclass
class EmptyClosure(Model):
    def _parse(self, ctx):
        return ctx._empty_closure()

    def _first(self, k, f) -> ffset:
        return {()}

    def _pretty(self, lean=False):
        return '{}'

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class Optional(Decorator):
    def _parse(self, ctx):
        ctx.last_node = None
        self._add_defined_attributes(ctx, ctx.ast)
        with ctx._optional():
            return self.exp._parse(ctx)

    def _first(self, k, f) -> ffset:
        return set({()}) | self.exp._first(k, f)

    def _pretty(self, lean=False):
        exp = self.exp._pretty(lean=lean)
        if len(exp.splitlines()) <= 1:
            return f'[{exp}]'
        return f'[\n{exp}\n]'

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class Cut(Model):
    def _parse(self, ctx):
        ctx._cut()

    def _first(self, k, f) -> ffset:
        return {()}

    def _pretty(self, lean=False):
        return '~'

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class Named(Decorator):
    name: str = ''

    def __post_init__(self):
        super().__post_init__()
        if self.ast is None:
            raise GrammarError('ast in Named cannot be None')
        assert getattr(self, 'name', None) is not None
        self.exp = self.ast.exp

    def _parse(self, ctx):
        value = self.exp._parse(ctx)
        ctx.ast[self.name] = value
        return value

    def defines(self):
        return [(self.name, False), *super().defines()]

    def _pretty(self, lean=False):
        if lean:
            return self.exp._pretty(lean=True)
        return f'{self.name}:{self.exp._pretty(lean=lean)}'


class NamedList(Named):
    def _parse(self, ctx):
        value = self.exp._parse(ctx)
        ctx.ast._setlist(self.name, value)
        return value

    def defines(self):
        return [(self.name, True), *super().defines()]

    def _pretty(self, lean=False):
        if lean:
            return self.exp._pretty(lean=True)
        return f'{self.name}+:{self.exp._pretty(lean=lean)!s}'


class Override(Named):
    def __init__(self, ast: Model):
        super().__init__(ast=AST(name='@', exp=ast))

    def defines(self):
        return self.exp.defines()


class OverrideList(NamedList):
    def __init__(self, ast: list[Model]):
        super().__init__(ast=AST(name='@', exp=ast))

    def defines(self):
        return self.exp.defines()


@tatsudataclass
class Call(Model):
    def __post_init__(self):
        super().__post_init__()
        self.name: str = self.ast
        assert isinstance(self.name, str), self.name

    def follow_ref(self, rulemap: Mapping[str, Rule]) -> Model:
        return rulemap.get(self.name, self)

    def _parse(self, ctx):
        try:
            rule = ctx._find_rule(self.name)
            return rule()
        except KeyError as e:
            raise ctx.newexcept(self.name, exclass=FailedRef) from e

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        if self.name not in rulenames:
            return set({self.name})
        return set()

    def _used_rule_names(self) -> set[str]:
        return {self.name}

    def _first(self, k, f) -> ffset:
        return f[self.name] | {ref(self.name)}

    def _follow(self, k, fl, a):
        fl[self.name] |= a
        return set(a) | {self.name}

    def _pretty(self, lean=False):
        return self.name

    def is_nullable(self, rulemap: Mapping[str, Rule] | None = None) -> bool:
        if rulemap is None:
            return False
        else:
            return rulemap[self.name].is_nullable(rulemap)


class RuleInclude(Decorator):
    def __init__(self, ast: Rule):
        assert isinstance(ast, Rule), str(ast.name)
        super().__init__(ast=ast.exp)
        self.rule = ast

    def _pretty(self, lean=False):
        return f'>{self.rule.name}'


@tatsudataclass
class Rule(Decorator):
    name: str
    params: tuple[str, ...] = field(default_factory=tuple)
    kwparams: dict[str, Any] = field(default_factory=dict)
    decorators: list[str] = field(default_factory=list)
    base: str | None = None
    is_name: bool = False
    is_leftrec: bool = False
    is_memoizable: bool = True

    def __post_init__(self):
        super().__post_init__()
        self.is_name = 'name' in self.decorators
        self.params = self.params or ()

        if not self.kwparams:
            self.kwparams = {}
        elif not isinstance(self.kwparams, dict):
            self.kwparams = dict(self.kwparams)

        assert isinstance(self.kwparams, dict), f'{typename(self)}: {self.kwparams=!r}'

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return self.exp.missing_rules(rulenames)

    def _parse(self, ctx):
        return self._parse_rhs(ctx, self.exp)

    def _parse_rhs(self, ctx, exp):
        ruleinfo = RuleInfo(
            self.name,
            exp._parse,
            self.is_leftrec,
            self.is_memoizable,
            self.is_name,
            self.params,
            self.kwparams,
        )
        return ctx._call(ruleinfo)

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
        str_template = """\
                {is_name}{name}{base}{params}
                    =
                {exp}
                    ;
                """

        if lean:
            params = ''
        else:
            params = (
                ', '.join(self.param_repr(p) for p in self.params)
                if self.params
                else ''
            )

            kwparams = ''
            if self.kwparams:
                kwparams = ', '.join(
                    f'{k}={self.param_repr(v)}'
                    for (k, v) in self.kwparams.items()
                )

            if params and kwparams:
                params = f'({params}, {kwparams})'
            elif kwparams:
                params = f'({kwparams})'
            elif params:
                params = (
                    f'::{params}'
                    if len(self.params) == 1
                    else f'({params})'
                )

        base = f' < {self.base!s}' if self.base else ''

        return trim(str_template).format(
            name=self.name,
            base=base,
            params=params,
            exp=indent(self.exp._pretty(lean=lean)),
            is_name='@name\n' if self.is_name else '',
        )


@tatsudataclass
class BasedRule(Rule):
    baserule: Rule  # note: base is name in the AST from the rule
    rhs: Model = Model()

    def __post_init__(self):
        super().__post_init__()

        assert isinstance(self.baserule, Rule), f'{typename(self.base)}: {self.basrulee=!r}'

        self.params = self.params or self.baserule.params
        self.kwparams = self.kwparams or self.baserule.kwparams
        self.rhs = Sequence(ast=[self.baserule.exp, self.exp])

    def _parse(self, ctx):
        return self._parse_rhs(ctx, self.rhs)

    def defines(self):
        return super().defines() + self.rhs.defines()


@tatsudataclass
class Grammar(Model):
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
        assert isinstance(rules, list), str(rules)
        directives = directives or {}
        self.directives = directives

        config = ParserConfig.new(config=config, **settings)
        config = config.hard_override(**directives)
        self.config = config

        self.rules: list[Rule] = rules
        self._rulemap: dict[str, Rule] = {
            rule.name: rule
            for rule in rules
        }

        if name is None:
            name = self.directives.get('grammar')
        if name is None:
            name = self.config.name
        if name is None and config.filename is not None:
            name = Path(config.filename).stem
        if name is None:
            name = 'My'
        self.name = name

        missing: set[str] = self.missing_rules(set(self._rulemap))
        if missing:
            msg = '\n'.join(['', *sorted(missing)])
            raise GrammarError('Unknown rules, no parser generated:' + msg)

        self._calc_lookahead_sets()

    @property
    def rulemap(self) -> dict[str, Rule]:
        return self._rulemap

    @property
    def keywords(self) -> Collection[str]:
        return self.config.keywords

    @property
    def semantics(self) -> type[object] | None:
        return self.config.semantics

    @semantics.setter
    def semantics(self, value: type[object]):
        self.config.semantics = value

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return set().union(
            *[rule.missing_rules(rulenames) for rule in self.rules],
        )

    def _used_rule_names(self) -> set[str]:
        if not self.rules:
            return set()

        used = {'start', self.rules[0].name}
        prev: set[str] = set()
        while used != prev:
            prev = used
            used |= set().union(
                *[
                    rule._used_rule_names()
                    for rule in self.rules
                    if rule.name in used
                ],
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
            /, *,
            ctx: ParseContext | None = None,
            config: ParserConfig | None = None,
            **settings):
        config = self.config.override_config(config)
        # note: bw-comp: allow overriding directives
        config = config.override(**settings)

        if isinstance(config.semantics, type):
            raise TypeError(
                'semantics must be an object instance or None, '
                f'not class {config.semantics!r}',
            )

        start = config.effective_rule_name()
        if start is None:
            start = self.rules[0].name
            config.start = start
            config.start_rule = start

        if ctx is None:
            ctx = ModelContext(self.rules, config=config)
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
                    else str(value)
                    if directive in str_directives
                    else value
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
        ).rstrip() + '\n'
        return directives + keywords + rules

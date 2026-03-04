#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import field
from typing import Any

from ..ast import AST
from ..builder import ModelBuilderSemantics
from ..contexts import ParseContext
from ..contexts.infos import RuleInfo
from ..objectmodel import Node, tatsudataclass
from ..parserconfig import ParserConfig
from ..util import compress_seq, indent, trim, typename
from .math import ffset, kdot


PEP8_LLEN = 72

_model_classes: list[type[Model]] = []


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

    def _find_rule(self, name: str) -> Callable:
        return self.rulemap[name]._parse
        # return functools.partial(self.rulemap[name]._parse, self)


@tatsudataclass
class Model(Node):
    _lookahead: ffset = field(init=False, default_factory=set)
    _firstset: ffset = field(init=False, default_factory=set)
    _follow_set: ffset = field(init=False, default_factory=set)

    def __init_subclass__(cls: type[Model], **kwargs):
        super().__init_subclass__(**kwargs)
        _model_classes.append(cls)

    @staticmethod
    def model_classes() -> list[type[Model]]:
        return _model_classes

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

        keys = [k for k, ll in defines.items() if not ll]
        list_keys = [k for k, ll in defines.items() if ll]
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

    def is_nullable(self, rulemap: Mapping[str, Rule] | None = None) -> bool:
        return self._nullable()

    def _nullable(self) -> bool:
        return False

    # list of Model that can be invoked at the same position
    def callable_at_same_pos(
        self,
        rulemap: Mapping[str, Rule] | None = None,
    ) -> list[Model]:
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


@tatsudataclass
class NULL(Model):
    def _parse(self, ctx):
        ctx.fail()

    def _pretty(self, lean=False):
        return NULL.__name__

    def _nullable(self) -> bool:
        return False


@tatsudataclass
class Void(Model):
    def _parse(self, ctx):
        ctx.void()

    def _pretty(self, lean=False):
        return '()'

    def _nullable(self) -> bool:
        return True


@tatsudataclass
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

    def _parse(self, ctx) -> Any | None:
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


@tatsudataclass
class NamedBox(Box):
    name: str = field(default='')  # pyright: ignore[reportIncompatibleVariableOverride]


@tatsudataclass
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

    def _parse(self, ctx):
        return self._parse_rhs(ctx, self.exp)

    def _parse_rhs(self, ctx, exp):
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

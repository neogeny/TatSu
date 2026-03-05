# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from ast import literal_eval
from collections.abc import Iterable
from typing import Any

from . import grammars as g
from .builder import ModelBuilderSemantics
from .contexts import ParseContext
from .exceptions import FailedSemantics
from .grammars import _core
from .util import eval_escapes, flatten, re, warning


class TatSuGrammarSemantics(ModelBuilderSemantics):
    def __init__(self, name: str | None = None, context: ParseContext | None = None):
        super().__init__(
            basetype=g.Model,
            constructors=g.model_classes(),  # ty:ignore[invalid-argument-type]
        )
        self.name = name
        self.context = context
        self.rulemap: dict[str, g.Rule] = {}

    def set_context(self, context: ParseContext):
        self.context = context

    @classmethod
    def _validate_literal(cls, ast: Any):
        try:
            literal_eval(repr(str(ast)))
        except SyntaxError as e:
            raise FailedSemantics('literal string error: ' + str(e)) from e

    @classmethod
    def _validate_pattern(cls, ast: Any):
        cls._validate_literal(ast)
        try:
            re.compile(str(ast))
        except (TypeError, re.error) as e:
            raise FailedSemantics('pattern error: ' + str(e)) from e

    def token(self, ast: str) -> g.Token:
        token = ast
        if not token:
            raise FailedSemantics('empty token')
        literal_eval(repr(token))
        return g.Token(ast=token)

    def pattern(self, ast: str) -> g.Pattern:
        pattern = ast
        self._validate_literal(pattern)
        return g.Pattern(ast=pattern)

    def regexes(self, ast: Iterable[str]) -> Iterable[str]:
        pattern = ''.join(ast)
        self._validate_pattern(pattern)
        return ast

    def regex(self, ast: str) -> str:
        pattern = ast
        self._validate_pattern(pattern)
        return pattern

    def string(self, ast):
        return eval_escapes(ast)

    def hex(self, ast):
        return int(ast, 16)

    def float(self, ast):
        return float(ast)

    def int(self, ast):
        return int(ast)

    def null(self, _ast):
        return None

    def cut_deprecated(self, _ast):
        warning('The use of >> for cut is deprecated. Use the ~ symbol instead.')
        return g.Cut()

    def override_single_deprecated(self, ast):
        warning('The use of @ for override is deprecated. Use @: instead')
        return g.Override(ast)

    def sequence(self, ast):
        # if isinstance(ast, list | tuple):
        #     seq = ast
        # else:
        #     seq = ast.sequence
        seq = ast
        assert isinstance(seq, list), str(seq)
        if len(seq) == 1:
            return seq[0]
        return g.Sequence(ast=ast)

    def choice(self, ast):
        return g.Choice(ast=ast)

    def new_name(self, name):
        if name in self.rulemap:
            raise FailedSemantics(f'rule "{name!s}" already defined')
        return name

    def known_name(self, name) -> str:
        if name not in self.rulemap:
            raise FailedSemantics(f'rule "{name!s}" not yet defined')
        return name

    def boolean(self, ast):
        return str(ast).lower() in {'true', 'yes', 'ok', '1'}

    def rule(self, ast):
        decorators = ast.decorators
        name = ast.name
        base = ast.base
        params = ast.params
        kwparams = dict(ast.kwparams) if ast.kwparams else {}

        if 'override' not in decorators and name in self.rulemap:
            self.new_name(name)
        elif 'override' in decorators:
            self.known_name(name)

        if not base:
            rule = g.Rule(
                ast=ast,
                name=name,
                params=params,
                kwparams=kwparams,
                decorators=decorators,
            )
        else:
            self.known_name(base)
            baserule = self.rulemap[base]
            rule = g.BasedRule(
                ast=ast,
                name=name,
                baserule=baserule,
                params=params,
                kwparams=kwparams,
                decorators=decorators,
            )

        self.rulemap[name] = rule
        return rule

    def rule_include(self, ast):
        name = str(ast)
        self.known_name(name)

        rule = self.rulemap[name]
        return g.RuleInclude(ast=ast, rule=rule)

    def grammar(self, ast):
        directives = {d.name: d.value for d in flatten(ast.directives)}
        for value in directives.values():
            literal_eval(repr(value))
        keywords = list(flatten(ast.keywords)) or []

        if directives.get('whitespace') in {'None', 'False'}:
            # NOTE: use '' because None will _not_ override defaults in configuration
            directives['whitespace'] = ''

        name = self.name or directives.get('grammar')
        grammar = _core.Grammar(
            name,
            list(self.rulemap.values()),
            directives=directives,
            keywords=keywords,
        )
        return grammar

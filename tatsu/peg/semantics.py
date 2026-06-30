# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from ast import literal_eval
from collections.abc import Iterable, Sequence
from typing import Any

from .. import peg as g
from ..contexts import ParseContext
from ..contexts.infos import ParseInfo
from ..exceptions import FailedSemantics
from ..objectmodel.builder import ModelBuilderSemantics
from ..util import WARNING_print, eval_escapes, flatten, re, trim


class GrammarSemantics(ModelBuilderSemantics):
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
            raise FailedSemantics(f'"{ast!r}"pattern error: {e!s}') from e

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

    def meta(self, ast: str, *_args) -> g.Meta:
        match ast:
            case "name":
                return g.NameMeta()
            case "int":
                return g.IntMeta()
            case "uint":
                return g.UIntMeta()
            case "float":
                return g.FloatMeta()
            case "bool":
                return g.BoolMeta()
            case _:
                raise FailedSemantics(f'unknown meta: {ast}')

    def deprecated_regex(self, ast: str, _parseinfo: ParseInfo | None = None):
        return self.regex(ast)
        # import warnings
        # if parseinfo:
        #     pi = parseinfo
        #     msg = (
        #         f'Deprecated syntax "?/../?" for regular expressions'
        #         f' at {pi.cursor.input.source} line {pi.line + 1}'
        #         f'\n?/"{ast}"/?'
        #     )
        # else:
        #     msg = 'Deprecated syntax "?/../? for regular expressions"'
        # warnings.warn(
        #     message=msg,
        #     category=DeprecationWarning,
        #     stacklevel=12,
        # )
        # return ast

    def string(self, ast):
        value = ast
        return eval_escapes(value)

    def multiline_string(self, ast):
        value = ast
        value = trim(value.strip()).rstrip()
        return eval_escapes(value)

    def hex(self, ast):
        return int(ast, 16)

    def float(self, ast):
        return float(ast)

    def int(self, ast):
        return int(ast)

    def none(self, _ast):
        return None

    def boolean(self, ast):
        return str(ast).lower() not in {'false', 'no', 'fail', '0'}

    # JSON
    def null(self, _ast):
        return None

    # JSON
    def true(self, _ast):
        return True

    # JSON
    def false(self, _ast):
        return False

    # JSON
    def number(self, ast):
        if isinstance(ast, str):
            return literal_eval(ast)
        return ast

    def cut_deprecated(self, _ast):
        WARNING_print('The use of >> for cut is deprecated. Use the ~ symbol instead.')
        return g.Cut()

    def override_single_deprecated(self, ast):
        WARNING_print('The use of @ for override is deprecated. Use @: instead')
        return g.Override(ast)

    def sequence(self, ast):
        seq = ast
        assert isinstance(seq, Sequence), str(seq)
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

    def rule(self, ast):
        decorators = ast.decorators or []
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

        return g.RuleInclude(ast=ast, name=name)

    def grammar(self, ast):
        directives = {d.name: d.value for d in flatten(ast.directives) if d}
        for value in directives.values():
            literal_eval(repr(value))
        keywords = tuple(flatten(ast.keywords)) or ()

        if directives.get('whitespace') in {'None', 'False'}:
            # NOTE: use '' because None will _not_ override defaults in configuration
            directives['whitespace'] = ''

        name = self.name or directives.get('grammar')
        grammar = g.Grammar(
            name,
            list(self.rulemap.values()),
            directives=directives,
            keywords=keywords,
        )
        return grammar

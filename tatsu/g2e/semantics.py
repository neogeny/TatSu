#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
from typing import Any

from .. import grammars as g
from ..contexts import AST


def camel2py(name: Any) -> str:
    return re.sub(
        r'([a-z0-9])([A-Z])',
        lambda m: m.group(1) + '_' + m.group(2).lower(),
        str(name),
    )


class ANTLRSemantics:
    def __init__(self, name):
        self.name = name
        self.tokens = {}
        self.token_rules = {}
        self.synthetic_rules = []

    def grammar(self, ast: AST) -> g.Grammar:
        # Add any defined tokens that were not part of a rule
        for name, exp in self.tokens.items():
            if name not in self.token_rules:
                self.synthetic_rules.append(g.Rule(name=name, exp=exp))

        # Resolve or fail any remaining placeholders
        for name, exp in self.token_rules.items():
            if isinstance(exp, g.Synth):
                # This placeholder was referenced but never defined.
                # Create a new rule that fails.
                rule_name = name.lower()
                if not any(r.name == rule_name for r in ast.rules):
                    self.synthetic_rules.append(g.Rule(name=rule_name, exp=g.Fail()))

        return g.Grammar(
            self.name,
            [r for r in (*ast.rules, *self.synthetic_rules) if r is not None],
        )

    def rule(self, ast: AST) -> g.Rule | None:
        name = camel2py(ast.name)
        exp = ast.exp
        if name[0].isupper():
            name = name.upper()
            # This is a token rule.
            # If a placeholder (Synth) for this token already exists, update it.
            if name in self.token_rules and isinstance(
                self.token_rules.get(name), g.Synth
            ):
                self.token_rules[name].exp = exp
            else:
                # Otherwise, just store the token definition.
                self.token_rules[name] = exp

            # If the expression is not a simple token, it's a fragment rule
            # that defines a token. We need a standard rule for it.
            if not isinstance(exp, g.Token):
                return g.Rule(ast=ast, name=name.lower(), exp=exp)

            # Simple token rules do not generate g.Rule objects directly
            return None

        return g.Rule(ast=ast, name=name, params=ast.params, kwparams=ast.kwparams)

    def alternatives(self, ast: AST) -> g.Model:
        options = [o for o in ast.options if o is not None]
        if len(options) == 1:
            return options[0]
        else:
            options = [g.Option(o) for o in options]
            return g.Choice(options)

    def elements(self, ast: list[g.Model]) -> g.Model:
        elements = [e for e in ast if e is not None]
        if not elements:
            return g.Void()
        elif len(elements) == 1:
            return elements[0]
        else:
            return g.Sequence(elements)

    def predicate_or_action(self, _ast: Any) -> None:
        return None

    def named(self, ast: AST) -> g.Named:
        if ast.force_list:
            return g.NamedList(ast)
        else:
            return g.Named(ast)

    def syntactic_predicate(self, _ast: Any) -> None:
        return None

    def optional(self, ast: g.Optional) -> g.Optional:
        return g.Optional(ast)

    def closure(self, ast: g.Model) -> g.Closure:
        if isinstance(ast, g.Group):
            # noinspection PyUnresolvedReferences
            ast = ast.exp
        return g.Closure(ast)

    def positive_closure(self, ast: g.Model) -> g.Closure:
        if isinstance(ast, g.Group):
            # noinspection PyUnresolvedReferences
            ast = ast.exp
        return g.PositiveClosure(ast)

    def negative(self, ast: g.Model) -> g.Sequence:
        neg = g.NegativeLookahead(ast)
        any = g.Pattern('.')
        return g.Sequence([neg, any])

    def subexp(self, ast: g.Model) -> g.Group:
        return g.Group(ast)

    def regexp(self, ast: AST) -> g.Pattern:
        pattern = ''.join(ast)
        regex = re.compile(pattern)
        return g.Pattern(regex.pattern)

    def charset_optional(self, ast: AST) -> str:
        return f'{ast}?'

    def charset_closure(self, ast: AST) -> str:
        return f'{ast}*'

    def charset_positive_closure(self, ast: AST) -> str:
        return f'{ast}+'

    def charset_or(self, ast: AST) -> str:
        return '[{}]'.format(''.join(ast))

    def charset_negative_or(self, ast: AST) -> str:
        return '[^{}]'.format(''.join(ast))

    @staticmethod
    def escape(s: str) -> str:
        return ''.join('\\' + c if c in '[]().*+{}^$' else c for c in s)

    def charset_atom(self, ast: AST) -> AST:
        return ast

    def charset_char(self, ast: AST) -> AST:
        return ast

    def charset_range(self, ast: AST) -> str:
        return f'{ast.first}-{ast.last}'

    def newranges(self, ast: AST) -> g.Pattern:
        pattern = ''.join(ast)
        regex = re.compile(pattern)
        return g.Pattern(regex.pattern)

    def newrange(self, ast: AST) -> str:
        pattern = '[{}]{}'.format(ast.range, ast.repeat or '')
        re.compile(pattern)
        return pattern

    def negative_newrange(self, ast: AST) -> str:
        pattern = '[^{}]{}'.format(ast.range, ast.repeat or '')
        re.compile(pattern)
        return pattern

    def call(self, ast: str) -> g.Call:
        assert ast[0].islower()
        return g.Call(camel2py(ast))

    def any(self, _ast: AST) -> g.Pattern:
        return g.Pattern(r'\w+|\S+')

    def string(self, ast: AST) -> g.Token:
        text = str(ast)
        if isinstance(text, list):
            text = ''.join(text)
        return g.Token(text)

    def eof(self, _ast: AST) -> g.EOF:
        return g.EOF()

    def token(self, ast: AST) -> g.Token | g.Void:
        name = ast.name
        if ast.exp:
            exp = g.Token(ast.value)
            self.tokens[name] = exp
        else:
            exp = g.Void()  # type: ignore
            rule = g.Rule(ast=exp, name=name)
            self.synthetic_rules.append(rule)
        return exp

    def token_ref(self, ast: AST) -> g.Model:
        name = camel2py(ast).upper()

        # If the token is already fully defined, return it
        if name in self.token_rules and not isinstance(
            self.token_rules[name], g.Synth
        ):
            return self.token_rules[name]

        # If a placeholder exists, return it
        if name in self.token_rules:
            return self.token_rules[name]

        # Otherwise, create a new placeholder for a future definition
        exp = g.Synth(g.Call(name.lower()))
        self.token_rules[name] = exp
        return exp

#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
from itertools import chain
from typing import Any

from .. import grammars as model
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

    def grammar(self, ast: AST) -> model.Grammar:
        # Add any defined tokens that were not part of a rule
        for name, exp in self.tokens.items():
            if name not in self.token_rules:
                self.synthetic_rules.append(model.Rule(name=name, exp=exp))

        # Add any token rules that were referenced but not explicitly defined
        # (they will still be Synth(...) placeholders)
        for name, exp in self.token_rules.items():
            if isinstance(exp, model.Synth):
                # Create a rule for this placeholder
                rule_name = name.lower()
                if not any(r.name == rule_name for r in ast.rules):
                    self.synthetic_rules.append(model.Rule(name=rule_name, exp=exp))

        return model.Grammar(
            self.name,
            [r for r in chain(ast.rules, self.synthetic_rules) if r is not None],
        )

    def rule(self, ast: AST) -> model.Rule | None:
        name = camel2py(ast.name)
        exp = ast.exp
        if name[0].isupper():
            name = name.upper()
            # This is a token rule.
            # If a placeholder (Synth) for this token already exists, update it.
            if name in self.token_rules and isinstance(
                self.token_rules.get(name), model.Synth
            ):
                self.token_rules[name].exp = exp
            else:
                # Otherwise, just store the token definition.
                self.token_rules[name] = exp

            # If the expression is not a simple token, it's a fragment rule
            # that defines a token. We need a standard rule for it.
            if not isinstance(exp, model.Token):
                return model.Rule(ast=ast, name=name.lower(), exp=exp)

            # Simple token rules do not generate model.Rule objects directly
            return None

        return model.Rule(ast=ast, name=name, params=ast.params, kwparams=ast.kwparams)

    def alternatives(self, ast: AST) -> model.Model:
        options = [o for o in ast.options if o is not None]
        if len(options) == 1:
            return options[0]
        else:
            options = [model.Option(o) for o in options]
            return model.Choice(options)

    def elements(self, ast: list[model.Model]) -> model.Model:
        elements = [e for e in ast if e is not None]
        if not elements:
            return model.Void()
        elif len(elements) == 1:
            return elements[0]
        else:
            return model.Sequence(elements)

    def predicate_or_action(self, _ast: Any) -> None:
        return None

    def named(self, ast: AST) -> model.Named:
        if ast.force_list:
            return model.NamedList(ast)
        else:
            return model.Named(ast)

    def syntactic_predicate(self, _ast: Any) -> None:
        return None

    def optional(self, ast: model.Optional) -> model.Optional:
        return model.Optional(ast)

    def closure(self, ast: model.Model) -> model.Closure:
        if isinstance(ast, model.Group):
            # noinspection PyUnresolvedReferences
            ast = ast.exp
        return model.Closure(ast)

    def positive_closure(self, ast: model.Model) -> model.Closure:
        if isinstance(ast, model.Group):
            # noinspection PyUnresolvedReferences
            ast = ast.exp
        return model.PositiveClosure(ast)

    def negative(self, ast: model.Model) -> model.Sequence:
        neg = model.NegativeLookahead(ast)
        any = model.Pattern('.')
        return model.Sequence([neg, any])

    def subexp(self, ast: model.Model) -> model.Group:
        return model.Group(ast)

    def regexp(self, ast: AST) -> model.Pattern:
        pattern = ''.join(ast)
        regex = re.compile(pattern)
        return model.Pattern(regex.pattern)

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

    def newranges(self, ast: AST) -> model.Pattern:
        pattern = ''.join(ast)
        regex = re.compile(pattern)
        return model.Pattern(regex.pattern)

    def newrange(self, ast: AST) -> str:
        pattern = '[{}]{}'.format(ast.range, ast.repeat or '')
        re.compile(pattern)
        return pattern

    def negative_newrange(self, ast: AST) -> str:
        pattern = '[^{}]{}'.format(ast.range, ast.repeat or '')
        re.compile(pattern)
        return pattern

    def call(self, ast: str) -> model.Call:
        assert ast[0].islower()
        return model.Call(camel2py(ast))

    def any(self, _ast: AST) -> model.Pattern:
        return model.Pattern(r'\w+|\S+')

    def string(self, ast: AST) -> model.Token:
        text = str(ast)
        if isinstance(text, list):
            text = ''.join(text)
        return model.Token(text)

    def eof(self, _ast: AST) -> model.EOF:
        return model.EOF()

    def token(self, ast: AST) -> model.Token | model.Void:
        name = ast.name
        if ast.exp:
            exp = model.Token(ast.value)
            self.tokens[name] = exp
        else:
            exp = model.Void()  # type: ignore
            rule = model.Rule(ast=exp, name=name)
            self.synthetic_rules.append(rule)
        return exp

    def token_ref(self, ast: AST) -> model.Model:
        name = camel2py(ast).upper()

        # If the token is already fully defined, return it
        if name in self.token_rules and not isinstance(
            self.token_rules[name], model.Synth
        ):
            return self.token_rules[name]

        # If a placeholder exists, return it
        if name in self.token_rules:
            return self.token_rules[name]

        # Otherwise, create a new placeholder for a future definition
        exp = model.Synth(model.Call(name.lower()))
        self.token_rules[name] = exp
        return exp

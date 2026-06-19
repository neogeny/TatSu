#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
from typing import Any

from .. import peg as g
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

        # For non-trivial token rules (non-Token expressions), use Fail()
        # since converting ANTLR patterns to Python regex is not viable.
        for rule in ast.rules:
            if rule is None:
                continue
            token_name = rule.name.upper() if rule.name else ''
            if token_name in self.token_rules and not isinstance(
                self.token_rules.get(token_name), g.Synth
            ):
                exp = self.token_rules[token_name]
                if not isinstance(exp, g.Token):
                    rule.exp = g.Fail()

        # Resolve or fail any remaining placeholders
        for name, exp in self.token_rules.items():
            if isinstance(exp, g.Synth):
                # This placeholder was referenced but never defined.
                # Create a new rule that fails.
                rule_name = name
                if not any(r.name == rule_name for r in ast.rules):
                    self.synthetic_rules.append(g.Rule(name=rule_name, exp=g.Fail()))

        # Deduplicate rules by name, keeping the first occurrence
        all_rules = [r for r in (*ast.rules, *self.synthetic_rules) if r is not None]
        seen: set[str] = set()
        deduped = []
        for r in all_rules:
            if r.name not in seen:
                seen.add(r.name)
                deduped.append(r)
        return g.Grammar(self.name, deduped)

    def rule(self, ast: AST) -> g.Rule | None:
        name = camel2py(ast.name)
        exp = ast.exp
        if name[0].isupper():
            name = name.upper()
            old = self.token_rules.get(name)
            self.token_rules[name] = exp
            if isinstance(exp, g.Token) and isinstance(old, g.Synth):
                old.exp = exp
            return g.Rule(name=name, exp=exp)

        return g.Rule(name=name, exp=exp)

    def alternatives(self, ast: AST) -> g.Model:
        options = [o for o in ast.options if o is not None]
        if len(options) == 1:
            return options[0]
        else:
            options = [
                g.Option(
                    exp=g.Group(exp=o) if isinstance(o, (g.Choice, g.Sequence)) else o
                )
                for o in options
            ]
            return g.Choice(options=options)

    def elements(self, ast: list[g.Model]) -> g.Model:
        elements = [e for e in ast if e is not None]
        if not elements:
            return g.Void()
        elif len(elements) == 1:
            return elements[0]
        else:
            return g.Sequence(sequence=elements)

    def predicate_or_action(self, _ast: Any) -> None:
        return None

    def named(self, ast: AST) -> g.Named:
        if ast.force_list:
            return g.NamedList(name=ast.name, exp=ast.exp)
        else:
            return g.Named(name=ast.name, exp=ast.exp)

    def syntactic_predicate(self, _ast: Any) -> None:
        return None

    def optional(self, ast: g.Model) -> g.Optional:
        if isinstance(ast, g.Group):
            ast = ast.exp
        return g.Optional(exp=ast)

    def closure(self, ast: g.Model) -> g.Closure:
        if isinstance(ast, g.Group):
            ast = ast.exp
        return g.Closure(exp=ast)

    def positive_closure(self, ast: g.Model) -> g.Closure:
        if isinstance(ast, g.Group):
            ast = ast.exp
        return g.PositiveClosure(exp=ast)

    def negative(self, ast: g.Model) -> g.Sequence:
        neg = g.NegativeLookahead(exp=ast)
        any = g.Pattern(pattern='.')
        return g.Sequence(sequence=[neg, any])

    def subexp(self, ast: g.Model) -> g.Group:
        return g.Group(exp=ast)

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
        return g.Call(name=camel2py(ast))

    def any(self, _ast: AST) -> g.Pattern:
        return g.Pattern(r'\w+|\S+')

    def string(self, ast: AST) -> g.Token:
        text = str(ast)
        if isinstance(text, list):
            text = ''.join(text)
        return g.Token(token=text)

    def eof(self, _ast: AST) -> g.EOF:
        return g.EOF()

    def token(self, ast: AST) -> g.Token | g.Void:
        name = ast.name
        if ast.exp:
            exp = g.Token(token=ast.value)
            self.tokens[name] = exp
        else:
            exp = g.Void()  # type: ignore
            rule = g.Rule(exp=exp, name=name)
            self.synthetic_rules.append(rule)
        return exp

    def token_ref(self, ast: AST) -> g.Model:
        name = camel2py(ast).upper()

        if name in self.token_rules and not isinstance(self.token_rules[name], g.Synth):
            result = self.token_rules[name]
            if isinstance(result, g.Token):
                return result
            return g.Call(name=name)

        if name in self.token_rules:
            return self.token_rules[name]

        exp = g.Synth(exp=g.Call(name=name))
        self.token_rules[name] = exp
        return exp

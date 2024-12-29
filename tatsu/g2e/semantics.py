from __future__ import annotations

import re
from itertools import chain

from tatsu import grammars as model
from tatsu.ast import AST


def camel2py(name):
    return re.sub(
        r'([a-z0-9])([A-Z])',
        lambda m: m.group(1) + '_' + m.group(2).lower(),
        name,
    )


class ANTLRSemantics:
    def __init__(self, name):
        self.name = name
        self.tokens = {}
        self.token_rules = {}
        self.synthetic_rules = []

    def grammar(self, ast):
        return model.Grammar(
            self.name,
            [
                r
                for r in chain(ast.rules, self.synthetic_rules)
                if r is not None
            ],
        )

    def rule(self, ast):
        name = camel2py(ast.name)
        exp = ast.exp
        if name[0].isupper():
            name = name.upper()
            if isinstance(exp, model.Token):
                if name in self.token_rules:
                    self.token_rules[
                        name
                    ].exp = exp  # it is a model._Decorator
                else:
                    self.token_rules[name] = exp
                return None
            elif not ast.fragment and not isinstance(exp, model.Sequence):
                ref = model.RuleRef(name.lower())
                if name in self.token_rules:
                    self.token_rules[name].exp = ref
                else:
                    self.token_rules[name] = ref
                name = name.lower()

        return model.Rule(ast, name, exp, ast.params, ast.kwparams)

    def alternatives(self, ast):
        options = [o for o in ast.options if o is not None]
        if len(options) == 1:
            return options[0]
        else:
            options = [model.Option(o) for o in options]
            return model.Choice(options)

    def elements(self, ast):
        elements = [e for e in ast if e is not None]
        if not elements:
            return model.Void()
        elif len(elements) == 1:
            return elements[0]
        else:
            return model.Sequence(AST(sequence=elements))

    def predicate_or_action(self, ast):
        return None

    def named(self, ast):
        if ast.force_list:
            return model.NamedList(ast)
        else:
            return model.Named(ast)

    def syntactic_predicate(self, ast):
        return None

    def optional(self, ast):
        if isinstance(ast, model.Group | model.Optional | model.Closure):
            ast = ast.exp
        return model.Optional(ast)

    def closure(self, ast):
        if isinstance(ast, model.Group | model.Optional):
            ast = ast.exp
        return model.Closure(ast)

    def positive_closure(self, ast):
        if isinstance(ast, model.Group):
            ast = ast.exp
        return model.PositiveClosure(ast)

    def negative(self, ast):
        neg = model.NegativeLookahead(ast)
        any = model.Pattern('.')
        return model.Sequence(AST(sequence=[neg, any]))

    def subexp(self, ast):
        return model.Group(ast)

    def regexp(self, ast):
        pattern = ''.join(ast)
        re.compile(pattern)
        return model.Pattern(pattern)

    def charset_optional(self, ast):
        return f'{ast}?'

    def charset_closure(self, ast):
        return f'{ast}*'

    def charset_positive_closure(self, ast):
        return f'{ast}+'

    def charset_or(self, ast):
        return '[{}]'.format(''.join(ast))

    def charset_negative_or(self, ast):
        return '[^{}]'.format(''.join(ast))

    @staticmethod
    def escape(s):
        return ''.join('\\' + c if c in '[]().*+{}^$' else c for c in s)

    def charset_atom(self, ast):
        return ast

    def charset_char(self, ast):
        return ast

    def charset_range(self, ast):
        return f'{ast.first}-{ast.last}'

    def newranges(self, ast):
        pattern = ''.join(ast)
        re.compile(pattern)
        return model.Pattern(pattern)

    def newrange(self, ast):
        pattern = '[{}]{}'.format(ast.range, ast.repeat or '')
        re.compile(pattern)
        return pattern

    def negative_newrange(self, ast):
        pattern = '[^{}]{}'.format(ast.range, ast.repeat or '')
        re.compile(pattern)
        return pattern

    def rule_ref(self, ast):
        assert ast[0].islower()
        return model.RuleRef(camel2py(ast))

    def any(self, ast):
        return model.Pattern(r'\w+|\S+')

    def string(self, ast):
        text = ast
        if isinstance(text, list):
            text = ''.join(text)
        return model.Token(text)

    def eof(self, ast):
        return model.EOF()

    def token(self, ast):
        name = ast.name
        if ast.value:
            exp = model.Token(ast.value)
            self.tokens[name] = exp
        else:
            exp = model.Fail()
            rule = model.Rule(ast, name, exp, [], {})
            self.synthetic_rules.append(rule)
        return exp

    def token_ref(self, ast):
        name = camel2py(ast).upper()

        value = self.tokens.get(name)
        if value and isinstance(value, model.Model):
            return value

        if name in self.token_rules:
            exp = self.token_rules[name]
        else:
            exp = model.Decorator(model.RuleRef(name))
            self.token_rules[name] = exp
        return exp

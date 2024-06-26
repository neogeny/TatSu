from __future__ import annotations

from collections.abc import Sequence

from . import grammars
from .exceptions import FailedSemantics
from .semantics import ModelBuilderSemantics
from .util import eval_escapes, flatten, re, warning


class EBNFGrammarSemantics(ModelBuilderSemantics):
    def __init__(self, grammar_name):
        super().__init__(
            base_type=grammars.Model, types=grammars.Model.classes(),
        )
        self.grammar_name = grammar_name
        self.rules = {}

    def token(self, ast, *args):
        token = ast
        if not token:
            raise FailedSemantics('empty token')
        return grammars.Token(token)

    def pattern(self, ast, *args):
        return grammars.Pattern(ast)

    def regexes(self, ast, *args):
        pattern = ''.join(ast)
        try:
            re.compile(pattern)
        except (TypeError, re.error) as e:
            raise FailedSemantics('regexp error: ' + str(e)) from e
        return ast

    def regex(self, ast, *args):
        pattern = ast
        try:
            re.compile(pattern)
        except (TypeError, re.error) as e:
            raise FailedSemantics('regexp error: ' + str(e)) from e
        return pattern

    def string(self, ast):
        return eval_escapes(ast)

    def hex(self, ast):
        return int(ast, 16)

    def float(self, ast):
        return float(ast)

    def int(self, ast):
        return int(ast)

    def null(self, ast):
        return None

    def cut_deprecated(self, ast, *args):
        warning(
            'The use of >> for cut is deprecated. Use the ~ symbol instead.',
        )
        return grammars.Cut()

    def override_single_deprecated(self, ast, *args):
        warning('The use of @ for override is deprecated. Use @: instead')
        return grammars.Override(ast)

    def sequence(self, ast, *args):
        seq = ast.sequence
        assert isinstance(seq, Sequence), str(seq)
        if len(seq) == 1:
            return seq[0]
        return grammars.Sequence(ast)

    def choice(self, ast, *args):
        if len(ast) == 1:
            return ast[0]
        return grammars.Choice(ast)

    def new_name(self, name):
        if name in self.rules:
            raise FailedSemantics(f'rule "{name!s}" already defined')
        return name

    def known_name(self, name):
        if name not in self.rules:
            raise FailedSemantics(f'rule "{name!s}" not yet defined')
        return name

    def boolean(self, ast):
        return str(ast).lower() in {'true', 'yes', 'ok', '1'}

    def rule(self, ast, *args):
        decorators = ast.decorators
        name = ast.name
        exp = ast.exp
        base = ast.base
        params = ast.params
        kwparams = dict(ast.kwparams) if ast.kwparams else None

        if 'override' not in decorators and name in self.rules:
            self.new_name(name)
        elif 'override' in decorators:
            self.known_name(name)

        if not base:
            rule = grammars.Rule(
                ast, name, exp, params, kwparams, decorators=decorators,
            )
        else:
            self.known_name(base)
            base_rule = self.rules[base]
            rule = grammars.BasedRule(
                ast,
                name,
                exp,
                base_rule,
                params,
                kwparams,
                decorators=decorators,
            )

        self.rules[name] = rule
        return rule

    def rule_include(self, ast, *args):
        name = str(ast)
        self.known_name(name)

        rule = self.rules[name]
        return grammars.RuleInclude(rule)

    def grammar(self, ast, *args):
        directives = {d.name: d.value for d in flatten(ast.directives)}
        keywords = list(flatten(ast.keywords)) or []

        if directives.get('whitespace') in {'None', 'False'}:
            # NOTE: use '' because None will _not_ override defaults in configuration
            directives['whitespace'] = ''

        name = self.grammar_name or directives.get('grammar')
        return grammars.Grammar(
            name,
            list(self.rules.values()),
            directives=directives,
            keywords=keywords,
        )

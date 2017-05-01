# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict

from tatsu.util import simplify_list
from tatsu.util import eval_escapes
from tatsu.util import warning
from tatsu.util import builtins
from tatsu.util import re, RE_FLAGS

from tatsu.exceptions import FailedSemantics
from tatsu.exceptions import SemanticError

from tatsu.objectmodel import Node
from tatsu.objectmodel import BASE_CLASS_TOKEN

from tatsu.synth import synthesize
from tatsu import grammars


class ASTSemantics(object):

    def group(self, ast, *args):
        return simplify_list(ast)

    def element(self, ast, *args):
        return simplify_list(ast)

    def sequence(self, ast, *args):
        return simplify_list(ast)

    def choice(self, ast, *args):
        if len(ast) == 1:
            return simplify_list(ast[0])
        return ast


class ModelBuilderSemantics(object):
    """ Intended as a semantic action for parsing, a ModelBuilderSemantics creates
        nodes using the class name given as first parameter to a grammar
        rule, and synthesizes the class/type if it's not known.
    """
    def __init__(self, context=None, base_type=Node, types=None):
        self.ctx = context
        self.base_type = base_type

        self.constructors = dict()

        for t in types or ():
            self._register_constructor(t)

    def _register_constructor(self, constructor):
        self.constructors[constructor.__name__] = constructor
        return constructor

    def _find_existing_constructor(self, typename):
        constructor = builtins
        for name in typename.split('.'):
            try:
                context = vars(constructor)
            except Exception as e:
                raise SemanticError(
                    'Could not find constructor for %s (%s): %s'
                    % (typename, type(constructor).__name__, str(e))
                )
            if name in context:
                constructor = context[name]
            else:
                constructor = None
                break
        return constructor

    def _get_constructor(self, typename, base):
        typename = str(typename)  # cannot be unicode in Python 2.7

        if typename in self.constructors:
            return self.constructors[typename]

        constructor = (
            self._find_existing_constructor(typename) or
            synthesize(typename, base)
        )

        return self._register_constructor(constructor)

    def _default(self, ast, *args, **kwargs):
        if not args:
            return ast

        typespec = args[0].split(BASE_CLASS_TOKEN)
        typename = typespec[0]
        bases = typespec[1:]

        base = self.base_type
        for base in bases:
            base = self._get_constructor(bases[0], base)

        constructor = self._get_constructor(typename, base)
        try:
            if type(constructor) is type and issubclass(constructor, Node):
                return constructor(*args[1:], ast=ast, ctx=self.ctx, **kwargs)
            else:
                return constructor(ast, *args[1:], **kwargs)
        except Exception as e:
            raise SemanticError(
                'Could not call constructor for %s: %s'
                % (typename, str(e))
            )


class EBNFGrammarSemantics(ModelBuilderSemantics):
    def __init__(self, grammar_name):
        super(EBNFGrammarSemantics, self).__init__(
            base_type=grammars.Model,
            types=grammars.Model.classes()
        )
        self.grammar_name = grammar_name
        self.rules = OrderedDict()

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
            re.compile(pattern, RE_FLAGS)
        except (TypeError, re.error) as e:
            raise FailedSemantics('regexp error: ' + str(e))
        return ast

    def regex(self, ast, *args):
        pattern = ast
        try:
            re.compile(pattern, RE_FLAGS)
        except (TypeError, re.error) as e:
            raise FailedSemantics('regexp error: ' + str(e))
        return pattern

    def string(self, ast):
        return eval_escapes(ast)

    def hext(self, ast):
        return int(ast, 16)

    def float(self, ast):
        return float(ast)

    def int(self, ast):
        return int(ast)

    def cut_deprecated(self, ast, *args):
        warning('The use of >> for cut is deprecated. Use the ~ symbol instead.')
        return grammars.Cut()

    def override_single_deprecated(self, ast, *args):
        warning('The use of @ for override is deprecated. Use @: instead')
        return grammars.Override(ast)

    def sequence(self, ast, *args):
        seq = ast.sequence
        assert isinstance(seq, list), str(seq)
        if len(seq) == 1:
            return seq[0]
        return grammars.Sequence(ast)

    def choice(self, ast, *args):
        if len(ast) == 1:
            return ast[0]
        return grammars.Choice(ast)

    def new_name(self, name):
        if name in self.rules:
            raise FailedSemantics('rule "%s" already defined' % str(name))
        return name

    def known_name(self, name):
        if name not in self.rules:
            raise FailedSemantics('rule "%s" not yet defined' % str(name))
        return name

    def boolean(self, ast):
        return eval(ast)

    def rule(self, ast, *args):
        decorators = ast.decorators
        name = ast.name
        exp = ast.exp
        base = ast.base
        params = ast.params
        kwparams = OrderedDict(ast.kwparams) if ast.kwparams else None

        if 'override' not in decorators and name in self.rules:
            self.new_name(name)
        elif 'override' in decorators:
            self.known_name(name)

        if not base:
            rule = grammars.Rule(ast, name, exp, params, kwparams, decorators=decorators)
        else:
            self.known_name(base)
            base_rule = self.rules[base]
            rule = grammars.BasedRule(ast, name, exp, base_rule, params, kwparams, decorators=decorators)

        self.rules[name] = rule
        return rule

    def rule_include(self, ast, *args):
        name = str(ast)
        self.known_name(name)

        rule = self.rules[name]
        return grammars.RuleInclude(rule)

    def grammar(self, ast, *args):
        directives = OrderedDict((d.name, d.value) for d in ast.directives)
        keywords = set(ast.keywords or [])
        return grammars.Grammar(
            self.grammar_name,
            list(self.rules.values()),
            directives=directives,
            keywords=keywords
        )

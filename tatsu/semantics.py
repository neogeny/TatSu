# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from tatsu.util import simplify_list
from tatsu.util import builtins
from tatsu.exceptions import SemanticError
from tatsu.objectmodel import Node
from tatsu.objectmodel import BASE_CLASS_TOKEN
from tatsu.synth import synthesize


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

        constructor = self._find_existing_constructor(typename)
        if not constructor:
            constructor = synthesize(typename, base)

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

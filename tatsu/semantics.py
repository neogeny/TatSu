from __future__ import annotations

import builtins
import inspect
import keyword
from collections.abc import Callable, Iterable, Mapping, MutableMapping
from typing import Any

from .contexts import ParseContext
from .ngmodel import NodeBase
from .objectmodel import Node
from .synth import registered_synthetics, synthesize
from .util import simplify_list


class ASTSemantics:
    def group(self, ast: Any, *args) -> Any:
        return simplify_list(ast)

    def element(self, ast: Any, *args) -> Any:
        return simplify_list(ast)

    def sequence(self, ast: Any, *args) -> Any:
        return simplify_list(ast)

    def choice(self, ast: Any, *args) -> Any:
        if len(ast) == 1:
            return simplify_list(ast[0])
        return ast


class ModelBuilderSemantics:
    """Intended as a semantic action for parsing, a ModelBuilderSemantics creates
    nodes using the class name given as first parameter to a grammar
    rule, and synthesizes the class/type if it's not known.
    """

    def __init__(
            self,
            context: ParseContext | None = None,
            base_type: type[NodeBase] = Node,
            types: Iterable[Callable] | None = None):
        self.ctx = context
        self.base_type = base_type

        self.constructors: MutableMapping[str, Callable] = {}

        for t in types or ():
            self._register_constructor(t)

    def _register_constructor(self, constructor: Callable) -> Callable:
        if hasattr(constructor, '__name__') and isinstance(constructor.__name__, str):
            self.constructors[str(constructor.__name__)] = constructor
        return constructor

    def _find_existing_constructor(self, typename: str) -> Callable | None:
        context: Mapping[Any, Any] = vars(builtins) | registered_synthetics()
        constructor = context.get(typename)
        if constructor is not None:
            return constructor

        for name in typename.split('.'):
            if name not in context:
                return None

            constructor = context[name]
            if hasattr(constructor, '__dict__'):
                context = vars(constructor)
            else:
                context = {}

        return constructor

    def _get_constructor(self, typename, base):
        typename = str(typename)

        if typename in self.constructors:
            return self.constructors[typename]

        constructor = self._find_existing_constructor(typename)
        if not constructor:
            constructor = synthesize(typename, base)

        return self._register_constructor(constructor)

    def _find_actual_params(self, fun: Callable, ast, args, kwargs) -> tuple[list, dict]:
        if hasattr(fun, '__name__') and fun.__name__ in vars(builtins):
            return [ast], {}

        declared = inspect.signature(fun).parameters
        params = []
        kwparams = kwargs
        known_params = {
            'ast': ast,
            'ctx': self.ctx,
            'exp': ast,
            'kwargs': {},
        }
        for name, var in known_params.items():
            if name not in declared:
                continue
            param = declared[name]
            match param.kind:
                case inspect.Parameter.POSITIONAL_ONLY:
                    params.append(var)
                case inspect.Parameter.VAR_KEYWORD:
                    kwparams |= kwargs
                case _:
                    kwparams[name] = var
        params.extend(args)
        if not (params or kwparams):
            params = [ast]
        return params, kwparams

    def _default(self, ast, *args, **kwargs) -> Any:
        if not args:
            return ast

        def is_reserved(name) -> bool:
            return (
                keyword.iskeyword(name) or
                keyword.issoftkeyword(name) or
                name in {'type', 'list', 'dict', 'set'}
            )

        def mangle(name: str) -> str:
            while is_reserved(name):
                name += '_'
            return name

        typespec = [mangle(s) for s in args[0].split('::')]
        typename = typespec[0]
        bases = reversed(typespec)

        base = self.base_type
        for base_ in bases:
            base = self._get_constructor(base_, base)

        constructor = self._get_constructor(typename, base)
        params, kwparams = self._find_actual_params(constructor, ast, args[1:], kwargs)

        return constructor(*params, **kwparams)

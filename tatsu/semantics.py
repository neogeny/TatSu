from __future__ import annotations

import builtins
import inspect
import keyword
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .contexts import ParseContext
from .objectmodel import Node
from .synth import registered_synthetics, synthesize
from .util import simplify_list


@dataclass
class ActualParameters:
    params: list[Any] = field(default_factory=list)
    param_names: dict[str, Any] = field(default_factory=dict)
    kwparams: dict[str, Any] = field(default_factory=dict)
    has_args: bool = False
    has_kwargs: bool = False

    def has_any_params(self) -> bool:
        return bool(self.params) or bool(self.kwparams)

    def add_param(self, name: str, var: Any):
        self.param_names[name] = var
        self.params.append(var)

    def add_kwparam(self, name: str, var: Any):
        self.kwparams[name] = var

    def add_args(self, args: Iterable[Any]):
        self.params.extend(args)
        self.has_args = True

    def add_kwargs(self, kwargs: Mapping[str, Any]):
        self.kwparams.update(kwargs)
        self.has_kwargs = True


class AbstractSemantics:
    def safe_context(self, /, *other: Mapping[str, Any]) -> Mapping[str, Any]:
        context: dict[str, Any] = {}
        for ctx in other:
            context |= ctx

        return {
            name: value
            for name, value in context.items()
            if callable(value) and not name.startswith('_')
        }


class ASTSemantics(AbstractSemantics):
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


class ModelBuilderSemantics(AbstractSemantics):
    """Intended as a semantic action for parsing, a ModelBuilderSemantics creates
    nodes using the class name given as first parameter to a grammar
    rule, and synthesizes the class/type if it's not known.
    """

    def __init__(
            self,
            context: ParseContext | None = None,
            base_type: type[Node] = Node,
            types: Iterable[Callable] | None = None):
        self.ctx = context
        self.base_type = base_type

        self.constructors: dict[str, Callable] = {}

        for t in types or ():
            if not callable(t):
                raise TypeError(f'Expected callable in types, got: {type(t)!r}')
            if not hasattr(t, '__name__'):
                raise TypeError(f'Expected __name__ in callable, got: {t!r}')
            # note: allow standalone functions
            self._register_constructor(t)

    def safe_context(self, /, *other: Mapping[str, Any]) -> Mapping[str, Any]:
        return super().safe_context(self.constructors, *other)

    def _register_constructor(self, constructor: Callable) -> Callable:
        if hasattr(constructor, '__name__') and isinstance(constructor.__name__, str):
            self.constructors[str(constructor.__name__)] = constructor
        return constructor

    def _find_existing_constructor(self, typename: str) -> Callable | None:
        context: Mapping[str, Any] = (
                self.constructors |
                vars(builtins) |
                registered_synthetics()
        )
        constructor = context.get(typename)
        if constructor is not None:
            return constructor

        for name in reversed(typename.split('.')[:-1]):
            if name not in context:
                break

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
            constructor = synthesize(typename, (base,))

        return self._register_constructor(constructor)

    def _find_actual_params(
            self,
            fun: Callable,
            ast: Any,
            args: Iterable[Any],
            kwargs: Mapping[str, Any],
    ) -> ActualParameters:
        fun_name = ''
        if hasattr(fun, '__name__'):
            fun_name = fun.__name__
        if fun_name and fun_name in vars(builtins):
            return ActualParameters(params=[ast])

        known_params = {
            'ast': ast,
            'ctx': self.ctx,
            'exp': ast,
            'kwargs': {},
        }
        actual = ActualParameters()
        declared = inspect.signature(fun).parameters

        for name, value in known_params.items():
            if name not in declared:
                continue
            param = declared[name]
            match param.kind:
                case inspect.Parameter.POSITIONAL_ONLY | inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    actual.add_param(name, value)
                case inspect.Parameter.KEYWORD_ONLY:
                    actual.add_kwparam(name, value)
                case _:
                    pass

        for param in declared.values():
            match param.kind:
                case inspect.Parameter.VAR_POSITIONAL:
                    actual.add_args(args)
                case inspect.Parameter.VAR_KEYWORD:
                    actual.add_kwargs(kwargs)
                case _:
                    pass

        # debug(
        #     f'CALLING {fun_name}'
        #     f'\nwith {tuple(actual.param_names)!r}'
        #     f'\nand {tuple(actual.kwparams)!r}',
        # )
        if not actual.has_any_params() and len(declared) == 1:
            actual.params = [ast]
        # else: No parameters
        return actual

    def _default(self, ast: Any, *args: Any, **kwargs: Any) -> Any:
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

        actual = self._find_actual_params(constructor, ast, args[1:], kwargs)
        return constructor(*actual.params, **actual.kwparams)

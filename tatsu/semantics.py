from __future__ import annotations

import builtins
import inspect
import keyword
import types
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any

from .objectmodel import Node
from .synth import synthesize
from .util import simplify_list
from .util.configs import Config
from .util.deprecation import deprecated_params
from .util.misc import least_upper_bound_type

__all__ = [
    'ASTSemantics',
    'ModelBuilderSemantics',
    'TypeContainer',
]

type Constructor = type | Callable
type TypeContainer = type | ModuleType | Mapping[str, Any]


class TypeResolutionError(TypeError):
    """Raised when a constructor for a node type cannot be found or synthesized"""
    pass


def types_defined_in(container: Any) -> list[type]:
    return AbstractSemantics.types_defined_in(container)


@dataclass
class BuilderConfig(Config):
    basetype: type = Node
    synthok: bool = True
    typedefs: list[TypeContainer] = field(default_factory=list)
    constructors: list[Constructor] = field(default_factory=list)


@dataclass
class ActualParameters:
    params: list[Any] = field(default_factory=list)
    param_names: dict[str, Any] = field(default_factory=dict)
    kwparams: dict[str, Any] = field(default_factory=dict)

    def has_any_params(self) -> bool:
        return bool(self.params) or bool(self.kwparams)

    def add_param(self, name: str, var: Any):
        self.param_names[name] = var
        self.params.append(var)

    def add_kwparam(self, name: str, var: Any):
        self.kwparams[name] = var

    def add_args(self, args: Iterable[Any]):
        self.params.extend(args)

    def add_kwargs(self, kwargs: Mapping[str, Any]):
        self.kwparams.update(kwargs)


class AbstractSemantics:
    def safe_context(self, /, *other: Mapping[str, Any]) -> Mapping[str, Any]:
        context: dict[str, Any] = {}
        for ctx in other:
            context |= ctx

        return {
            name: value
            for name, value in context.items()
            if callable(value)
        }

    @staticmethod
    def types_defined_in(container: Any) -> list[type]:
        contents: dict[str, Any] = {}
        if isinstance(container, types.ModuleType):
            contents.update(vars(container))
        elif isinstance(container, Mapping):
            contents.update(container)
        elif hasattr(container, '__dict__'):
            contents.update(vars(container))
        else:
            return []

        type_list = [t for t in contents.values() if isinstance(t, type)]
        name = (
            getattr(container, '__module__', None)
            or getattr(container, '__name__', None)
        )
        if name is None:
            return type_list
        return [t for t in type_list if t.__module__ == name]


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
    @deprecated_params(
        base_type='basetype',
        types='constructors',
        context=None,
    )
    def __init__(
            self,
            config: BuilderConfig | None = None,
            synthok: bool = True,
            basetype: type | None = None,
            typedefs: list[TypeContainer] | None = None,
            constructors: list[Constructor] | None = None,
            # deprecations
            context: Any | None = None,
            base_type: type | None = None,
            types: list[Callable] | None = None,  # for bw compatibility
    ) -> None:
        assert context is None
        config = BuilderConfig.new(
            config=config,
            basetype=basetype,
            synthok=synthok,
            typedefs=typedefs,
            constructors=constructors,
        )
        self._constructor_registry: dict[str, Constructor] = {}

        # handle deeprecations
        if isinstance(base_type, type):
            config = config.override(basetype=base_type)
        if types is not None:
            config = config.override(constructors=[*(config.constructors or []), *types])

        config = self._typedefs_to_constructors(config)
        config = self._narrow_basetype(config)
        self._register_constructors(config)

        self.config = config
        # HACK!
        self.config = self.config.override(synthok=not constructors)

    def _typedefs_to_constructors(self, config: BuilderConfig) -> BuilderConfig:
        if not config.typedefs:
            return config

        contained = []
        for container in config.typedefs:
            contained += self.types_defined_in(container)

        all_constructors = [*config.constructors, *contained]
        return config.override(constructors=all_constructors)

    def _narrow_basetype(self, config: BuilderConfig) -> BuilderConfig:
        if config.basetype and config.basetype is not object:
            return config
        basetype = least_upper_bound_type(config.constructors)
        return config.override(basetype=basetype)

    def _register_constructors(self, config: BuilderConfig) -> None:
        for t in config.constructors:
            if not callable(t):
                raise TypeResolutionError(f'Expected callable in constructors, got: {type(t)!r}')
            if not hasattr(t, '__name__'):
                raise TypeResolutionError(f'Expected __name__ in constructor, got: {type(t)!r}')

            # NOTE: this allows for standalone functions as constructors
            self._register_constructor(t)

    def safe_context(self, /, *other: Mapping[str, Any]) -> Mapping[str, Any]:
        return super().safe_context(self._constructor_registry, *other)

    def _register_constructor(self, constructor: Constructor) -> Constructor:
        name = getattr(constructor, '__name__', None)
        if not name:
            return constructor

        existing = self._constructor_registry.get(name)
        if existing and existing is not constructor:
            raise TypeResolutionError(
                f"Conflict for constructor name {name!r}: "
                f"attempted to register {constructor!r}, "
                f"but {existing!r} is already registered.",
            )

        self._constructor_registry[name] = constructor
        return constructor

    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-01-31)
    def _find_existing_constructor(self, typename: str) -> Constructor | None:
        return (
            self._constructor_registry.get(typename)
            or vars(builtins).get(typename)
        )

    def _get_constructor(self, typename: str, base: type) -> Constructor:
        constructor = self._find_existing_constructor(typename)
        if not constructor:
            synthok = bool(self.config.synthok)
            if synthok:
                constructor = synthesize(typename, (base,))
            else:
                raise TypeResolutionError(
                    f'Could not find constructor for type {typename!r}, and {synthok=} ',
                )
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

        basetype = self.config.basetype
        for base_ in bases:
            defined = self._get_constructor(base_, base=basetype)
            if isinstance(defined, type):
                basetype = defined

        constructor = self._get_constructor(typename, base=basetype)

        actual = self._find_actual_params(constructor, ast, args[1:], kwargs)
        return constructor(*actual.params, **actual.kwparams)

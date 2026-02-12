# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import builtins
import keyword
import types
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any

from .objectmodel import Node
from .synth import synthesize
from .util.configs import Config
from .util.deprecate import deprecated_params
from .util.misc import least_upper_bound_type
from .util.typing import boundcall

__all__ = [
    'BuilderConfig',
    'ModelBuilder',
    'ModelBuilderSemantics',
    'TypeContainer',
]


type Constructor = type | Callable
type TypeContainer = type | ModuleType | Mapping[str, type] | dict[str, type]


class TypeResolutionError(TypeError):
    """Raised when a constructor for a node type cannot be found or synthesized"""
    pass


def types_defined_in(container: TypeContainer) -> list[type]:
    return ModelBuilder.types_defined_in(container)


@dataclass
class BuilderConfig(Config):
    basetype: type = Node
    synthok: bool = True
    typedefs: list[TypeContainer] = field(default_factory=list)
    constructors: list[Constructor] = field(default_factory=list)


class ModelBuilder:
    """Intended as a semantic action for parsing. A ModelBuildercreates
    nodes using the class name given as first parameter to a grammar
    rule, and synthesizes the class/type if it's not known.
    """
    def __init__(
        self,
        config: BuilderConfig | None = None,
        synthok: bool = True,
        basetype: type | None = None,
        typedefs: list[TypeContainer] | None = None,
        constructors: list[Constructor] | None = None,
    ) -> None:

        config = BuilderConfig.new(
            config=config,
            basetype=basetype,
            synthok=synthok,
            typedefs=typedefs,
            constructors=constructors,
        )
        self._constructor_registry: dict[str, Constructor] = {}

        config = self._typedefs_to_constructors(config)
        config = self._narrow_basetype(config)
        self._register_constructors(config)

        self.config = config
        # HACK!
        self.config = self.config.override(synthok=not constructors)

    def instance(self, typename, known: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
        return self._instantiate(typename, known, *args, **kwargs)

    def _instantiate(
            self,
            typename: str,
            known: dict[str, Any],
            /,
            *args: Any,
            base: type | None = None,
            **kwargs: Any,
        ) -> Any:
        constructor = self._get_constructor(typename, base=base)
        return boundcall(constructor, known, *args, **kwargs)

    def safe_context(self, *other: Mapping[str, Any]) -> Mapping[str, Any]:
        context: dict[str, Any] = {}
        for ctx in other:
            context |= ctx

        return {
            name: value
            for name, value in context.items()
            if callable(value)
        }

    @staticmethod
    def types_defined_in(container: TypeContainer, /) -> list[type]:
        contents: dict[str, Any] = {}
        if isinstance(container, types.ModuleType):
            contents.update(vars(container))
        elif isinstance(container, Mapping):
            contents.update(container)  # ty:ignore[no-matching-overload]
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

    def _funname(self, obj: Any) -> str | None:
        name = getattr(obj, '__name__', None)
        if not name and callable(obj):
            name = type(obj).__name__
        return name

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

            name = self._funname(t)
            if not name:
                raise TypeResolutionError(f'Expected __name__ in constructor, got: {type(t)!r}')

            # NOTE: this allows for standalone functions as constructors
            self._register_constructor(t)

    def _register_constructor(self, constructor: Constructor) -> Constructor:
        name = self._funname(constructor)
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

    def _find_existing_constructor(self, typename: str) -> Constructor | None:
        return (
            self._constructor_registry.get(typename)
            or vars(builtins).get(typename)
        )

    def _get_constructor(self, typename: str, base: type | None, **args: Any) -> Constructor:
        if constructor := self._find_existing_constructor(typename):
            return constructor

        if not self.config.synthok:
            synthok = bool(self.config.synthok)
            raise TypeResolutionError(
                f'Could not find constructor for type {typename!r}, and {synthok=} ',
            )

        if base is None:
            constructor = synthesize(typename, (), **args)
        else:
            constructor = synthesize(typename, (base,), **args)

        return self._register_constructor(constructor)


class ModelBuilderSemantics:
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
        config = BuilderConfig.new(
            config=config,
            basetype=basetype,
            synthok=synthok,
            typedefs=typedefs,
            constructors=constructors,
        )
        # handle deeprecations
        assert context is None
        if isinstance(base_type, type):
            config = config.override(basetype=base_type)
        if types is not None:
            constructors = [*(config.constructors or []), *types]
            config = config.override(constructors=constructors)

        self.config = config
        self._builder = ModelBuilder(
            config=config,
            synthok=synthok,
            basetype=basetype,
            typedefs=typedefs,
            constructors=constructors,
        )

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
        basenames = reversed(typespec)

        base = self.config.basetype
        for basename in basenames:
            defined = self._builder._get_constructor(basename, base=base)
            if isinstance(defined, type):
                base = defined

        known = {
            'ast': ast,
            'exp': ast,
        }
        return self._builder._instantiate(typename, known, ast, *args, base=base, **kwargs)

from __future__ import annotations

import builtins
import inspect
import keyword
import types
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .objectmodel import Node
from .synth import registered_synthetics, synthesize
from .util import simplify_list
from .util.configurations import Config
from .util.deprecation import deprecated_params

__all__ = [
    'ASTSemantics',
    'ModelBuilderSemantics',
    'NodesModuleType',
]

type NodesModuleType = types.ModuleType


def node_subclasses_in(container: Any, *, nodebase: type[Node] = Node) -> list[type]:
    return AbstractSemantics.node_subclasses_in(container, nodebase=nodebase)


@dataclass
class BuilderConfig(Config):
    nodebase: type = Node
    nodedefs: NodesModuleType | None = None
    nosynth: bool = False
    constructors: Iterable[Callable] = field(default_factory=list)

    # def __getstate__(self) -> dict[str, Any]:
    #     # NOTE: ModuleType cannot be pickled
    #     state = self.asdict()
    #     state['nodedefs__'] = getattr(self.nodedefs, '__name__', None)
    #     del state['nodedefs']
    #     return state
    #
    # def __setstate__(self, state: dict[str, Any]) -> None:
    #     name = state.pop('nodedefs__', None)
    #     if name:
    #         state['nodedefs'] = importlib.import_module(name)
    #     for key, value in state.items():
    #         setattr(self, key, value)


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
            if callable(value) and not name.startswith('_')
        }

    @staticmethod
    def node_subclasses_in(container: Any, *, nodebase: type = Node) -> list[type]:
        contents: dict[str, Any] = {}
        if isinstance(container, types.ModuleType):
            contents.update(vars(container))
        elif isinstance(container, Mapping):
            contents.update(container)
        elif hasattr(container, '__dict__'):
            contents.update(vars(container))
        else:
            return []

        return [
            t for t in contents.values()
            if isinstance(t, type) and issubclass(t, nodebase)
        ]


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
    @deprecated_params(base_type='nodebase', types='constructors')
    def __init__(
            self,
            config: BuilderConfig | None = None,
            nodebase: type | None = None,
            base_type: type | None = None,
            nodedefs: NodesModuleType | None = None,
            nosynth: bool = False,
            constructors: Iterable[Callable] | None = None,
            types: Iterable[Callable] | None = None,  # for bw compatibility
    ) -> None:
        config = BuilderConfig.new(
            config,
            nodebase=nodebase,
            nodedefs=nodedefs,
            nosynth=nosynth,
            constructors=constructors,
        )
        if isinstance(base_type, type):
            config = config.replace(nodebase=base_type)
        if types is not None:
            config = config.replace(constructors=[*(config.constructors or []), *types])
        if config.nodedefs:
            config = config.replace(
                constructors=[
                    *(config.constructors or []),
                    *self.node_subclasses_in(
                        config.nodedefs,
                        nodebase=config.nodebase,
                    ),
                ],
            )

        self.config = config

        self._constructors: dict[str, Callable] = {}
        for t in config.constructors:
            if not callable(t):
                raise TypeError(f'Expected callable in types, got: {type(t)!r}')
            if not hasattr(t, '__name__'):
                raise TypeError(f'Expected __name__ in callable, got: {t!r}')
            # note: this allows for standalone functions as constructors
            self._register_constructor(t)

    def safe_context(self, /, *other: Mapping[str, Any]) -> Mapping[str, Any]:
        return super().safe_context(self._constructors, *other)

    def _register_constructor(self, constructor: Callable) -> Callable:
        if hasattr(constructor, '__name__') and isinstance(constructor.__name__, str):
            self._constructors[str(constructor.__name__)] = constructor
        return constructor

    def _find_existing_constructor(self, typename: str) -> Callable | None:
        context: Mapping[str, Any] = (
                self._constructors |
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

    def _get_constructor(self, typename: str, base: type) -> type | Callable:
        typename = str(typename)

        if typename in self._constructors:
            return self._constructors[typename]

        constructor = self._find_existing_constructor(typename)
        # FIXME
        # if not constructor and isinstance(base, type):
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

        nodebase: type = self.config.nodebase
        for base_ in bases:
            defined = self._get_constructor(base_, base=nodebase)
            if isinstance(defined, type):
                nodebase = defined

        constructor = self._get_constructor(typename, base=nodebase)

        actual = self._find_actual_params(constructor, ast, args[1:], kwargs)
        return constructor(*actual.params, **actual.kwparams)

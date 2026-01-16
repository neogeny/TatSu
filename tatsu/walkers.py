from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import contextmanager
from typing import Any, ClassVar, Concatenate, cast

from .ngmodel import nodeshell
from .objectmodel import Node
from .util import pythonize_name

type WalkerMethod = Callable[Concatenate[NodeWalker, Any, ...], Any]


class NodeWalkerMeta(type):
    def __new__(mcs, name, bases, dct):  # type: ignore
        cls = super().__new__(mcs, name, bases, dct)
        # note: a different cache for each subclass
        cls._walker_cache: dict[str, WalkerMethod | None] = {}  # type: ignore
        return cls


class NodeWalker(metaclass=NodeWalkerMeta):
    # note: this is shared among all instances of the same sublass of NodeWalker
    _walker_cache: ClassVar[dict[str, WalkerMethod | None]] = {}

    @property
    def walker_cache(self):
        return self._walker_cache

    def walk(self, node: Any, *args, **kwargs) -> Any:
        node = nodeshell(node)

        if isinstance(node, Mapping):
            actual2 = cast(Mapping[str, Any], node)
            return {
                name: self.walk(value, *args, **kwargs)
                for name, value in actual2.items()
            }

        if isinstance(node, list | tuple | set):
            return type(node)(
                self.walk(n, *args, **kwargs)
                for n in node
                if n != node
            )

        walker = self._find_walker(node)
        if callable(walker):
            return walker(self, node, *args, **kwargs)
        else:
            return node

    def walk_children(self, node: Any, *args, **kwargs) -> list[Any]:
        node = nodeshell(node)
        if not hasattr(node, 'children'):
            return []

        return [
            self.walk(child, *args, **kwargs)
            for child in node.children()
        ]

    # note: backwards compatibility
    _walk_children = walk_children

    def _find_walker(self, node: Any, prefix: str = 'walk_') -> WalkerMethod | None:
        node = nodeshell(node)

        def get_callable(acls: type, aname: str) -> WalkerMethod | None:
            result = getattr(acls, aname, None)
            return result if callable(result) else None

        cls = self.__class__
        node_cls = node.__class__
        node_cls_qualname = node_cls.__qualname__

        if walker := self._walker_cache.get(node_cls_qualname):
            return walker

        class_stack: list[type] = [node.__class__]
        while class_stack and not walker:
            node_cls = class_stack.pop()

            cammelcase_name = node_cls.__name__
            pythonic_name = pythonize_name(cammelcase_name)

            possible_walker_names = [
                cammelcase_name,
                '_' + pythonic_name,  # double underscore before name
                pythonic_name.lstrip('_'),  # single underscore before name
            ]
            for possible_name in possible_walker_names:
                name = prefix + possible_name
                if walker := get_callable(cls, name):
                    break
            else:
                # try to find a walker for any of the base classes
                bases: list[type] = [
                    b for b in node_cls.__bases__ if b not in class_stack
                ]
                class_stack = bases + class_stack

        walker = (
            walker or
            get_callable(cls, '_walk__default') or
            get_callable(cls, '_walk_default') or
            get_callable(cls, 'walk_default')
        )

        self._walker_cache[node_cls_qualname] = walker
        return walker


class PreOrderWalker(NodeWalker):
    def walk(self, node, *args, **kwargs):
        node = nodeshell(node)
        result = super().walk(node, *args, **kwargs)
        if result is not None:
            self.walk_children(node, *args, **kwargs)
        return result


class DepthFirstWalker(NodeWalker):
    def walk(self, node, *args, **kwargs):
        node = nodeshell(node)
        if isinstance(node, Node):
            children = [self.walk(c, *args, **kwargs) for c in node.children()]
            return super().walk(node, children, *args, **kwargs)
        elif isinstance(node, Mapping):
            return {n: self.walk(e, *args, **kwargs) for n, e in node.items()}
        elif isinstance(node, list | tuple):
            return [self.walk(e, *args, **kwargs) for e in iter(node)]
        else:
            return super().walk(node, [], *args, **kwargs)


class ContextWalker(NodeWalker):
    def __init__(self, initial_context):
        super().__init__()
        self._initial_context = initial_context
        self._context_stack = [initial_context]

    # abstract
    def get_node_context(self, node, *args, **kwargs):
        pass

    # abstract
    def enter_context(self, ctx):
        pass

    # abstract
    def leave_context(self, ctx):
        pass

    def push_context(self, ctx):
        self._context_stack.append(ctx)

    def pop_context(self):
        self._context_stack.pop()

    @property
    def initial_context(self):
        return self._initial_context

    @property
    def context(self):
        return self._context_stack[-1]

    @contextmanager
    def new_context(self, node, *args, **kwargs):
        node = nodeshell(node)
        ctx = self.get_node_context(node, *args, **kwargs)
        if ctx == self.context:
            yield ctx
        else:
            self.enter_context(ctx)
            try:
                self.push_context(ctx)
                try:
                    yield ctx
                finally:
                    self.pop_context()
            finally:
                self.leave_context(ctx)

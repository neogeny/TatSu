from __future__ import annotations

from collections.abc import Callable, Collection, Mapping
from contextlib import contextmanager
from typing import Any, ClassVar, cast

from .objectmodel import Node
from .util import debug, is_list, pythonize_name


class NodeWalkerMeta(type):
    def __new__(mcs, name, bases, dct):  # type: ignore
        cls = super().__new__(mcs, name, bases, dct)
        # note: a different cache for each subclass
        cls._walker_cache: dict[str, Any] = {}  # type: ignore
        return cls


class NodeWalker(metaclass=NodeWalkerMeta):
    # note: this is shared among all instances of the same sublass of NodeWalker
    _walker_cache: ClassVar[dict[str, Any]] = {}

    @property
    def walker_cache(self):
        return self._walker_cache

    def walk(self, node: Node | Collection[Node], *args, **kwargs) -> Any:
        if isinstance(node, list | tuple):
            actual1 = cast(tuple[Node] | list[Node], node)
            return [self.walk(n, *args, **kwargs) for n in actual1]

        if isinstance(node, Mapping):
            actual2 = cast(Mapping[str, Any], node)
            return {
                name: self.walk(value, *args, **kwargs)
                for name, value in actual2.items()
            }

        if isinstance(node, Node):
            walker = self._find_walker(node)
            if callable(walker):
                return walker(self, node, *args, **kwargs)
            else:
                debug(node.__class__.__qualname__, walker)
                return node
        else:
            return node

    def walk_children(self, node: Node, *args, **kwargs) -> list[Any]:
        if not isinstance(node, Node):
            return []

        return [
            self.walk(child, *args, **kwargs)
            for child in node.children()
        ]

    # note: backwards compatibility
    _walk_children = walk_children

    def _find_walker(self, node: Node, prefix='walk_') -> Callable | None:

        def get_callable(acls: type, name: str) -> Callable | None:
            result = getattr(acls, name, None)
            return result if callable(result) else None

        cls = self.__class__
        node_cls = node.__class__
        node_cls_qualname = node_cls.__qualname__

        if walker := self._walker_cache.get(node_cls_qualname):
            return walker

        class_stack: list[type] = [node.__class__]
        walker = None
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
        result = super().walk(node, *args, **kwargs)
        if result is not None:
            self.walk_children(node, *args, **kwargs)
        return result


class DepthFirstWalker(NodeWalker):
    def walk(self, node, *args, **kwargs):
        if isinstance(node, Node):
            children = [self.walk(c, *args, **kwargs) for c in node.children()]
            return super().walk(node, children, *args, **kwargs)
        elif isinstance(node, Mapping):
            return {n: self.walk(e, *args, **kwargs) for n, e in node.items()}
        elif is_list(node):
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
        return node

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

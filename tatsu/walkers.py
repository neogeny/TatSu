# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from typing import Any, ClassVar, Concatenate

from .util.deprecate import deprecated
from .util.string import pythonize_name

type WalkerMethod = Callable[Concatenate[NodeWalker, Any, ...], Any]


class NodeWalker:
    # note: this is shared among all instances of the same sublass of NodeWalker
    _walker_cache: ClassVar[dict[str, WalkerMethod | None]] = (
        {}
    )  # pyright: ignore[reportRedeclaration]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # note: a different cache for each subclass
        cls._walker_cache: dict[str, WalkerMethod | None] = {}

    @property
    def walker_cache(self):
        return self._walker_cache

    # CAVEAT:
    #  in general: do not override this mehod
    #  instead: define walk_xyz() methods
    def walk(self, node: Any, *args, **kwargs) -> Any:
        if isinstance(node, dict):
            return type(node)(
                {
                    name: self.walk(value, *args, **kwargs)
                    for name, value in node.items()
                    if value != node
                },
            )
        elif isinstance(node, list | tuple | set):
            return type(node)(self.walk(n, *args, **kwargs) for n in node if n != node)
        elif (walker := self._find_walker(node)) and callable(walker):
            return walker(
                self,
                node,
                *args,
                **kwargs,
            )  # walkers are unbound, define self
        else:
            return node

    def children_of(self, node: Any) -> Iterable[Any]:
        if not hasattr(node, 'children') or not callable(node.children):
            return ()
        return node.children()  # pyright: ignore[reportReturnType]

    def walk_children(self, node: Any, *args, **kwargs) -> tuple[Any, ...]:
        return tuple(
            self.walk(child, *args, **kwargs) for child in self.children_of(node)
        )

    # note: backwards compatibility
    _walk_children = walk_children

    def _find_walker(self, node: Any, prefix: str = 'walk_') -> WalkerMethod | None:

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
                # breadth first
                class_stack = [*bases, *class_stack]

        walker = (
            walker
            or get_callable(cls, '_walk__default')
            or get_callable(cls, '_walk_default')
            or get_callable(cls, 'walk__default')
            or get_callable(cls, 'walk_default')
        )

        self._walker_cache[node_cls_qualname] = walker
        return walker


class BreadthFirstWalker(NodeWalker):
    """
    A generator-based Breadth-First Search traversal.
    """

    def __init__(self) -> None:
        super().__init__()
        self.queue: deque[Any] | None = None

    # CAVEAT:
    #  in general: do not override this mehod
    #  instead: define walk_xyz() methods
    def walk(self, node: Any, *args, **kwargs) -> tuple[Any, ...]:
        """Flattens the bfs_walk generator into a tuple of results."""
        return tuple(self.iter_breadthfirst(node, *args, **kwargs))

    def iter_breadthfirst(self, node: Any, *args, **kwargs) -> Iterable[Any]:
        if self.queue is not None:
            raise RuntimeError(
                f'{type(self).__name__}.walk_breadthfirst() called recursively',
            )

        self.queue = deque([node])
        try:
            while self.queue:
                nd = self.queue.popleft()
                yield super().walk(nd, *args, **kwargs)
                self.queue.extend(self.children_of(nd))
        finally:
            self.queue = None

    def walk_children(self, node: Any, *args, **kwargs) -> Any:
        """
        An error during a BFS walk
        """
        raise RuntimeError(
            f'{type(self).__name__}.walk_children() is not allowed in BFS mode',
        )


# note: for backwars compatibility
@deprecated(replacement=BreadthFirstWalker)
class PreOrderWalker(BreadthFirstWalker):
    pass


class DepthFirstWalker(NodeWalker):
    # CAVEAT:
    #  In general, do not override this method...
    #  Define walk_xyz() methods instead.
    def walk(self, node, *args, **kwargs) -> tuple[Any, ...]:
        return tuple(self.iter_depthfirst(node, *args, **kwargs))

    def iter_depthfirst(self, node, *args, **kwargs) -> Iterable[Any]:
        yield super().walk(node, *args, **kwargs)
        for child in self.children_of(node):
            yield from self.iter_depthfirst(child)


class PostOrderDepthFirstWalker(NodeWalker):
    # CAVEAT:
    #  In general, do not override this method...
    #  Define walk_xyz() methods instead.
    def walk(self, node, *args, **kwargs) -> tuple[Any, ...]:
        return tuple(self.iter_postdepthfirst(node, *args, **kwargs))

    def iter_postdepthfirst(self, node, *args, **kwargs) -> Iterable[Any]:
        def iter_children() -> Iterable[Any]:
            for child in self.children_of(node):
                yield from self.iter_postdepthfirst(child)

        children = tuple(iter_children())
        yield super().walk(node, *args, children=children, **kwargs)


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

from __future__ import annotations

import re
from collections.abc import Mapping
from contextlib import contextmanager
from typing import Any

from .objectmodel import Node
from .util import is_list


class NodeWalkerMeta(type):
    def __new__(mcs, name, bases, dct):
        class_ = super().__new__(mcs, name, bases, dct)
        class_._walker_cache = {}
        return class_


class NodeWalker(metaclass=NodeWalkerMeta):
    def __init__(self):
        super().__init__()
        # copy the class attribute to avoid linter warnings
        self._walker_cache = type(
            self,
        )._walker_cache  # pylint: disable=no-member

    def walk(self, node: Node | list[Node], *args, **kwargs) -> Any:
        if isinstance(node, list | tuple):
            return [self.walk(n, *args, **kwargs) for n in node]

        if isinstance(node, Mapping):
            return {
                name: self.walk(value, *args, **kwargs)
                for name, value in node.items()
            }

        walker = self._find_walker(node)
        if callable(walker):
            return walker(self, node, *args, **kwargs)
        else:
            return node

    def walk_children(self, node: Node, *args, **kwargs):
        if not isinstance(node, Node):
            return []

        return [
            self.walk(child, *args, **kwargs)
            for child in node.children()
        ]

    # note: backwards compatibility
    _walk_children = walk_children

    def _find_walker(self, node: Node, prefix='walk_'):
        def pythonize_match(m):
            return '_' + m.group().lower()

        cls = self.__class__
        node_cls = node.__class__
        node_cls_qualname = node_cls.__qualname__

        if walker := self._walker_cache.get(node_cls_qualname):
            return walker

        node_classes = [node.__class__]
        while node_classes:
            node_cls = node_classes.pop(0)

            cammelcase_name = node_cls.__name__
            walker = getattr(cls, prefix + cammelcase_name, None)
            if callable(walker):
                break

            # walk__pythonic_name with double underscore after walk
            pythonic_name = re.sub(
                r'[A-Z]+', pythonize_match, node_cls.__name__,
            )
            if pythonic_name != cammelcase_name:
                walker = getattr(cls, prefix + pythonic_name, None)
                if callable(walker):
                    break

            # walk_pythonic_name with single underscore after prefix
            pythonic_name = pythonic_name.lstrip('_')
            if pythonic_name != cammelcase_name:
                walker = getattr(cls, prefix + pythonic_name, None)
                if callable(walker):
                    break

            for b in node_cls.__bases__:
                if b not in node_classes:
                    node_classes.append(b)
        else:
            walker = getattr(cls, '_walk_default', None)
            if walker is None:
                walker = getattr(
                    cls, 'walk_default', None,
                )  # backwards compatibility
            if not callable(walker):
                walker = None

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

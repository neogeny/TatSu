# -*- coding: utf-8 -*-
import collections
from contextlib import contextmanager

from tatsu.objectmodel import Node
from tatsu.util import is_list
from tatsu.util import re


class NodeWalker(object):
    def __new__(cls, *args, **kwargs):
        cls._walker_cache = {}
        return super(NodeWalker, cls).__new__(cls)

    def walk(self, node, *args, **kwargs):
        walker = self._find_walker(node)
        if callable(walker):
            return walker(node, *args, **kwargs)

    def _find_walker(self, node, prefix='walk_'):
        def pythonize_match(m):
            return '_' + m.group().lower()

        classid = id(node.__class__)

        if classid in self._walker_cache:
            return self._walker_cache[classid]

        classes = [node.__class__]
        while classes:
            cls = classes.pop(0)

            cammelcase_name = cls.__name__
            walker = getattr(self, prefix + cammelcase_name, None)
            if callable(walker):
                break

            # walk__pythonic_name with double underscore after walk
            pythonic_name = re.sub('[A-Z]+', pythonize_match, cls.__name__)
            if pythonic_name != cammelcase_name:
                walker = getattr(self, prefix + pythonic_name, None)
                if callable(walker):
                    break

            # walk_pythonic_name with single underscore after walk

            # pythonic_name = pythonic_name.lstrip('_')
            # if pythonic_name != cammelcase_name:
            #     walker = getattr(self, prefix + pythonic_name, None)
            #     if callable(walker):
            #         break

            for b in cls.__bases__:
                if b not in classes:
                    classes.append(b)
        else:
            walker = getattr(self, '_walk_default', None)
            if walker is None:
                walker = getattr(self, 'walk_default', None)  # backwars compatibility
            if not callable(walker):
                walker = None

        self._walker_cache[classid] = walker
        return walker


class PreOrderWalker(NodeWalker):
    def walk(self, node, *args, **kwargs):
        result = super(PreOrderWalker, self).walk(node, *args, **kwargs)
        if isinstance(node, Node):
            for child in node.children_list():
                self.walk(child)
        return result


class NodePreOrderWalker(NodeWalker):
    def walk_object(self, node, *args, **kwargs):
        return node

    def walk_node(self, node, *args, **kwargs):
        for child in node.children_list():
            self.walk(child)
        return node


class DepthFirstWalker(NodeWalker):
    def walk(self, node, *args, **kwargs):
        supers_walk = super(DepthFirstWalker, self).walk
        if isinstance(node, Node):
            children = [self.walk(c, *args, **kwargs) for c in node.children()]
            return supers_walk(node, children, *args, **kwargs)
        elif isinstance(node, collections.Mapping):
            return {n: self.walk(e, *args, **kwargs) for n, e in node.items()}
        elif is_list(node):
            return [self.walk(e, *args, **kwargs) for e in iter(node)]
        else:
            return supers_walk(node, [], *args, **kwargs)


class ContextWalker(NodeWalker):
    def __init__(self, initial_context):
        super(ContextWalker, self).__init__()
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

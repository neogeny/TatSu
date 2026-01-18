from __future__ import annotations

import weakref
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol, cast, overload, runtime_checkable

from ..ast import AST
from ..infos import ParseInfo
from ..tokenizing import CommentInfo
from ..util import AsJSONMixin, asjson, asjsons


@overload
def nodeshell[T: NGNode](node: T) -> NodeShell[T]: ...

@overload
def nodeshell[U](node: U) -> U: ...


def nodeshell(node: Any) -> Any:
    if isinstance(node, NGNode):
        return NodeShell.shell(node)
    return node


@overload
def unshell[U: NGNode](node: NodeShell[U]) -> U: ...

@overload
def unshell[T](node: T) -> T: ...


def unshell(node: Any) -> Any:
    if isinstance(node, NodeShell):
        return node.shelled()
    elif isinstance(node, list | tuple):
        return type(node)(unshell(elem) for elem in node)
    elif isinstance(node, dict):
        return type(node)(
            {name: unshell(value) for name, value in node.items()},
        )
    return node


@overload
def children_of(node: NGNode) -> tuple[NGNode, ...]: ...

@overload
def children_of[U](node: U) -> tuple[NodeBase, ...]: ...


def children_of(node: Any) -> tuple[Any, ...]:
    if isinstance(node, HasChildren):
        return tuple(node.children())
    elif isinstance(node, NGNode):
        return nodeshell(node).children()
    else:
        return ()


@runtime_checkable
class HasChildren(Protocol):
    def children(self) -> Iterable[Any]:
        ...


@dataclass
class NodeBase:
    ast: Any = None
    ctx: Any = None


@dataclass(unsafe_hash=True)
class NGNode(AsJSONMixin, NodeBase):
    _parseinfo: ParseInfo | None = field(init=False, default=None)
    _parent_ref: weakref.ref[NGNode] | None = field(init=False, default=None)

    def __post_init__(self):
        if self._parseinfo is None and isinstance(self.ast, AST):
            self._parseinfo = self.ast.parseinfo

    @property
    def parseinfo(self) -> Any:
        return self._parseinfo


class NodeShell[T: NGNode](AsJSONMixin, HasChildren):
    """
    Stateful View of a Node.
    Manages bi-directional navigation and metadata access.
    """
    # Multi-type cache: Maps Node types to their specific WeakKeyDictionaries
    _cache: ClassVar[weakref.WeakKeyDictionary[NGNode, NodeShell[Any]]] = weakref.WeakKeyDictionary()

    def __init__(self, node: T):
        self.node: T = node
        # Weak reference to parent Node to prevent reference cycles
        self._children: tuple[NodeShell[Any], ...] = ()

        self.__original_class__ = self.__class__

    @classmethod
    def shell(cls, node: T) -> NodeShell[T]:
        if not isinstance(node, NGNode):
            raise TypeError(f'<{type(node).__name__}> is not a Node')
        if isinstance(node, (weakref.ReferenceType, *weakref.ProxyTypes)):
            raise TypeError(f'<{type(node).__name__}> is a weak reference')
        try:
            if node not in cls._cache:
                cls._cache[node] = NodeShell(node)
            return cls._cache[node]
        except TypeError as e:
            raise TypeError(f'Problem with <{type(node).__name__}>: {e!s}') from e

    def shelled(self) -> NGNode:
        return self.node

    def __getattr__(self, name: str) -> Any:
        node = object.__getattribute__(self, 'node')
        try:
            return getattr(self.node, name)
        except AttributeError as e:
            raise AttributeError(
                f"'{type(self).__name__}' cannot find '{name}' in "
                f"NodeShell, node._attributes, or {type(node).__name__}",
            ) from e

    def __dir__(self) -> list[str]:
        return sorted(set(super().__dir__()) | set(dir(self.node)))

    @property
    def ast(self) -> Any:
        return self.node.ast

    @property
    def parseinfo(self) -> Any:
        return self.node._parseinfo

    @property
    def parent(self) -> NGNode | None:
        ref = self.node._parent_ref
        if ref is None:
            return None
        else:
            return ref()

    @property
    def path(self) -> tuple[NGNode, ...]:
        ancestors: list[NGNode] = []
        parent = self.parent
        while parent is not None:
            ancestors.append(parent)
            parent = nodeshell(parent).parent
        return tuple(reversed(ancestors))

    @property
    def comments(self) -> CommentInfo:
        if self.parseinfo and hasattr(self.parseinfo.tokenizer, 'comments'):
            comments = cast(Callable, self.parseinfo.tokenizer.comments)
            return comments(self.parseinfo.pos)
        return CommentInfo([], [])

    def children(self) -> tuple[Any, ...]:
        return self.children_tuple()

    def children_list(self) -> list[Any]:
        return list(self.children_tuple())

    def children_tuple(self) -> tuple[Any, ...]:
        return tuple(
            unshell(shell) for shell in self._children_shell_tuple()
        )

    def _children_shell_tuple(self) -> tuple[Any, ...]:
        if not self._children:
            self._children = tuple(self._get_children())
        return self._children

    def _get_children(self) -> Iterable[Any]:

        def walk(obj: Any) -> Iterable[NGNode]:
            match obj:
                case NodeShell() as shell:
                    yield from walk(shell.node)
                case NGNode() as node:
                    node._parent_ref = weakref.ref(self.node)
                    yield node
                case Mapping() as map:
                    for name, value in map.items():
                        if name.startswith("_"):
                            continue
                        if value is None:
                            continue
                        yield from walk(value)
                case (list() | tuple()) as seq:
                    for item in seq:
                        yield from walk(item)
                case _:
                    pass

        return tuple(walk(self.node._pubdict()))

    @property
    def text(self) -> str:
        pi = self.node._parseinfo
        if pi and hasattr(pi.tokenizer, "text"):
            return pi.tokenizer.text[pi.pos : pi.endpos]
        return ''

    @property
    def line(self) -> int | None:
        return self.node._parseinfo.line if self.node._parseinfo else None

    def asjson(self) -> Any:
        return asjson(self.node)

    def _pubdict(self) -> dict[str, Any]:
        return self.node._pubdict()

    def __json__(self, seen: set[int] | None = None) -> Any:
        return self.node.__json__(seen)

    def __str__(self) -> str:
        return asjsons(self)

    def __repr__(self) -> str:
        return f"nodeshell({super().__repr__()})"

    def __hash__(self) -> int:
        return self.node.__hash__()

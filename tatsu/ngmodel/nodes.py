from __future__ import annotations

import weakref
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar, cast, overload

from tatsu.util import AsJSONMixin, asjson, asjsons

from ..ast import AST
from ..infos import ParseInfo
from ..tokenizing import CommentInfo

BASE_CLASS_TOKEN = '::'  # noqa: S105


@overload
def nodeshell[T: Node](node: T) -> NodeShell[T]: ...

@overload
def nodeshell[T](node: T) -> T: ...


def nodeshell(node: Any) -> Any:
    if isinstance(node, Node):
        return NodeShell.shell(node)
    return node


@overload
def unwrap[T: Node](node: T) -> NodeShell[T]: ...

@overload
def unwrap[T](node: T) -> T: ...


def unwrap(node: Any) -> Any:
    if isinstance(node, NodeShell):
        return node.unwrap()
    elif isinstance(node, list | tuple):
        return type(node)(unwrap(elem) for elem in node)
    elif isinstance(node, dict):
        unwrapped = {name: unwrap(value) for name, value in node.items()}
        return type(node)(unwrapped)
    return node


@dataclass
class NodeBase:
    # NOTE: allows for compatibility with old Node
    def __init__(
            self,
            ast: Any = None,
            ctx: Any = None,
            parseinfo: ParseInfo | None = None,
            **attributes: Any,
    ):
        pass

    def _is_shell(self) -> bool:
        return False


@dataclass(unsafe_hash=True)
class Node(AsJSONMixin, NodeBase):
    """
    Pure data container.
    Stores the AST structure and attributes but remains unaware of its
    position within a larger tree to ensure easy serialization.
    """
    _ast: Any = None
    _ctx: Any = None
    _parseinfo: ParseInfo | None = None
    _attributes: dict[str, Any] = field(default_factory=dict, hash=False, compare=False)

    def __init__(
            self,
            ast: Any = None,
            ctx: Any = None,
            parseinfo: ParseInfo | None = None,
            **attributes: Any,
    ):
        super().__init__()
        self._ast = ast
        self._ctx = ctx
        self._parseinfo = parseinfo
        self._attributes = {}
        self._attributes.update(attributes)
        self.__post_init__()

    def __post_init__(self):
        if not self._parseinfo and isinstance(self._ast, AST):
            self._parseinfo = self._ast.parseinfo
        if isinstance(self._ast, Mapping):
            for name in set(self._ast) - {"parseinfo"}:
                self._attributes[name] = self._ast[name]

    def __getattr__(self, name: str) -> Any:
        if name in self._attributes:
            return self._attributes[name]
        raise AttributeError(
            f"'{type(self).__name__}' cannot find '{name}' in "
            f"NodeShell, node._attributes, or {type(self).__name__}",
        )

    def _pubdict(self) -> dict[str, Any]:
        return super()._pubdict() | self._attributes


class NodeShell[T: Node](AsJSONMixin):
    """
    Stateful View of a Node.
    Manages bi-directional navigation and metadata access.
    """
    # Multi-type cache: Maps Node types to their specific WeakKeyDictionaries
    _cache: ClassVar[weakref.WeakKeyDictionary[Node, NodeShell[Any]]] = weakref.WeakKeyDictionary()

    @classmethod
    def shell(cls, node: T) -> NodeShell[T]:
        if node not in cls._cache:
            cls._cache[node] = NodeShell(node)

        return cls._cache[node]

    def unwrap(self) -> Node:
        return self.node

    def _is_shell(self) -> bool:
        return True

    def __init__(self, node: T):
        self.node: T = node
        # Weak reference to parent Node to prevent reference cycles
        self._parent_ref: weakref.ref[Node] | None = None
        self._children: tuple[NodeShell[Any], ...] = ()

        self.__original_class__ = self.__class__

    def __getattr__(self, name: str) -> Any:
        node = object.__getattribute__(self, 'node')
        try:
            return getattr(node, name)
        except AttributeError:
            raise AttributeError(
                f"'{type(self).__name__}' cannot find '{name}' in "
                f"NodeShell, node._attributes, or {type(node).__name__}",
            ) from None

    def __dir__(self) -> list[str]:
        return sorted(set(super().__dir__()) | set(dir(self.node)) | set(self.node._attributes.keys()))

    @property
    def ast(self) -> Any:
        return self.node._ast

    @property
    def ctx(self) -> Any:
        return self.node._ctx

    @property
    def parseinfo(self) -> Any:
        return self.node._parseinfo

    @property
    def parent(self) -> NodeShell[Any] | None:
        """Resolves the weak parent reference and returns its NodeShell."""
        if self._parent_ref is None:
            return None
        parent_node = self._parent_ref()
        if parent_node is not None:
            return NodeShell.shell(parent_node)
        return None

    @property
    def path(self) -> list[NodeShell[Any]]:
        """Returns the list of ancestor shells from root down to this shell's parent."""
        ancestors: list[NodeShell[Any]] = []
        curr = self.parent
        while curr is not None:
            ancestors.append(curr)
            curr = curr.parent
        return ancestors[::-1]

    def children(self) -> tuple[Any, ...]:
        return self.children_tuple()

    def children_list(self) -> list[Any]:
        return list(self.children_tuple())

    def children_tuple(self) -> tuple[Any, ...]:
        return tuple(
            unwrap(shell) for shell in self._children_shell_tuple()
        )

    def _children_shell_tuple(self) -> tuple[NodeShell[Any], ...]:
        if not self._children:
            self._children = tuple(self._find_children_shells())
        return self._children

    def _find_children_shells(self) -> Iterable[NodeShell[Any]]:
        """Walks the AST data, yields shells, and sets parentage links."""
        def walk(obj: Any) -> Iterator[NodeShell[Any]]:
            match obj:
                case Node():
                    child_shell = NodeShell.shell(obj)
                    # Link child shell back to this node via weak reference
                    child_shell._parent_ref = weakref.ref(self.node)
                    yield child_shell
                case NodeShell() as shell:
                    yield from walk(shell.unwrap())
                case Mapping() as map:
                    for name, value in map.items():
                        if not name.startswith("_"):
                            yield from walk(value)
                case (list() | tuple()) as seq:
                    for item in seq:
                        yield from walk(item)
                case _:
                    pass  # only yield descendant of NodeBase

        source = self.node._attributes or self.node._ast
        yield from walk(source)

    @property
    def text(self) -> str:
        pi = self.node._parseinfo
        if pi and hasattr(pi.tokenizer, "text"):
            return pi.tokenizer.text[pi.pos : pi.endpos]
        return ''

    @property
    def line(self) -> int | None:
        return self.node._parseinfo.line if self.node._parseinfo else None

    @property
    def context(self) -> Any:
        return self.node._ctx

    @property
    def comments(self) -> CommentInfo:
        pi = self.node._parseinfo
        if pi and hasattr(pi.tokenizer, "comments"):
            return cast(Callable, pi.tokenizer.comments)(pi.pos)
        return CommentInfo([], [])

    def asjson(self) -> Any:
        return asjson(self)

    def _pubdict(self) -> dict[str, Any]:
        return super()._pubdict() | self.node._pubdict()

    def __str__(self) -> str:
        return asjsons(self)

    def __repr__(self) -> str:
        return f"nodeshell({self.node.__class__.__name__})"

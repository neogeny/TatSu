from __future__ import annotations

import weakref
from collections.abc import Callable, Iterator, Mapping
from dataclasses import InitVar, dataclass, field
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
    """
    Entry point to wrap a Node in its contextual Shell.
    If the input is not a Node, it is returned unchanged.
    """
    if isinstance(node, Node):
        return NodeShell.shell(node)
    return node


@dataclass
class NodeBase:
    pass


@dataclass(unsafe_hash=True)
class Node(AsJSONMixin, NodeBase):
    """
    Pure data container.
    Stores the AST structure and attributes but remains unaware of its
    position within a larger tree to ensure easy serialization.
    """
    ast: InitVar[Any] | None = None
    ctx: InitVar[Any] | None = None

    _ast: AST | Node | NodeBase | str | None = None
    _ctx: Any = None
    _parseinfo: ParseInfo | None = None
    _attributes: dict[str, Any] = field(default_factory=dict, hash=False, compare=False)

    def __post_init__(self, ast: Any, ctx: Any) -> None:  # type: ignore
        self._ast = ast
        self._ctx = ctx
        if isinstance(self._ast, dict):
            self._ast = AST(self._ast)
        if not self._parseinfo and isinstance(self._ast, AST):
            self._parseinfo = self._ast.parseinfo
        if isinstance(self._ast, Mapping):
            for name in set(self._ast) - {"parseinfo"}:
                self._attributes[name] = self._ast[name]


class NodeShell[T: Node]:
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

    def __init__(self, node: T):
        self.node: T = node
        # Weak reference to parent Node to prevent reference cycles
        self._parent_ref: weakref.ref[Node] | None = None
        self._children: list[NodeShell[Any]] = self.find_children()

    def __getattr__(self, name: str) -> Any:
        """Proxies to node attributes or dynamic AST data."""
        if name in self.node._attributes:
            return self.node._attributes[name]
        try:
            return getattr(self.node, name)
        except AttributeError:
            raise AttributeError(
                f"'{type(self).__name__}' cannot find '{name}' in "
                f"NodeShell, node._attributes, or {type(self.node).__name__}",
            ) from None

    def __dir__(self) -> list[str]:
        return sorted(set(super().__dir__()) | set(dir(self.node)) | set(self.node._attributes.keys()))

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

    def children(self) -> list[NodeShell[Any]]:
        """Lazy-loads and returns child NodeShells."""
        if self._children is None:
            self._children = list(self._find_children())
        return self._children

    def _find_children(self) -> Iterator[NodeShell[Any]]:
        """Walks the AST data, yields shells, and sets parentage links."""
        def walk(obj: Any) -> Iterator[NodeShell[Any]]:
            if isinstance(obj, Node):
                child_shell = NodeShell.shell(obj)
                # Link child shell back to this node via weak reference
                child_shell._parent_ref = weakref.ref(self.node)
                yield child_shell
            elif isinstance(obj, Mapping):
                for k, v in obj.items():
                    if not k.startswith("_"):
                        yield from walk(v)
            elif isinstance(obj, (list, tuple)):
                for item in obj:
                    yield from walk(item)

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
        return asjson(self.node)

    def __str__(self) -> str:
        return asjsons(self.node)

    def __repr__(self) -> str:
        return f"nodeshell({self.node.__class__.__name__})"

from __future__ import annotations

import weakref
from collections.abc import Callable, Iterator, Mapping
from dataclasses import InitVar, dataclass, field
from typing import Any, cast, overload

from tatsu.util import AsJSONMixin, asjson, asjsons

from ..ast import AST
from ..infos import ParseInfo
from ..tokenizing import CommentInfo, LineInfo

BASE_CLASS_TOKEN = '::'  # noqa: S105


@overload
def nodeshell[T: Node](node: T) -> NodeShell[T]: ...

@overload
def nodeshell[T](node: T) -> T: ...


def nodeshell(node: Any) -> Any:
    if isinstance(node, Node):
        return NodeShell.shell(node)
    else:
        return node


@dataclass()
class NodeBase:
    def __hash__(self) -> int:
        return id(self)


@dataclass(unsafe_hash=True)
class Node(AsJSONMixin, NodeBase):
    """
    Pure data container.
    All fields are private to ensure interaction only via NodeShell.
    """

    ast: InitVar[Any] | None = None
    ctx: InitVar[Any] | None = None

    _ast: AST | NodeBase | str | None = None
    _ctx: Any = None
    _parseinfo: ParseInfo | None = None
    _attributes: dict[str, Any] = field(default_factory=dict, hash=False, compare=False)

    def __post_init__(self, ast, ctx):
        self._ast = ast
        self._ctx = ctx
        if isinstance(self._ast, dict):
            self._ast = AST(self._ast)

        if not self._parseinfo and isinstance(self._ast, AST):
            self._parseinfo = self._ast.parseinfo

        if isinstance(self._ast, Mapping):
            for name in set(self._ast) - {"parseinfo"}:
                self._attributes[name] = self._ast[name]

    def __str__(self) -> str:
        return asjsons(self)

    # NOTE: --- Serialization ---
    #   Since we removed _parent and _children from Node,
    #   default pickling now works perfectly without custom __getstate__.


class NodeShell[T: Node](NodeBase):
    """
    The 'Stateful View' of a Node.
    Manages tree hierarchy and provides public access to private Node data.
    """

    _cache: weakref.WeakKeyDictionary[Node, NodeShell[Any]] = (
        weakref.WeakKeyDictionary()
    )

    @staticmethod
    def shell[U: Node](node: U) -> NodeShell[U] | NodeBase:
        if node not in NodeShell._cache:
            NodeShell._cache[node] = NodeShell(node)
        return NodeShell._cache[node]

    def __init__(self, node: T):
        self.node: T = node
        # Hierarchy state moved from Node to NodeShell
        self._parent: Node | None = None
        self._children: list[Node] | None = None

    def __getattr__(self, name: str) -> Any:
        """
        Proxies attribute access with the following priority:
        1. Explicit keys in node._attributes
        2. Normal attributes/methods on the node instance (for subclasses)
        """
        # 1. Check the dynamic attributes dictionary
        if name in self.node._attributes:
            return self.node._attributes[name]

        # 2. Check for real attributes on the Node instance itself
        # We use getattr() on self.node to find subclass fields
        try:
            return getattr(self.node, name)
        except AttributeError:
            raise AttributeError(
                f"'{type(self).__name__}' cannot find '{name}' in "
                f"NodeShell, node._attributes, or {type(self.node).__name__}",
            ) from None

    def __dir__(self) -> list[str]:
        """Combines Shell methods, Node attributes, and dynamic keys for introspection."""
        node_attrs = set(dir(self.node))
        dynamic_attrs = set(self.node._attributes.keys())
        shell_attrs = set(super().__dir__())
        return sorted(shell_attrs | node_attrs | dynamic_attrs)

    # --- Hierarchy & Navigation ---

    @property
    def parent(self) -> Node | None:
        return self._parent

    @property
    def context(self) -> Any:
        return self.node._ctx

    def children(self) -> list[Node]:
        """Lazy-loads children and establishes self as the source of their parentage."""
        if self._children is None:
            self._children = list(self._find_children())
        return self._children

    def _find_children(self) -> Iterator[Node]:
        def walk(obj: Any) -> Iterator[Node]:
            if isinstance(obj, Node):
                # We get the shell for the child to set its parent locally
                child_shell = NodeShell.shell(obj)
                child_shell._parent = self.node
                yield obj
            elif isinstance(obj, Mapping):
                for k, v in obj.items():
                    if not k.startswith("_"):
                        yield from walk(v)
            elif isinstance(obj, (list, tuple)):
                for item in obj:
                    yield from walk(item)

        source = self.node._attributes or self.node._ast
        yield from walk(source)

    # --- Metadata Accessors ---

    @property
    def text(self) -> str:
        pi = self.node._parseinfo
        if not pi or not hasattr(pi.tokenizer, "text"):
            return ""
        text: str = pi.tokenizer.text
        return text[pi.pos : pi.endpos]

    @property
    def line(self) -> int | None:
        return self.node._parseinfo.line if self.node._parseinfo else None

    @property
    def line_info(self) -> LineInfo | None:
        pi = self.node._parseinfo
        if pi:
            return pi.tokenizer.line_info(pi.pos)
        return None

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

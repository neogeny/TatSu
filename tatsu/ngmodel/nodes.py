from __future__ import annotations

import weakref
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, cast

from tatsu.util import AsJSONMixin, asjson, asjsons

from ..ast import AST
from ..infos import ParseInfo
from ..tokenizing import CommentInfo, LineInfo

# --- Module Level Entry Point ---


def shell[T: Node](node: T) -> NodeShell[T]:
    """Module-level entry point to get the logic shell for a node."""
    return NodeShell.shell(node)


@dataclass(unsafe_hash=True)
class Node(AsJSONMixin):
    """
    Pure data container.
    All fields are private to ensure interaction only via NodeShell.
    """

    _ast: AST | Node | str | None = None
    _ctx: Any = None
    _parseinfo: ParseInfo | None = None
    _attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
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



class NodeShell[T: Node]:
    """
    The 'Stateful View' of a Node.
    Manages tree hierarchy and provides public access to private Node data.
    """

    _cache: weakref.WeakKeyDictionary[Node, NodeShell[Any]] = (
        weakref.WeakKeyDictionary()
    )

    @staticmethod
    def shell[U: Node](node: U) -> NodeShell[U]:
        if node not in NodeShell._cache:
            NodeShell._cache[node] = NodeShell(node)
        return NodeShell._cache[node]

    def __init__(self, node: T):
        self.node: T = node
        # Hierarchy state moved from Node to NodeShell
        self._parent: Node | None = None
        self._children: list[Node] | None = None

    def __getattr__(self, name: str) -> Any:
        """Proxies access to the node's private _attributes."""
        try:
            return self.node._attributes[name]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' has no attribute '{name}'",
            ) from None

    def __dir__(self) -> list[str]:
        return sorted(set(super().__dir__()) | set(self.node._attributes.keys()))

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

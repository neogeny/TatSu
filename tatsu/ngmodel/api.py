from collections.abc import Iterable
from typing import Any, Protocol, overload, runtime_checkable

from ..tokenizing import CommentInfo
from .nodes import Node, NodeBase, NodeShell


@runtime_checkable
class HasChildren(Protocol):
    def children(self) -> Iterable[Any]:
        ...


@overload
def nodeshell[T: Node](node: T) -> NodeShell[T]: ...

@overload
def nodeshell[U](node: U) -> U: ...


def nodeshell(node: Any) -> Any:
    if isinstance(node, Node):
        return NodeShell.shell(node)
    return node


@overload
def children_of(node: Node) -> tuple[Node, ...]: ...

@overload
def children_of[U](node: U) -> tuple[NodeBase, ...]: ...


def children_of(node: Any) -> tuple[Any, ...]:
    if isinstance(node, HasChildren):
        return tuple(node.children())
    elif isinstance(node, Node):
        return nodeshell(node).children()
    else:
        return ()


@overload
def comments_for(node: Node) -> CommentInfo: ...

@overload
def comments_for[U](node: U) -> CommentInfo: ...


def comments_for(node: Any) -> CommentInfo:
    if isinstance(node, Node):
        return nodeshell(node).comments
    return CommentInfo([], [])

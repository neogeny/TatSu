from collections.abc import Iterable
from typing import Any, Protocol, overload, runtime_checkable

from .nodes import NGNode, NodeBase, NodeShell


@overload
def nodeshell[T: NGNode](node: T) -> NodeShell[T]: ...

@overload
def nodeshell[U](node: U) -> U: ...


def nodeshell(node: Any) -> Any:
    if isinstance(node, NGNode):
        return NodeShell.shell(node)
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

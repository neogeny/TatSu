from __future__ import annotations

import weakref
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol, overload, runtime_checkable

from tatsu.util import AsJSONMixin, asjson, asjsons, debug

from ..ast import AST
from ..infos import ParseInfo

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
def unshell[T: Node](node: T) -> NodeShell[T]: ...

@overload
def unshell[T](node: T) -> T: ...


def unshell(node: Any) -> Any:
    if isinstance(node, NodeShell):
        return node.unshell()
    elif isinstance(node, list | tuple):
        return type(node)(unshell(elem) for elem in node)
    elif isinstance(node, dict):
        return type(node)(
            {name: unshell(value) for name, value in node.items()},
        )
    return node


@runtime_checkable
class HasChildren(Protocol):
    def children(self) -> Iterable[Any]:
        ...


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

    def __hash__(self) -> int:
        return hash(asjsons(self))


@dataclass
class Node(AsJSONMixin, NodeBase):
    """
    Pure data container.
    Stores the AST structure and attributes but remains unaware of its
    position within a larger tree to ensure easy serialization.
    """
    _ast: Any = None
    _ctx: Any = None
    _parseinfo: ParseInfo | None = None
    _attributes: dict[str, Any] = field(default_factory=dict, compare=False)

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

        for name, value in attributes.items():
            if hasattr(self, name):
                setattr(self, name, value)
            else:
                self._attributes[name] = value

        self._attributes.update(attributes)
        self.__post_init__()

    def __post_init__(self):
        if not self._parseinfo and isinstance(self._ast, AST):
            self._parseinfo = self._ast.parseinfo
        if isinstance(self._ast, Mapping):
            for name in set(self._ast) - {"parseinfo"}:
                self._attributes[name] = self._ast[name]

    def __getattr__(self, name: str) -> Any:
        ast = self._ast
        if name == 'ast':
            return ast
        if name == 'asjson':
            return self._asjson_private
        if name in self.__dict__:
            return self.__dict__[name]
        if isinstance(ast, dict) and name in ast:
            return ast[name]
        if name in self._attributes:
            return self._attributes[name]
        raise AttributeError(
            f"'{type(self).__name__}' cannot find '{name}' in "
            f"self._ast or self._attributes",
        )

    def __getattribute__(self, name) -> Any:
        if name == 'symbol':
            raise AttributeError(name)
        return super().__getattribute__(name)

    def _asjson_private(self) -> Any:
        return asjson(self)

    def _pubdict(self) -> dict[str, Any]:
        result = super()._pubdict() | self._attributes
        if isinstance(self._ast, dict):
            result |= self._ast
        return result

    def __hash__(self) -> int:
        return hash(asjsons(self))


class NodeShell[T: Node](AsJSONMixin, HasChildren):
    """
    Stateful View of a Node.
    Manages bi-directional navigation and metadata access.
    """
    # Multi-type cache: Maps Node types to their specific WeakKeyDictionaries
    _cache: ClassVar[weakref.WeakKeyDictionary[Node, NodeShell[Any]]] = weakref.WeakKeyDictionary()

    @classmethod
    def shell(cls, node: T) -> NodeShell[T]:
        if not isinstance(node, Node):
            raise TypeError(f'<{type(node).__name__}> is not a Node')
        if isinstance(node, (weakref.ReferenceType, *weakref.ProxyTypes)):
            raise TypeError(f'<{type(node).__name__}> is a weak reference')
        try:
            if node not in cls._cache:
                cls._cache[node] = NodeShell(node)

            return cls._cache[node]
        except TypeError as e:
            raise TypeError(f'Problem with <{type(node).__name__}>: {e!s}') from e

    def unshell(self) -> Node:
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
        except AttributeError as e:
            raise AttributeError(
                f"'{type(self).__name__}' cannot find '{name}' in "
                f"NodeShell, node._attributes, or {type(node).__name__}",
            ) from e

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
    def attributes(self) -> dict[str, Any]:
        return self.node._attributes

    @property
    def parent(self) -> NodeShell[Any] | None:
        """Resolves the weak parent reference and returns its NodeShell."""
        if self._parent_ref is None:
            return None
        parent_node = self._parent_ref()
        if parent_node is not None:
            return nodeshell(parent_node)
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
            unshell(shell) for shell in self._children_shell_tuple()
        )

    def _children_shell_tuple(self) -> tuple[Any, ...]:
        if not self._children:
            self._children = tuple(self._find_children_shells())
        return self._children

    def _find_children_shells(self) -> Iterable[Any]:
        def walk(obj: Any) -> Iterator[NodeShell[Any]]:
            # no recursion
            match obj:
                case NodeShell() as shell:
                    yield from walk(shell.unshell())
                case Node() as node:
                    child_shell = nodeshell(node)
                    child_shell._parent_ref = weakref.ref(self.node)
                    yield child_shell
                case Mapping() as map:
                    for name, value in map.items():
                        if name.startswith("_"):
                            continue
                        if not name.startswith("_"):
                            yield from walk(value)
                case (list() | tuple()) as seq:
                    for item in seq:
                        yield from walk(item)
                case NodeBase() as node:
                    yield nodeshell(node)
                case _:
                    pass  # only yield descendant of NodeBase

        sources = [self.ast, self.attributes]
        debug('SOURCES', type(self).__name__, sources)
        yield from walk(sources)

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

    def asjson(self) -> Any:
        return asjson(self.node)

    def _pubdict(self) -> dict[str, Any]:
        return self.node._pubdict()

    def __json__(self, seen: set[int] | None = None) -> Any:
        return self.node.__json__(seen)

    def __str__(self) -> str:
        return asjsons(self)

    def __repr__(self) -> str:
        return f"nodeshell({self.node.__class__.__name__})"

    def __hash__(self) -> int:
        return self.node.__hash__()

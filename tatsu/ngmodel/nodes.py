from __future__ import annotations

import weakref
from collections.abc import Callable, Iterable, Mapping
from typing import Any, ClassVar, cast, overload

from ..ast import AST
from ..infos import ParseInfo
from ..tokenizing import CommentInfo
from ..util import AsJSONMixin, asjson, asjsons


def _hasattr(obj, name: str) -> bool:
    try:
        return name in vars(obj) or hasattr(obj, name)
    except TypeError:
        return False


@overload
def unshell[U: Node](node: NodeShell[U]) -> U: ...

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


class NodeBase(AsJSONMixin):
    # NOTE: declare at the class level in case __init__ is not called
    ast: Any = None
    ctx: Any = None

    def __init__(self, ast: Any = None, ctx: Any = None):
        self.ast: Any = ast
        self.ctx: Any = ctx

    def __hash__(self) -> int:
        def tweak(value: Any):
            if isinstance(value, list):
                return tuple(value)
            else:
                return value

        signature = (
            (name, tweak(value))
            for name, value in vars(self).items()
        )
        return hash(signature)


class Node(NodeBase):
    # NOTE: declare at the class level in case __init__ is not called
    parseinfo: ParseInfo | None = None

    _attributes: dict[str, Any] | None = None
    _parent_ref: weakref.ref[Node] | None = None

    def __init__(
            self,
            ast: Any = None,
            ctx: Any = None,
            parseinfo: ParseInfo | None = None,
            **kwargs: Any,
    ):
        super().__init__(ast=ast, ctx=ctx)
        self.parseinfo: ParseInfo | None = parseinfo
        self._attributes: dict[str, Any] = {}
        self._parent_ref: weakref.ref[Node] | None = None

        if not self.parseinfo and isinstance(self.ast, AST):
            self.parseinfo = self.ast.parseinfo

        # NOTE: objectmodel.Node sets self attributes from ast: AST
        allargs = ast | kwargs if isinstance(self.ast, AST) else kwargs
        for name, value in allargs.items():
            if _hasattr(self, name):
                setattr(self, name, value)
            else:
                self._attributes[name] = value

    # FIXME: declared here to ease transition from objectmodel
    @property
    def comments(self) -> CommentInfo:
        if self.parseinfo and hasattr(self.parseinfo.tokenizer, 'comments'):
            comments = cast(Callable, self.parseinfo.tokenizer.comments)
            return comments(self.parseinfo.pos)
        return CommentInfo([], [])

    def __getattr__(self, name: str) -> Any:
        # note: here only if normal attribute search failed
        try:
            assert isinstance(self._attributes, dict)
            return self._attributes[name]
        except KeyError as e:
            # NOTE: signals hasattr() and the likes that the name was not found
            raise AttributeError(
                f'"{name}" is not a valid attribute in {type(self).__name__}',
            ) from e

    def _nonrefdict(self) -> Mapping[str, Any]:
        return {
            name: value
            for name, value in vars(self).items()
            if (
                    name not in {'_parent', '_children'}
                    and type(value) not in {weakref.ReferenceType, weakref.ProxyTypes}
            )
        }

    # NOTE: pickling is important for parallel parsing
    def __getstate__(self) -> Any:
        return self._nonrefdict()

    def __setstate__(self, state):
        self.__dict__.update(state)


class NodeShell[T: Node](AsJSONMixin):
    """
    Stateful View of a Node.
    Manages bi-directional navigation and metadata access.
    """
    # Multi-type cache: Maps Node types to their specific WeakKeyDictionaries
    _cache: ClassVar[weakref.WeakKeyDictionary[Node, NodeShell[Any]]] = weakref.WeakKeyDictionary()

    def __init__(self, node: T):
        self.node: T = node
        # Weak reference to parent Node to prevent reference cycles
        self._children: tuple[NodeShell[Any], ...] = ()

        self.__original_class__ = self.__class__

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

    def shelled(self) -> Node:
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
        return self.node.parseinfo

    @property
    def parent(self) -> Node | None:
        ref = self.node._parent_ref
        if ref is None:
            return None
        else:
            return ref()

    @property
    def path(self) -> tuple[Node, ...]:
        ancestors: list[Node] = []
        parent = self.parent
        while parent is not None:
            ancestors.append(parent)
            parent = NodeShell.shell(parent).parent
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

        def walk(obj: Any) -> Iterable[Node]:
            match obj:
                case NodeShell() as shell:
                    yield from walk(shell.node)
                case Node() as node:
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
        pi = self.node.parseinfo
        if pi and hasattr(pi.tokenizer, "text"):
            return pi.tokenizer.text[pi.pos : pi.endpos]
        return ''

    @property
    def line(self) -> int | None:
        return self.node.parseinfo.line if self.node.parseinfo else None

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
        return hash(self.node) + 42

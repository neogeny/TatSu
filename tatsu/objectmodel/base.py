from __future__ import annotations

import inspect
import warnings
import weakref
from typing import Any

from ..ast import AST
from ..infos import ParseInfo
from ..util.asjson import AsJSONMixin, asjson, asjsons


class BaseNode(AsJSONMixin):
    # NOTE: declare at the class level in case __init__ is not called
    ast: Any = None
    parseinfo: ParseInfo | None = None
    __attributes: dict[str, Any] = {}  # noqa: RUF012

    def __init__(self, ast: Any = None, **kwargs: Any):
        super().__init__()
        self.ast: Any = ast
        self.parseinfo: ParseInfo | None = None
        self.__attributes: dict[str, Any] = {}

        if isinstance(ast, AST) and 'parseinfo' in ast:
            self.parseinfo = ast['parseinfo']

        allargs = ast | kwargs if isinstance(self.ast, AST) else kwargs
        self.__set_attributes(**allargs)

    def set_parseinfo(self, value: ParseInfo | None) -> None:
        self.parseinfo = value

    def asjson(self) -> Any:
        return asjson(self)

    def __set_attributes(self, **attrs) -> None:
        for name, value in attrs.items():
            if hasattr(self, name) and not inspect.ismethod(getattr(self, name)):
                setattr(self, name, value)
            else:
                if hasattr(self, name):
                    warnings.warn(
                        f'"{name}" in keyword arguments will shadow'
                        f' {type(self).__name__}.{name}',
                        stacklevel=2,
                    )
                self.__attributes[name] = value

    def __getattr__(self, name: str) -> Any:
        # note: here only if normal attribute search failed
        try:
            assert isinstance(self.__attributes, dict)
            return self.__attributes[name]
        except KeyError:
            return super().__getattribute__(name)

    def __str__(self) -> str:
        return asjsons(self)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"({', '.join(self._pubdict())})"
        )

    def __eq__(self, other) -> bool:
        # note: no use case for structural equality
        return id(self) == id(other)

    def __hash__(self) -> int:
        # note: no use case for structural equality
        return hash(id(self))

    def __getstate__(self) -> Any:
        return {
            name: value
            if not isinstance(
                value,
                (weakref.ReferenceType, *weakref.ProxyTypes),
            )
            else None
            for name, value in vars(self).items()
        }

    def __setstate__(self, state):
        self.__dict__.update(state)

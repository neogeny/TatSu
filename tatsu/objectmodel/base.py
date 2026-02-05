# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses
import functools
import inspect
import warnings
import weakref
from typing import Any

from ..ast import AST
from ..infos import ParseInfo
from ..util.asjson import AsJSONMixin, asjson, asjsons


@dataclasses.dataclass(
    # init=False,
    eq=False,
    repr=False,
    match_args=False,
    unsafe_hash=False,
    kw_only=True,
)
class BaseNode(AsJSONMixin):
    ast: Any = None
    ctx: Any = None
    parseinfo: ParseInfo | None = None

    def __init__(self, ast: Any = None, **attributes: Any):
        super().__init__()

        if isinstance(ast, dict):
            ast = AST(ast)
        self.ast = ast

        self.__set_attributes(**attributes)
        self.__post_init__()

    def __post_init__(self):
        ast = self.ast
        if not isinstance(ast, AST):
            return

        if not self.parseinfo:
            self.parseinfo = ast.parseinfo

        # note:
        #   Node objects are created by a model builer when invoked by he parser,
        #   which passes only the ast recovered when the object must be created.
        #   `
        #       point::Point = ... left:... right:... ;
        #   `
        #   Here the key,value pairs in the AST are injected into the corresponding
        #   attributes declared by the Node subclass. Synthetic classes
        #   override this to create the attributes.
        for name in ast.keys() - self.private_names:
            if hasattr(self, name):
                setattr(self, name, ast[name])

    def set_parseinfo(self, value: ParseInfo | None) -> None:
        self.parseinfo = value

    def asjson(self) -> Any:
        return asjson(self)

    def __init_dataclass(self):
        if not dataclasses.is_dataclass(type(self)):
            return

        for field in dataclasses.fields(type(self)):
            if hasattr(self, field.name):
                continue
            if field.default_factory is not dataclasses.MISSING:
                value = field.default_factory()
            elif field.default is not dataclasses.MISSING:
                value = field.default
            else:
                value = None
            setattr(self, field.name, value)

    def __set_attributes(self, **attrs) -> None:
        if not isinstance(attrs, dict):
            return

        for name, value in attrs.items():
            if not hasattr(self, name):
                continue
            if (prev := getattr(self, name, None)) and inspect.ismethod(prev):
                warnings.warn(
                    f'`{name}` in keyword arguments will shadow'
                    f' `{type(self).__name__}.{name}`',
                    stacklevel=2,
                )
            setattr(self, name, value)

    @functools.cached_property
    def private_names(self) -> set[str]:
        return {f.name for f in dataclasses.fields(BaseNode)}

    def __pubdict__(self) -> dict[str, Any]:
        unwanted = self.private_names

        if not isinstance(self.ast, AST):
            # ast may be all this object has
            unwanted -= {'ast'}

        return {
            name: value
            for name, value in super().__pubdict__().items()
            if name not in unwanted
        }

    def __str__(self) -> str:
        return asjsons(self)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"({', '.join(self.__pubdict__())})"
        )

    def __eq__(self, other) -> bool:
        # note: no use case for structural equality
        return other is self

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

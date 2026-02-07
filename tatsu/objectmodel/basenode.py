# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses
import functools
import inspect
import warnings
import weakref
from collections.abc import Callable
from typing import Any, overload

from ..ast import AST
from ..infos import ParseInfo
from ..util.asjson import AsJSONMixin, asjson, asjsons

__all__ = ['BaseNode', 'TatSuDataclassParams', 'tatsudataclass']


TatSuDataclassParams = dict(  # noqa: C408
    eq=False,
    repr=False,
    match_args=False,
    unsafe_hash=False,
    kw_only=True,
)


@overload
def tatsudataclass[T: type](cls: T) -> T: ...

@overload
def tatsudataclass[T: type](**params: Any) -> Callable[[T], T]: ...


def tatsudataclass[T: type](cls: T | None = None, **params: Any) -> T | Callable[[T], T]:
    # by Gemini (2026-02-07)
    # by [apalala@gmail.com](https://github.com/apalala)

    def decorator(target: T) -> T:
        allparams = {**TatSuDataclassParams, **params}
        return dataclasses.dataclass(**allparams)(target)

    # If cls is passed, it was used as @tatsudataclass with no arguments
    if cls is not None:
        return decorator(cls)

    return decorator


@tatsudataclass
class BaseNode(AsJSONMixin):
    ast: Any = None
    ctx: Any = None
    parseinfo: ParseInfo | None = None

    def __init__(self, ast: Any = None, **attributes: Any):
        # NOTE:
        #  A @datclass subclass may not call this,
        #  but __post_init__() should still be honored
        super().__init__()

        self.ast = ast
        self.__set_attributes(**attributes)
        self.__post_init__()

    def __post_init__(self):
        if self.ast and isinstance(self.ast, dict):
            self.ast = AST(self.ast)

        ast = self.ast
        if not isinstance(ast, AST):
            return

        if not self.parseinfo:
            self.parseinfo = ast.parseinfo

        # note:
        #   Node objects are created by a model builer when invoked by he parser,
        #   which passes only the ast recovered when the object was created.
        #   `
        #       point::Point = ... left:... right:... ;
        #   `
        #   Here the key,value pairs in the AST are injected into the corresponding
        #   attributes declared by the Node subclass. Synthetic classes
        #   override this to create the attributes.
        for name in ast.keys() - self.private_names:
            if not hasattr(self, name):
                continue
            setattr(self, name, ast[name])

    def set_parseinfo(self, value: ParseInfo | None) -> None:
        self.parseinfo = value

    def asjson(self) -> Any:
        return asjson(self)

    def __init_dataclass(self):
        if not dataclasses.is_dataclass(type(self)):
            return

        for field in dataclasses.fields(type(self)):  # pyright: ignore[reportArgumentType]
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
                continue  # this method is to support initialization of @dataclass
            if (prev := getattr(self, name, None)) and inspect.ismethod(prev):
                warnings.warn(
                    f'`{name}` in keyword arguments will shadow'
                    f' `{type(self).__name__}.{name}`',
                    stacklevel=2,
                )
            setattr(self, name, value)

    @functools.cached_property
    def private_names(self) -> set[str]:
        return (
            {'private_names'}
            | {f.name for f in dataclasses.fields(BaseNode)}  # pyright: ignore[reportArgumentType]
        )

    def __pubdict__(self) -> dict[str, Any]:
        unwanted = self.private_names

        if self.ast and not isinstance(self.ast, AST):
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
        attrs = ', '.join(
            f'{name}={value}'
            for name, value in self.__pubdict__().items()
        )
        return (
            f"{type(self).__name__}"
            f"({attrs})"
        )

    def __eq__(self, other) -> bool:
        # NOTE: No use case for structural equality
        return other is self

    def __hash__(self) -> int:
        # NOTE: No use case for structural equality
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

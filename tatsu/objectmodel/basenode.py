# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses
import inspect
import warnings
import weakref
from collections.abc import Callable
from functools import cache
from typing import Any, overload

from ..ast import AST
from ..infos import ParseInfo
from ..util.abctools import rowselect
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


def tatsudataclass[T: type](
    cls: T | None = None,
    **params: Any,
) -> T | Callable[[T], T]:
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
    ast: Any = dataclasses.field(kw_only=False, default=None)
    # _: dataclasses.KW_ONLY
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
        for name in ast:
            if not hasattr(self, name) or inspect.ismethod(getattr(self, name)):
                continue
            setattr(self, name, ast[name])

    def asjson(self) -> Any:
        return asjson(self)

    def __set_attributes(self, **attrs) -> None:
        if not isinstance(attrs, dict):
            return

        for name, value in attrs.items():
            if not hasattr(self, name):
                raise ValueError(f'Unknown argument {name}={value!r}')
            if inspect.ismethod(method := getattr(self, name)):
                raise TypeError(f'Overriding method {name}={method!r}')

            if (prev := getattr(self, name, None)) and inspect.ismethod(prev):
                warnings.warn(
                    f'`{name}` in keyword arguments will shadow'
                    f' `{type(self).__name__}.{name}`',
                    stacklevel=2,
                )
            setattr(self, name, value)

    @staticmethod
    @cache
    def _basenode_keys() -> frozenset[str]:
        # Gemini (2026-02-14)
        return frozenset(dir(BaseNode))

    def __pub__(self) -> dict[str, Any]:
        pub = super().__pub__()

        # Gemini (2026-02-14)
        wanted = pub.keys() - self._basenode_keys()
        if wanted or self.ast is None:
            pass
        elif not isinstance(self.ast, AST):
            wanted = {'ast'}  # self.ast may be all this object has

        return rowselect(wanted, pub)

    def __repr__(self) -> str:
        fieldindex = {
            f.name: i for i, f in enumerate(dataclasses.fields(self))  # type: ignore
        }

        def fieldorder(n) -> int:
            return fieldindex.get(n, len(fieldindex))

        pub = self.__pub__()
        sortedkeys = sorted(pub.keys(), key=fieldorder)
        attrs = ', '.join(
            f'{name}={pub[name]!r}' for name in sortedkeys if pub[name] is not None
        )
        return f'{type(self).__name__}({attrs})'

    def __str__(self) -> str:
        return asjsons(self)

    def __eq__(self, other) -> bool:
        # NOTE: No use case for structural equality
        return other is self

    def __hash__(self) -> int:
        # NOTE: No use case for structural equality
        return hash(id(self))

    def __getstate__(self) -> Any:
        return {
            name: (
                value
                if not isinstance(value, (weakref.ReferenceType, *weakref.ProxyTypes))
                else None
            )
            for name, value in vars(self).items()
        }

    def __setstate__(self, state):
        self.__dict__.update(state)

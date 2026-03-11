# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses as dc
import inspect
import warnings
from collections.abc import Callable
from functools import cache
from typing import Any, overload

from ..contexts.infos import ParseInfo
from ..util import AsJSONMixin, asjson, asjsons, rowselect, typename
from ..util.indent import fold

__all__ = ['BaseNode', 'NodeDataclassParams', 'nodedataclass']

NodeDataclassParams = dict(
    {},
    eq=False,
    repr=False,
    match_args=False,
    unsafe_hash=False,
    kw_only=True,
)


@overload
def nodedataclass[T: type](cls: T) -> T: ...


@overload
def nodedataclass[T: type](**params: Any) -> Callable[[T], T]: ...


def nodedataclass[T: type](
    cls: T | None = None,
    **params: Any,
) -> T | Callable[[T], T]:
    # by Gemini (2026-02-07)
    # by [apalala@gmail.com](https://github.com/apalala)

    def decorator(target: T) -> T:
        allparams = {**NodeDataclassParams, **params}
        return dc.dataclass(**allparams)(target)  # type: ignore

    # If cls is passed, it was used as @tatsudataclass with no arguments
    if cls is not None and not params:
        return decorator(cls)

    return decorator


@nodedataclass
class BaseNode(AsJSONMixin):
    ast: Any = dc.field(kw_only=False, default=None)
    ctx: Any = None
    parseinfo: ParseInfo | None = None

    def __init__(self, ast: Any = None, **attributes: Any):
        # NOTE:
        #  A @datclass subclass may not call this,
        #  but __post_init__() should still be honored
        super().__init__()

        self.ast = ast
        self.ctx = None
        self.parseinfo = None
        self.__set_attributes(**attributes)
        self.__post_init__()

    def __post_init__(self):

        ast = self.ast
        if not isinstance(ast, dict):
            return

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

    def __set_attributes(self, **attrs) -> None:
        if not isinstance(attrs, dict):
            return

        for name, value in attrs.items():
            if not hasattr(type(self), name):
                raise ValueError(f'Unknown argument {name}={value!r}')
            if inspect.isroutine(method := getattr(type(self), name)):
                raise TypeError(f'Overriding method {name}={method!r}')

            if (prev := getattr(self, name, None)) and inspect.ismethod(prev):
                warnings.warn(
                    f'`{name}` in keyword arguments will override'
                    f' `{typename(self)}.{name}`: {prev!r}',
                    stacklevel=2,
                )
            setattr(self, name, value)

    def asjson(self) -> Any:
        return asjson(self)

    def asjsons(self) -> str:
        return asjsons(self)

    @staticmethod
    @cache
    def _basenode_keys() -> frozenset[str]:
        # Gemini (2026-02-14)
        return frozenset(vars(BaseNode).keys())

    def __pub__(self, sunderok: bool = False) -> dict[str, Any]:
        pub = super().__pub__(sunderok=sunderok)
        if sunderok:
            return pub  # we're being called from __getstate__ not __repr__

        # Gemini (2026-02-14)
        wanted = pub.keys() - self._basenode_keys()
        if wanted or self.ast is None:
            pass
        elif not isinstance(self.ast, dict):
            wanted = {'ast'}  # self.ast may be all this object has

        return rowselect(wanted, pub)

    def __repr__(self) -> str:
        fieldindex = {f.name: i for i, f in enumerate(dc.fields(self))}  # type: ignore

        def fieldorder(n) -> int:
            return fieldindex.get(n, len(fieldindex))

        pub = self.__pub__()
        sortedkeys = sorted(pub.keys(), key=fieldorder)

        attr_repr_list = []
        values = {name: pub[name] for name in sortedkeys}
        for name, value in values.items():
            if value is None:
                continue

            line = fold(
                prefix=f"{name}=",
                value=value,
                amount=2,
                addlevels=2,
            )
            attr_repr_list += [line]

        return fold(
            prefix=f'{typename(self)}',
            value=tuple(attr_repr_list),
            reprs=False,
            amount=2,
        )

    def __str__(self) -> str:
        return super().__repr__()

    def __eq__(self, other) -> bool:
        # NOTE: No use case for structural equality
        return other is self

    def __hash__(self) -> int:
        # NOTE: No use case for structural equality
        return hash(id(self))

    def __getstate__(self) -> Any:
        return self.__pub__(sunderok=True)

    def __setstate__(self, state: dict[str, Any]) -> None:
        for name, value in state.items():
            setattr(self, name, value)

from __future__ import annotations

import dataclasses
from collections.abc import Generator, Mapping
from types import SimpleNamespace  # noqa: F401  # pyright: ignore[reportUnusedImport]
from typing import Any, Self

from ..util.abctools import isiter
from ..util.asjson import AsJSONMixin
from ..ztyle import Style


__from_json__class__: dict[str, type] = {}


class Object:
    pass


def dataclass_fields(
    cls: type,
) -> Generator[tuple[str, dataclasses.Field], None, None]:
    if not dataclasses.is_dataclass(cls):
        return
    for parent in cls.mro()[1:]:
        yield from dataclass_fields(parent)
    fields = dataclasses.fields(cls)
    yield from [(f.name, f) for f in fields]


class JSONBase(AsJSONMixin):
    def __init_subclass__(cls: type, **kwargs):
        __from_json__class__[cls.__name__] = cls

    @classmethod
    def __from_json__(cls: type[Self], data: Mapping[str, Any]) -> Self:
        if dataclasses.is_dataclass(cls):
            fieldmap: dict[str, dataclasses.Field] = dict(dataclass_fields(cls))
            initdata = {
                name: value
                for name, value in data.items()
                if (f := fieldmap.get(name)) and f.init
            }
            return cls(**initdata)  # type: ignore

        new = cls.__new__(cls)
        for name, value in data.items():
            if name == "__class__":
                continue
            try:
                setattr(new, name, value)
            except AttributeError:
                if hasattr(cls, name):
                    pass  # a read-only attribute
                else:
                    raise
        return new


def fromjson(obj: Any) -> Any:
    """
    Transform serialized JSON into a Python object.
    """

    def dfs(node: Any) -> Any:  # noqa: PLR0911
        def mapped() -> dict[str, Any]:
            map: dict = node
            return {
                name: dfs(value) for name, value in map.items() if name != "__class__"
            }

        def asobj() -> object:
            return SimpleNamespace(**mapped())
            # NOTE another, more complicated approach:
            # obj = Object()
            # for name, value in mapped().items():
            #     setattr(obj, name, value)
            # return obj

        match node:
            case str():
                if node.startswith(("\\e[", "f{")):
                    return Style.from_raw(node)
                return node
            case int() | float() | bool() | bytes() | bytearray() | complex():
                return node
            case Mapping() as map:
                typename = map.get("__class__", None)
                if not typename:
                    return mapped()
                if (cls := __from_json__class__.get(typename)) is not None:
                    assert issubclass(cls, JSONBase)
                    return cls.__from_json__(mapped())  # NOTE the raw contents
                return asobj()
            case list() | tuple() | set() as seq:
                return [dfs(e) for e in seq]
            case _ if isiter(node):
                return [dfs(e) for e in node]
            case _:
                return node

    return dfs(obj)

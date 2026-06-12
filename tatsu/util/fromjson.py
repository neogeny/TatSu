from __future__ import annotations

import dataclasses
from collections.abc import Generator, Mapping
from types import SimpleNamespace  # noqa: F401  # pyright: ignore[reportUnusedImport]
from typing import Any, Self

from ..util.abctools import isiter
from ..util.asjson import AsJSONMixin


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


@dataclasses.dataclass
class JSONBase(AsJSONMixin):
    @classmethod
    def __from_json__(cls, data: Mapping[str, Any]) -> Self:
        if dataclasses.is_dataclass(cls):
            fieldmap: dict[str, dataclasses.Field] = dict(dataclass_fields(cls))
            initdata = {
                name: value
                for name, value in data.items()
                if name in fieldmap and fieldmap[name].init
            }
            return cls(**initdata)

        new = cls.__new__(cls)
        for name, value in data.items():
            if name == "__class__":
                continue
            setattr(new, name, value)
        return new

    @classmethod
    def _init_dataclass(
        cls,
        new: object,
        fieldmap: dict[str, dataclasses.Field],
        data: Mapping[str, Any],
    ):
        if not dataclasses.is_dataclass(cls):
            return
        for fname, field in fieldmap.items():
            if field.default is not dataclasses.MISSING:
                setattr(new, fname, field.default)
            elif field.default_factory is not dataclasses.MISSING:
                setattr(new, fname, field.default_factory())
            # if fname in data:
            #     value = data[fname]
            #     # if value is None:
            #     #     continue
            #     setattr(new, fname, value)

    @classmethod
    def _init_dataclass2(cls, data: Mapping[str, Any]) -> None:
        if not dataclasses.is_dataclass(cls):
            return

        fieldmap: dict[str, dataclasses.Field] = dict(dataclass_fields(cls))
        _initdata = {
            name: value
            for name, value in data.items()
            if name in fieldmap and fieldmap[name].init
        }
        _args = tuple(
            value
            for name, value in data.items()
            if name in fieldmap and fieldmap[name].init and not fieldmap[name].kw_only
        )
        _kwargs = {
            name: value
            for name, value in data.items()
            if name in fieldmap and fieldmap[name].init and fieldmap[name].kw_only
        }
        _allkwargs = {
            name: value
            for name, value in data.items()
            if name in fieldmap and fieldmap[name].init
        }
        new = cls.__new__(cls)
        cls._init_dataclass(new, fieldmap, data)
        # new.__init__(**allkwargs)
        # new.__post_init__()  # pyright: ignore[reportAttributeAccessIssue]

    def __init_subclass__(cls: type, **kwargs):
        __from_json__class__[cls.__name__] = cls


def fromjson(obj: Any) -> Any:
    """
    Transform serialized JSON into a Python object.
    """

    def dfs(node: Any) -> Any:  # noqa: PLR0911
        if node is None or isinstance(node, int | float | str | bool):
            return node

        def mapped() -> dict[str, Any]:
            map: dict = node
            return {
                name: dfs(value) for name, value in map.items() if name != "__class__"
            }

        def asobj() -> object:
            # return SimpleNamespace(**mapped())
            obj = Object()
            for name, value in mapped().items():
                setattr(obj, name, value)
            return obj

        match node:
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

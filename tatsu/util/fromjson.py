from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import SimpleNamespace  # noqa: F401  # pyright: ignore[reportUnusedImport]
from typing import Any, Generator, Self

from tatsu.util.abctools import isiter
from tatsu.util.asjson import AsJSONMixin


__from_json__class__: dict[str, type] = {}


class Object:
    pass


class JSONBase(AsJSONMixin):
    @classmethod
    def __from_json__(cls, data: Mapping[str, Any]) -> Self:
        assert (typename := data.get("__class__")) and typename == cls.__name__

        def dataclass_fields(
            cls: type,
        ) -> Generator[tuple[str, dataclasses.Field], None, None]:
            if not dataclasses.is_dataclass(cls):
                return
            for parent in cls.mro()[1:]:
                yield from dataclass_fields(parent)
            fields = dataclasses.fields(cls)
            yield from [(f.name, f) for f in fields]

        fieldmap: dict[str, dataclasses.Field] = dict(dataclass_fields(cls))
        if dataclasses.is_dataclass(cls):
            args = tuple(
                fromjson(value)
                for name, value in data.items()
                if name in fieldmap
                and fieldmap[name].init
                and not fieldmap[name].kw_only
            )
            kwargs = {
                name: fromjson(value)
                for name, value in data.items()
                if name in fieldmap and fieldmap[name].init and fieldmap[name].kw_only
            }
            return cls(*args, **kwargs)

        new = cls.__new__(cls)
        for name, value in data.items():
            if name == "__class__":
                continue
            if not (hasattr(cls, name) or name in fieldmap):
                continue
            setattr(new, name, fromjson(value))

        if dataclasses.is_dataclass(cls):
            new.__post_init__()  # pyright: ignore[reportAttributeAccessIssue]

        return new

    def __init_subclass__(cls: type, **kwargs):
        super().__init_subclass__(**kwargs)
        __from_json__class__[cls.__name__] = cls


def fromjson(obj: Any) -> Any:
    """
    Transform serialized JSON into a Python object.
    """

    def dfs(node: Any) -> Any:  # noqa: PLR0911
        if node is None or isinstance(node, int | float | str | bool):
            return node

        def mapped() -> dict[str, Any]:
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
                    return cls.__from_json__(node)  # NOTE the raw contents
                return asobj()
            case list() | tuple() | set() as seq:
                return [dfs(e) for e in seq]
            case _ if isiter(node):
                return [dfs(e) for e in node]
            case _:
                return node

    return dfs(obj)

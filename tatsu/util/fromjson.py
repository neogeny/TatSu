from __future__ import annotations

from collections.abc import Mapping
from types import SimpleNamespace
from typing import Any

from tatsu.util.abctools import isiter


__from_json__class__: dict[str, type] = {}


class JSONBase:
    @classmethod
    def __from_json__(cls, data: dict[str, Any]) -> Self:
        new = cls.__new__(cls)

        for name, value in data.items():
            if not hasattr(cls, name):
                continue
            setattr(new, name, fromjson(value))

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

        match node:
            case Mapping() as map:
                if (
                    (typename := map.get("__class__", None))
                    and ((cls := __from_json__class__.get(typename)) is not None)
                    and issubclass(cls, JSONBase)
                ):
                    # NOTE pass the raw contents
                    return cls.__from_json__(node)
                return SimpleNamespace(
                    **{
                        name: dfs(value)
                        for name, value in map.items()
                        if name != "__class__"
                    }
                )
            case list() | tuple() | set() as seq:
                return [dfs(e) for e in seq]
            case _ if isiter(node):
                return [dfs(e) for e in node]
            case _:
                return node

    return dfs(obj)

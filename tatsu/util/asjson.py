from __future__ import annotations

import enum
import json
import weakref
from collections.abc import Mapping
from typing import Any

from tatsu.util import debug, is_namedtuple, isiter


class AsJSONMixin:
    def __json__(self, seen: set[int] | None = None) -> Any:
        return {
            '__class__': type(self).__name__,
            **asjson(self._pubdict(), seen=seen),
        }

    def _pubdict(self) -> dict[str, Any]:
        return {
            name: value
            for name, value in vars(self).items()
            if not name.startswith('_')
        }


def asjson(obj, seen: set[int] | None = None) -> Any:  # noqa: PLR0911, PLR0912
    if obj is None or isinstance(obj, int | float | str | bool):
        return obj

    if seen is None:
        seen = set()
    elif id(obj) in seen:
        return f'{type(obj).__name__}@{id(obj)}'

    if isinstance(obj, Mapping | AsJSONMixin) or isiter(obj):
        seen.add(id(obj))

    try:
        if isinstance(obj, weakref.ReferenceType | weakref.ProxyType):
            return f'{obj.__class__.__name__}@0x{hex(id(obj)).upper()[2:]}'
        elif hasattr(obj, '__json__'):
            return obj.__json__(seen=seen)
        elif is_namedtuple(obj):
            return asjson(obj._asdict(), seen=seen)
        elif isinstance(obj, Mapping):
            result = {}
            for k, v in obj.items():
                try:
                    result[k] = asjson(v, seen=seen)
                except TypeError:
                    debug('Unhashable key?', type(k), str(k))
                    raise
            return result
        elif isiter(obj):
            return [asjson(e, seen=seen) for e in obj]
        elif isinstance(obj, enum.Enum):
            return asjson(obj.value)
        else:
            return repr(obj)
    finally:
        # NOTE: id()s may be reused
        #   https://docs.python.org/3/library/functions.html#id
        seen -= {id(obj)}


def plainjson(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {
            name: plainjson(value)
            for name, value in obj.items()
            if name not in {'__class__', 'parseinfo'}
        }
    elif isinstance(obj, weakref.ReferenceType | weakref.ProxyType):
        return '@ref'
    elif isinstance(obj, str) and obj.startswith('@'):
        return '@ref'
    elif isiter(obj):
        return [plainjson(e) for e in obj]
    else:
        return obj


class FallbackJSONEncoder(json.JSONEncoder):
    """A JSON Encoder that falls back to repr() for non-JSON-aware objects."""

    def default(self, o: Any) -> str:
        return repr(o)


def asjsons(obj: Any) -> str:
    return json.dumps(asjson(obj), indent=2, cls=FallbackJSONEncoder)

# NOTE: from https://github.com/LuminosoInsight/ordered-set/blob/master/ordered_set.py
import itertools
from typing import (
    Any,
    Iterable,
    Iterator,
    Mapping,
    MutableSet,
    Optional,
    Sequence,
    MutableSequence,
    Set,
    TypeVar,
)

T = TypeVar("T")


class OrderedSet(MutableSet[T], Sequence[T]):
    def __init__(self, iterable: Optional[Iterable[T]] = None):
        if iterable is not None:
            self._map = dict.fromkeys(iterable)
        else:
            self._map = {}
        self._list_cache: Optional[Sequence[T]] = None

    def __len__(self):
        return len(self._map)

    def __getitem__(self, i):
        if self._list_cache is None:
            self._list_cache = list(self._map.keys())
        return self._list_cache[i]

    def copy(self) -> "OrderedSet[T]":
        return self.__class__(self)

    def __getstate__(self):
        if len(self) == 0:
            return (None,)
        else:
            return list(self)

    def __setstate__(self, state):
        if state == (None,):
            self.__init__([])
        else:
            self.__init__(state)

    def __contains__(self, key: Any) -> bool:
        return key in self._map

    def add(self, value: T):  # pylint: disable=W0221
        self._map[value] = len(self._map)
        self._list_cache = None

    def update(self, sequence: Iterable[T]):
        self._map.update(dict.fromkeys(sequence))
        self._list_cache = None

    def pop(self) -> T:
        key = next(iter(self._map.keys()))
        self._map.pop(key)
        self._list_cache = None
        return key

    def discard(self, value: T):  # pylint: disable=W0221
        self._map.pop(value, None)
        self._list_cache = None

    def clear(self):
        self._map = {}
        self._list_cache = None

    def __iter__(self) -> Iterator[T]:
        return iter(self._map.keys())

    def __repr__(self) -> str:
        return "{%s}" % ', '.join(repr(e) for e in self)

    def __eq__(self, other: Any) -> bool:
        return all(item in other for item in self)

    def union(self, *other: Iterable[T]) -> "OrderedSet[T]":
        # do not split `str`
        outer = tuple(
            [o] if not isinstance(o, (Set, Mapping, MutableSequence)) else o
            for o in other
        )
        inner = itertools.chain([self], *outer)  # type: ignore
        items = itertools.chain.from_iterable(inner)  # type: ignore
        return type(self)(itertools.chain(items))

    def __and__(self, other: Iterable[Iterable[T]]) -> "OrderedSet[T]":
        return self.intersection(other)

    def intersection(self, *other: Iterable[Iterable[T]]) -> "OrderedSet[T]":
        common = set.intersection(*other)  # type: ignore
        items = (item for item in self if item in common)
        return type(self)(items)

    def difference(self, *other: Iterable[T]) -> "OrderedSet[T]":
        other = set.union(*other)  # type: ignore
        items = (item for item in self if item not in other)
        return type(self)(items)

    def issubset(self, other: Set[T]) -> bool:
        return all(item in other for item in self)

    def issuperset(self, other: Set[T]) -> bool:
        if len(self) < len(other):  # Fast check for obvious cases
            return False
        return all(item in self for item in other)

    def symmetric_difference(self, other: Set[T]) -> "OrderedSet[T]":
        cls = type(self)
        diff1 = cls(self).difference(other)
        diff2 = cls(other).difference(self)
        return cls().union(diff1, diff2)

    def difference_update(self, *other: Iterable[T]):
        self._map = dict.fromkeys(self.difference(*other))

    def intersection_update(self, *other: Iterable[Iterable[T]]):
        self._map = dict.fromkeys(self.intersection(*other))

    def symmetric_difference_update(self, *other: Iterable[T]):
        self._map = dict.fromkeys(self.difference(*other))

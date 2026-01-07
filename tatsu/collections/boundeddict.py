from typing import Any, Generic, TypeVar

KT = TypeVar("KT")  # Key Type
VT = TypeVar("VT")  # Value Type


class BoundedDict(dict[KT, VT], Generic[KT, VT]):
    def __init__(self, capacity: int, *args: Any, **kwargs: Any) -> None:
        self.capacity: int = capacity
        super().__init__(*args, **kwargs)

    def __setitem__(self, key: KT, value: VT) -> None:
        # If the key exists, delete it first to update its position
        # to "most recent" (standard LRU/Bounded behavior)
        if key in self:
            del self[key]

        super().__setitem__(key, value)
        self._enforce_limit()

    # The base update() doesn't always call __setitem__,
    # so we override it to ensure limits are respected.
    def update(self, e: Any = None, /, **f: VT):
        super().update(e, **f)
        self._enforce_limit()

    def _enforce_limit(self):
        while len(self) > self.capacity:
            # iter(self) returns keys in insertion order.
            # next() gets the first (oldest) key.
            oldest_key = next(iter(self))
            del self[oldest_key]

    def __repr__(self) -> str:
        return f"{super().__repr__()}[{self.capacity}]"

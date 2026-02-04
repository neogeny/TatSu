# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from typing import Any


class BoundedDict[KT, VT](dict[KT, VT]):
    def __init__(self, capacity: int, *args: Any, **kwargs: Any) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity: int = capacity
        super().__init__(*args, **kwargs)
        self._enforce_limit()

    def __setitem__(self, key: Any, value: Any) -> None:
        # If the key exists, delete it first to update its position
        # to "most recent" (standard LRU/Bounded behavior)
        if key in self:
            del self[key]

        super().__setitem__(key, value)
        self._enforce_limit()

    # The base update() doesn't always call __setitem__,
    # so we override it to ensure limits are respected.
    def update(self, *args, **kwargs) -> None:
        """
        Use dict.update(), then reinsert keys so ordering and eviction
        behave consistently with self.__setitem__.
        """

        # Fast C-level update
        super().update(*args, **kwargs)

        #   Reinsert keys so self.__setitem__ semantics are applied
        incoming: dict[Any, Any] = dict(*args, **kwargs)
        for k, v in incoming.items():
            super().__delitem__(k)  # the above call to update() ensures k exists
            super().__setitem__(k, v)

        self._enforce_limit()

    def _enforce_limit(self):
        while len(self) > self.capacity:
            oldest_key = next(iter(self))
            del self[oldest_key]

    def __repr__(self) -> str:
        return f"{super().__repr__()}[{len(self)}/{self.capacity}]"

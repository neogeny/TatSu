# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from ..util.deprecation import deprecated
from .boundeddict import BoundedDict


# WARNING: this is broken
@deprecated
class LRUBoundedDict[K, V](BoundedDict[K, V]):
    def __getitem__(self, key: K) -> V:
        value = super().__getitem__(key)
        self.__setitem__(key, value)
        return value

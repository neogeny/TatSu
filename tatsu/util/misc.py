# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import shutil
import time
import uuid

from .itertools import first  # noqa  # pyright: ignore[reportUnusedImport]


def platform_has_command(name) -> bool:
    # noinspection PyDeprecation
    return shutil.which(name) is not None


def clock_time_ns() -> int:
    # WARNING Time is a crucial concept when dealing with concurrency
    # WARNING and wanting to calculate elapsed time accurately.
    return time.clock_gettime_ns(time.CLOCK_REALTIME)


def new_uuid_hex() -> str:
    return uuid.uuid4().hex

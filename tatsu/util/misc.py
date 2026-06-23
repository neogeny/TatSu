# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import shutil
import string
import time

from .itertools import first  # noqa  # pyright: ignore[reportUnusedImport]


ALPHABET = string.digits + string.ascii_uppercase
GREEKTOME = "αβδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
GREEKtome = "αβδεζηθικλμνξοπρστυφχψω"


def platform_has_command(name) -> bool:
    # noinspection PyDeprecation
    return shutil.which(name) is not None


def clock_time_μs() -> int:
    # WARNING Time is a crucial concept when dealing with concurrency
    # WARNING and wanting to calculate elapsed time accurately.
    return time.clock_gettime_ns(time.CLOCK_REALTIME) // 1000


def i2alpha(value: int, width: int = 1, alphabet: str = ALPHABET):
    if value == 0:
        return alphabet[0] * width

    n = len(alphabet)

    def gen(value: int):
        while value != 0:
            value, c = divmod(value, n)
            yield alphabet[c]

    result = "".join(reversed(list(gen(value))))
    return result.rjust(width, alphabet[0])


def i2greek(value: int, width: int = 1):
    return i2alpha(value, width, GREEKTOME)


def new_id() -> str:
    d = 8
    t = time.monotonic_ns()
    _mm, mn = divmod(t, 10**d)
    return i2alpha(mn, width=d, alphabet=GREEKtome)

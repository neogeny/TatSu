# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import hashlib
import os
import shutil
import string
import time
from typing import Any

from .itertools import first  # noqa  # pyright: ignore[reportUnusedImport]


ALPHABET = string.digits + string.ascii_uppercase
GREEKTOME = "αβδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
GREEKtome = "αβδεζηθικλμνξοπρστυφχψω"


def is_main_process() -> bool:
    import multiprocessing

    return multiprocessing.parent_process() is None


MAIN_PID = os.getpid()


def check_pid() -> bool:
    return os.getpid() == MAIN_PID


def platform_has_command(name) -> bool:
    # noinspection PyDeprecation
    return shutil.which(name) is not None


def clock_time_μs() -> int:
    # WARNING Time is a crucial concept when dealing with concurrency
    # WARNING and wanting to calculate elapsed time accurately.
    return time.clock_gettime_ns(time.CLOCK_REALTIME) // 1000


def ascii2greek(value: str) -> str:
    a = string.ascii_lowercase
    m = max(len(a), len(GREEKTOME))
    g = (GREEKTOME * 2)[:m]

    return value.translate(str.maketrans(a, g, string.punctuation + string.whitespace))


def greek2ascii(value: str) -> str:
    a = string.ascii_lowercase
    g = GREEKTOME
    return value.translate(str.maketrans(g, a * 2))


def i2alpha(value: int, width: int = 1, alphabet: str = ALPHABET):
    value = int(value)
    width = int(width)
    alphabet = str(alphabet)

    if value == 0:
        return alphabet[0] * width

    n = len(alphabet)

    def gen(value: int):
        while value != 0:
            value, c = divmod(value, n)
            yield alphabet[c]

    result = "".join(reversed(list(gen(value))))
    return result.rjust(width, alphabet[0])


def i2Greek(value: int, width: int = 1):
    return i2alpha(value, width, GREEKTOME)


def i2greek(value: int, width: int = 1):
    return i2alpha(value, width, GREEKtome)


def greek_time() -> str:
    return i2greek(int(time.time()), width=8)


def alpha_timestamp() -> str:
    t = time.time()
    y, d = divmod(t, 24 * 3600)
    h, s = divmod(d, 3600)
    m, _ = divmod(s, 0.36)
    return f"{i2alpha(int(y), alphabet=string.ascii_lowercase)}-{h:02.0f}-{m:04.0f}"


def lower_time() -> str:
    return i2alpha(int(time.time()), width=8, alphabet=string.ascii_lowercase)


def new_id() -> str:
    d = 8
    t = time.monotonic_ns()
    _mm, mn = divmod(t, 10**d)
    return i2greek(mn, width=d)


def hash_2byte(data: Any) -> bytes:
    if data is None:
        return b"\x00\x00"
    return hashlib.blake2b(str(data).encode("utf-8"), digest_size=2).digest()


def hash_2str(data: Any) -> str:
    return hex(int.from_bytes(hash_2byte(data), "big"))

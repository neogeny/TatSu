# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from itertools import starmap
from typing import NamedTuple


class LineInfo(NamedTuple):
    filename: str
    line: int
    col: int
    start: int
    end: int
    text: str


class LineIndexInfo(NamedTuple):
    filename: str
    line: int

    @staticmethod
    def block_index(name, n) -> list[LineIndexInfo]:
        return list(starmap(LineIndexInfo, zip(n * [name], range(n), strict=False)))


class PosLine(NamedTuple):
    start: int
    line: int
    length: int

    @staticmethod
    def build_line_cache(lines, size):
        # an index from original positions to PosLine entries
        if not lines:
            return [], 1

        cache = []
        n = 0
        i = 0
        for n, line in enumerate(lines):
            pl = PosLine(i, n, len(line))
            for _ in line:
                cache.append(pl)  # noqa: PERF401
            i += len(line)

        n += 1
        if lines[-1][-1] in {'\r', '\n'}:
            n += 1
        cache.append(PosLine(i, n, 0))

        # the range depends on line[-1] ending in a newline
        endrange = range(len(lines), 2 + len(lines))
        assert n in endrange
        assert len(cache) == 1 + size

        return cache, n

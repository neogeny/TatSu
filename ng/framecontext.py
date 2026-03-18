# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import inspect
from dis import Positions
from pathlib import Path


def execute_logic(a, b) -> float:
    # Multiple lines to fill the context buffer
    val_a = a + 10
    val_b = b + 20

    # The error occurs here
    calc = (val_a * 2) / (val_b - 20)

    return calc


def capture_error() -> Exception:
    try:
        execute_logic(5, 0)
        return Exception()
    except ZeroDivisionError as e:
        return e


def report_with_full_context(exc: Exception, size=4) -> None:
    tb = exc.__traceback__
    if tb is None:
        return
    # Fetch 'size' lines above and below
    frames = inspect.getinnerframes(tb, size)

    print(f"--- Traceback (Context Size: {size}) ---")
    for info in frames:
        p = Path(info.filename)
        pos = info.positions
        assert isinstance(pos, Positions)

        print(f"\nFile: {p.name}, Line {info.lineno}, in {info.function}")

        if info.code_context:
            for i, line in enumerate(info.code_context):
                # Use a marker for the current line in the gutter
                gutter = ">> " if i == info.index else "   "
                print(f"{gutter}{line.rstrip()}")

                # If this is the failing line, insert the column markers below it
                if i == info.index and pos.col_offset is not None:
                    # 3 spaces for the gutter + col_offset spaces
                    padding = "   " + (" " * pos.col_offset)

                    # Calculate caret length
                    low = pos.col_offset
                    high = pos.end_col_offset or low + 1
                    marker = "^" * max(1, high - low)

                    print(f"{padding}{marker}")
        else:
            print("   (Source code not available)")


if __name__ == "__main__":
    error = capture_error()
    report_with_full_context(error)

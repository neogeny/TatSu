# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import logging
import os
import sys
import warnings
from typing import Any

from .strtools import prints


def TATSUDEBUG() -> int:
    return 10 * int(os.environ.get('TATSUDEBUG', logging.ERROR // 10))


LEVEL: int = TATSUDEBUG()


def set_debugging(level: int | str | None) -> None:
    global LEVEL  # noqa: PLW0603
    LEVEL = translate_level(level)


def translate_level(level: int | str | None) -> int:
    if isinstance(level, str):
        return getattr(logging, level.upper())
    elif isinstance(level, int):
        if level < 10:
            return level * 10
        return level
    return logging.ERROR


def eprint(*args: Any, **kwargs: Any) -> None:
    file = kwargs.pop('file', sys.stderr)
    kwargs.pop("highlight", None)
    kwargs.pop("markup", None)
    print(*args, file=file, **kwargs)


def DEBUG_print(*args: Any, **kwargs: Any) -> None:
    if not (__debug__ or LEVEL <= logging.DEBUG):
        return
    eprint(*args, **kwargs)


def INFO_print(*args: Any, **kwargs: Any) -> None:
    if LEVEL <= logging.INFO:
        return
    eprint('ⓘ', *args, **kwargs)


def WARNING_print(*args: Any, **kwargs: Any) -> None:
    if LEVEL <= logging.WARNING:
        return
    eprint('⚠', *args, **kwargs)
    warnings.warn(prints(*args, **kwargs), stacklevel=2)


def ERROR_print(
    *args: Any,
    extype: type[Exception] = RuntimeError,
    **kwargs: Any,
) -> Exception:
    WARNING_print(*args, **kwargs)
    return extype(prints(*args, **kwargs))

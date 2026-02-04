# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import warnings
from typing import Any

from .string import prints


def stderr_print(*args: Any, **kwargs: Any) -> None:
    file = kwargs.pop('file', sys.stderr)
    print(*args, file=file, **kwargs)


def info(*args: Any, **kwargs: Any) -> None:
    stderr_print('ⓘ', *args, **kwargs)


def debug(*args: Any, **kwargs: Any) -> None:
    if not __debug__:
        return
    stderr_print('🐞', *args, **kwargs)


def warning(*args: Any, **kwargs: Any) -> None:
    warnings.warn(prints(*args, **kwargs), stacklevel=2)


def error(*args: Any, **kwargs: Any) -> None:
    raise RuntimeError(prints(*args, **kwargs))

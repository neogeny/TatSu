# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import os
import sys
import warnings
from typing import Any

from .strtools import prints


TATSUDEBUG: int | str | None = os.environ.get('TATSUDEBUG', 0)


def eprint(*args: Any, **kwargs: Any) -> None:
    file = kwargs.pop('file', sys.stderr)
    kwargs.pop("highlight", None)
    kwargs.pop("markup", None)
    print(*args, file=file, **kwargs)


def info(*args: Any, **kwargs: Any) -> None:
    eprint('ⓘ', *args, **kwargs)


def debug(*args: Any, **kwargs: Any) -> None:
    if not (__debug__ or TATSUDEBUG):
        return
    eprint(*args, **kwargs)


def warning(*args: Any, **kwargs: Any) -> None:
    warnings.warn(prints(*args, **kwargs), stacklevel=2)


def error(*args: Any, **kwargs: Any) -> None:
    raise RuntimeError(prints(*args, **kwargs))

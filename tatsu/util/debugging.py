from __future__ import annotations

import sys
import warnings
from typing import Any

from .strings import prints


def stderr_print(*args: Any, **kwargs: Any) -> None:
    kwargs.pop('file', None)
    print(*args, file=sys.stderr, **kwargs)


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

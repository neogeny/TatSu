# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

from .typetools import cast


def importall(modulename: str) -> dict[str, object]:
    """
    Simulate 'from modulename import *' and return the resulting attributes as a dict.
    """
    module = importlib.import_module(modulename)

    if hasattr(module, "__all__"):
        keys: list[str] = cast(list[str], module.__all__)  # pyright: ignore[reportAny]
    else:
        keys = [n for n in dir(module) if not n.startswith("_")]

    return {k: getattr(module, k) for k in keys}


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def module_missing(name: str) -> bool:
    return not module_available(name)


def pathtomodulename(path: str | Path) -> str:
    path = Path(path) if isinstance(path, str) else path
    return str(path.with_suffix('')).replace('/', '.').replace('.__init__', '')

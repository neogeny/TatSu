# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path


def importall(modulename: str) -> dict:
    """
    Simulate 'from modulename import *' and return the resulting attributes as a dict.
    """
    module = importlib.import_module(modulename)

    if hasattr(module, "__all__"):
        keys = module.__all__
    else:
        keys = [n for n in dir(module) if not n.startswith("_")]

    return {k: getattr(module, k) for k in keys}


def module_available(name):
    return importlib.util.find_spec(name) is not None


def module_missing(name):
    return not module_available(name)


def pathtomodulename(path: Path):
    return str(path.with_suffix('')).replace('/', '.').replace('.__init__', '')

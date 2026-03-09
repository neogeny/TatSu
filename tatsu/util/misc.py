# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import importlib.util
import re
import shutil
from functools import cache
from pathlib import Path

from .itertools import first  # bwcompat


@cache
def cached_re_compile(
    pattern: str | bytes | re.Pattern,
    /,
    flags: int = 0,
) -> re.Pattern:
    if isinstance(pattern, re.Pattern):
        return pattern
    pattern = str(pattern)
    return re.compile(pattern, flags=flags)


def module_available(name):
    return importlib.util.find_spec(name) is not None


def module_missing(name):
    return not module_available(name)


def platform_has_command(name) -> bool:
    # noinspection PyDeprecation
    return shutil.which(name) is not None


def pathtomodulename(path: Path):
    return str(path.with_suffix('')).replace('/', '.').replace('.__init__', '')

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import importlib.util
import re
import shutil
from functools import cache
from pathlib import Path

from .itertools import first  # bwcompat

__all__ = [
    'first',
    'cached_re_compile',
    'module_available',
    'module_missing',
    'platform_has_command',
]


try:
    from rich import print as rprint
except ImportError:

    def rprint(*args, **kwargs):

        def strip_rich_markup(text):
            tag_pattern = r"(?<!\[)\[/?[a-zA-Z0-9 #,._]+\](?!\])"
            stripped = re.sub(tag_pattern, "", str(text))

            return stripped.replace("[[", "[").replace("]]", "]")

        clean_args = [strip_rich_markup(arg) for arg in args]
        print(*clean_args, **kwargs)


@cache
def cached_re_compile(
    pattern: str | bytes | re.Pattern, /, flags: int = 0
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
    return shutil.which(name) is not None


def pathtomodulename(path: Path):
    return str(path.with_suffix('')).replace('/', '.').replace('.__init__', '')

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import copy
from typing import Any

from ..util import is_list


def cstappend(cst: Any, node: Any, aslist: bool = False) -> Any:
    if cst is None:
        return [node] if aslist else copy.copy(node)
    elif is_list(cst):
        return [*cst, node]
    else:
        return [cst, node]


def cstextend(cst: Any, node: Any) -> Any:
    if node is None:
        return cst
    elif cst is None:
        return copy.copy(node)
    elif is_list(node) and is_list(cst):
        return cst + node
    elif is_list(node):
        return [cst, *node]
    elif is_list(cst):
        return [*cst, node]
    else:
        return [cst, node]

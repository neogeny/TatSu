# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .contexts.decorator import isname, leftrec, name, nomemo, rule, tatsumasu
from .objectmodel import NodeDataclassParams, nodedataclass as dataclass

__all__ = [
    'NodeDataclassParams',
    'dataclass',
    'isname',
    'name',
    'leftrec',
    'nomemo',
    'rule',
    'tatsumasu',
]

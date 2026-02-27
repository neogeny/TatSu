# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .contexts.decorator import isname, name, leftrec, nomemo, rule, tatsumasu
from .objectmodel import TatSuDataclassParams, tatsudataclass as dataclass

__all__ = [
    'TatSuDataclassParams',
    'dataclass',
    'isname',
    'name',
    'leftrec',
    'nomemo',
    'rule',
    'tatsumasu',
]

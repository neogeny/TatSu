# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .model import modelgen
from .python import pythongen
from .python import pythongen as codegen

__all__ = ['codegen', 'pythongen', 'modelgen']

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .walkgen_model import modelgen
from .walkgen_parser import pythongen
from .walkgen_parser import pythongen as codegen

__all__ = ['codegen', 'pythongen', 'modelgen']

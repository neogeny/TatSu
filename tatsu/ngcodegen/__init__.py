# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .ngmodel_gen import modelgen
from .ngparser_gen import pythongen
from .ngparser_gen import pythongen as codegen

__all__ = ['codegen', 'pythongen', 'modelgen']

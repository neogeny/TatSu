# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .grammar_gen import parsermodel_gen as parsergen
from .ngmodel_gen import modelgen
from .ngparser_gen import pythongen, pythongen as codegen


__all__ = ['codegen', 'parsergen', 'pythongen', 'modelgen']

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
# CAVEAT: THIS LEGACY MODULE IS KEPT ONLY FOR BACKWARDS COMPATIBILITY
from __future__ import annotations

from .cgbase import CodeGenerator, ModelRenderer
from .modelgen import modelgen
from .pythongen import codegen
from ..exceptions import CodegenError

__all__ = ['CodeGenerator', 'ModelRenderer', 'CodegenError', 'codegen', 'modelgen']

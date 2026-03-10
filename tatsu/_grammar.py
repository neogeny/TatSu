# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from importlib import resources


grammar_path = resources.files().joinpath("_tatsu.tatsu")  # noqa: RUF067
grammar = grammar_path.read_text()  # noqa: RUF067

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""TatSu CLI package, mirroring ogopego's three-subcommand structure."""

from __future__ import annotations

from .cli import CLIConfig, main, parse_args


__all__ = [
    "CLIConfig",
    "main",
    "parse_args",
]

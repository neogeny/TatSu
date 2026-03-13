# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import shutil


def platform_has_command(name) -> bool:
    # noinspection PyDeprecation
    return shutil.which(name) is not None

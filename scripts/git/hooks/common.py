# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import subprocess
from pathlib import Path


def get_staged_files() -> list[Path]:
    """
    Get the list of files currently staged for commit.
    """
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=d'],
            capture_output=True,
            text=True,
            check=True
        )
        return [Path(filename) for filename in result.stdout.splitlines()]
    except subprocess.CalledProcessError:
        return []

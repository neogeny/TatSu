# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import subprocess
from pathlib import Path


def black(filenames: list[str]) -> list[str]:
    """
    Apply black to a list of filenames
    """
    try:
        subprocess.run(  # noqa: S603
            ['black', *filenames],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        )
        return filenames
    except subprocess.CalledProcessError:
        return []


def get_staged_files() -> list[Path]:
    """
    Get the list of files currently staged for commit.
    """
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=d'],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        )
        filenames = black(result.stdout.splitlines())
        return [Path(filename) for filename in filenames]
    except subprocess.CalledProcessError:
        return []

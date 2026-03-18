# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def black(*filepaths: str | Path) -> bool:
    """
    Apply black to a list of filenames
    """
    filenames = [str(p) for p in filepaths]
    try:
        result = subprocess.run(  # noqa: S603
            ['black', '--check', *filenames],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        )
        if result.returncode == 0:
            return True
        print(result.stderr)
        return False
    except subprocess.CalledProcessError:
        return False


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
        filenames = result.stdout.splitlines()
        return [Path(filename) for filename in filenames]
    except subprocess.CalledProcessError:
        return []

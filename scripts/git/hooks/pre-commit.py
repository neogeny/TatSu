#!/usr/bin/env python3
# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
# by [apalala@gmail.com](https://github.com/apalala)
# by Gemini (2026-02-03)
from __future__ import annotations

import subprocess
import sys
from collections.abc import Collection
from datetime import date
from pathlib import Path

from common import get_staged_files


def is_header_missing(path: Path, target: Collection[str]) -> bool:
    """
    Check if a file is missing the license header using native string ops.
    Works for # (Python/Makefile) and // (JSONC) comments.
    """
    try:
        with path.open('r', encoding='utf-8', errors='ignore') as f:
            # Check the first 1024 bytes for the header
            head = f.read(1024)
            return any(line not in head for line in target)
    except Exception:
        return False


def main() -> None:
    """
    Main entry point. Exits with 1 if any staged files lack the header.
    """
    year = date.today().year
    target = {
        'Copyright (c)',
        f'{year} Juancarlo Añez (apalala@gmail.com)',
        'SPDX-License-Identifier: BSD-4-Clause',
    }
    ignored_suffix = {
        '.dot',
        '.g4',
        '.ico',
        '.jpg',
        '.lock',
        '.md',
        '.pdf',
        '.png',
        '.pyc',
        '.txt',
        '.zip',
    }

    ignored_prefix = [
        'bootstrap',
    ]

    ignored_paths = [
        Path('./.vale/styles/'),
    ]


    staged = get_staged_files()
    missing_paths: list[Path] = []

    for path in staged:
        must_ignore = (
            path.suffix in ignored_suffix
            or any(path.stem.startswith(p) for p in ignored_prefix)
            or any(path.is_relative_to(p) for p in ignored_paths)
        )
        if must_ignore:
            continue

        if is_header_missing(path, target):
            missing_paths.append(path)

    if missing_paths:
        print("ERROR: Commit aborted. The following files are missing the license header:")
        for f in missing_paths:
            print(f"  - {f}")
        print(f"\nPlease add:\n{target}")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()

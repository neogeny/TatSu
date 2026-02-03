#!/usr/bin/env python3
# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
# by [apalala@gmail.com](https://github.com/apalala)
# by Gemini (2026-02-03)
from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence

type FileList = Sequence[str]


def get_staged_files() -> FileList:
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
        return result.stdout.splitlines()
    except subprocess.CalledProcessError:
        return []


def is_header_missing(path: str, target: str) -> bool:
    """
    Check if a file is missing the license header using native string ops.
    Works for # (Python/Makefile) and // (JSONC) comments.
    """
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            # Check the first 1024 bytes for the header
            head = f.read(1024)
            return any(line not in head for line in target.splitlines())
    except Exception:
        return False


def main() -> None:
    """
    Main entry point. Exits with 1 if any staged files lack the header.
    """
    target = (
        'Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)'
        '\nSPDX-License-Identifier: BSD-4-Clause'
    )
    ignored = {
        '.dot',
        '.ico',
        '.jpg',
        '.lock',
        '.pdf',
        '.png',
        '.pyc',
        '.txt',
        '.zip',
        }

    staged = get_staged_files()
    missing_files: list[str] = []

    for path in staged:
        if any(path.endswith(ext) for ext in ignored) or not os.path.isfile(path):
            continue

        if is_header_missing(path, target):
            missing_files.append(path)

    if missing_files:
        print("ERROR: Commit aborted. The following files are missing the license header:")
        for f in missing_files:
            print(f"  - {f}")
        print(f"\nPlease add:\n{target}")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()

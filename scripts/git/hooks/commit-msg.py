#!/usr/bin/env python3
# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence

# by [apalala@gmail.com](https://github.com/apalala)
# by Gemini (2026-02-03)

type FileList = Sequence[str]

def get_staged_files() -> FileList:
    """
    Get files staged for commit. Still requires one external call to git.
    """
    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-02-03)
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=d'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError:
        return []

def get_missing_headers(files: FileList) -> FileList:
    """
    Identify which files are missing the SPDX header.
    """
    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-02-03)
    target = "SPDX-License-Identifier: BSD-4-Clause"
    ignored = {'.png', '.jpg', '.pdf', '.pyc', '.dot', '.ico'}
    missing = []

    for path in files:
        if any(path.endswith(ext) for ext in ignored) or not os.path.isfile(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                if target not in f.read(1024):
                    missing.append(path)
        except Exception:
            pass
    return missing

def main() -> None:
    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-02-03)
    if len(sys.argv) < 2:
        sys.exit(0)

    commit_msg_filepath = sys.argv[1]
    staged = get_staged_files()
    missing = get_missing_headers(staged)

    if missing:
        with open(commit_msg_filepath, 'a', encoding='utf-8') as f:
            f.write("\n# --------------------------------------------------------\n")
            f.write("# LICENSE HEADER WARNING:\n")
            f.write("# The following files are missing the SPDX header:\n")
            for path in missing:
                f.write(f"#   - {path}\n")
            f.write("# --------------------------------------------------------\n")

    sys.exit(0)

if __name__ == "__main__":
    main()

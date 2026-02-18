# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import subprocess
import sys

from scripts.git.hooks.common import get_staged_files


def run_black_on_staged() -> bool:
    """
    Runs Black only on Python files that are currently staged.
    """
    # by Gemini 2026/02/18
    staged = get_staged_files()

    # Filter for Python files only
    py_files = [str(f) for f in staged if f.suffix == '.py']

    if not py_files:
        print("Black: No staged Python files to check.")
        return True

    print(f"--- Running Black on {len(py_files)} staged file(s) ---")

    # Execute black on the filtered list
    cmd = [sys.executable, "-m", "black"] + py_files

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Black: Staged files formatted successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Black: Failed to format staged files!\n{e.stderr}")
        return False

def pre_commit_pipeline():
    # Chain your checks here
    checks = [
        run_black_on_staged,
        # Add your other grammar validation functions here
    ]

    for check in checks:
        if not check():
            print("Pipeline aborted. Please fix errors before committing.")
            sys.exit(1)

if __name__ == "__main__":
    pre_commit_pipeline()

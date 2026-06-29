#!/usr/bin/env python3

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause

"""
Log parser to split, reverse, and rejoin git-style logs.
Diagnostic messages are sent to stderr; reversed text is sent to stdout.
by [apalala@gmail.com](https://github.com/apalala)
Gemini 3 Flash - 2026-01-28
"""

from __future__ import annotations

import pathlib
import re
import sys


def parse_commits(log_text):
    # by [apalala@gmail.com](https://github.com/apalala)
    pattern = re.compile(r'^> commit', re.MULTILINE)
    starts = [m.start() for m in pattern.finditer(log_text)]
    ends = [*starts[1:], len(log_text)]

    return [log_text[start:end].strip() for start, end in zip(starts, ends)]


def main():
    # by [apalala@gmail.com](https://github.com/apalala)
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <log_file>", file=sys.stderr)
        sys.exit(1)

    filename = sys.argv[1]

    if not pathlib.Path(filename).is_file():
        print(f"Error: File '{filename}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        log_content = pathlib.Path(filename).read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    commits = parse_commits(log_content)

    # Send diagnostic info to stderr
    print(f"Parsed {len(commits)} commits from {filename}.", file=sys.stderr)

    # Reverse the list of commits
    commits.reverse()

    # Rejoin the content with spacing for readability
    output_text = "\n\n".join(commits)

    # Print the actual text output to stdout
    print(output_text)


if __name__ == "__main__":
    main()

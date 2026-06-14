#!/usr/bin/env python3
# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations


if __name__ == "__main__":
    import sys

    url = sys.stdin.read().strip()
    out = f"""
.. image:: {url}
    :alt: New CLI tool demo
    :width: 800px
"""
    print(out)
    if not sys.stdout.isatty():
        print(out, file=sys.stderr)
    sys.exit()

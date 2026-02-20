# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from rich.syntax import Syntax


def print_grammar(filename: str):
    raw = Path(filename).read_text()

    text = "\n".join(line.rstrip() for line in raw.splitlines())

    console = Console(force_terminal=True)
    syntax = Syntax(
        text,
        "ebnf",
        theme="material",
        line_numbers=True,
        background_color="default",
    )

    console.print(syntax)


def main(args: list[str]) -> None:
    print_grammar(args[0])


if __name__ == '__main__':
    main(sys.argv[1:])

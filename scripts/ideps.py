# Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import ast
import sys
from collections.abc import Iterable
from pathlib import Path


def pathtomodulename(path: Path):
    return (
        str(path.with_suffix(''))
        .replace('/', '.')
        .replace('.__init__', '')
    )


def moduledeps(name: str, path: Path, localnames: set[str]):
    source = path.read_text()
    modast = ast.parse(source, filename=name)
    assert isinstance(modast, ast.Module), modast

    return tuple(
        s.module for s in modast.body
        if isinstance(s, ast.ImportFrom) and s.level
    )


def all_local_names(modulenames: Iterable[str]) -> set[str]:
    def dfs(names):
        for name in names:
            yield name
            yield from dfs(name.split('.', 1)[1:])

    return set(dfs(modulenames))


def findeps(paths: list[Path]):
    modulepaths = sorted((pathtomodulename(path), path) for path in paths)

    localnames = {name for name, _ in modulepaths}
    localnames = all_local_names(localnames)

    for name, path in modulepaths:
        print(f'{name}: {moduledeps(name, path, localnames=localnames)}')


def main(filenames: list[str]) -> None:
    findeps([Path(filename) for filename in filenames])


if __name__ == '__main__':
    if not sys.argv[1:]:
        print(f'usage:\n   python3 {Path(__file__).name} FILENAME...')
        sys.exit(1)
    main(sys.argv[1:])

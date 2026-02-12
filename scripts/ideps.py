# Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import NamedTuple


class ModuleImports(NamedTuple):
    name: str
    path: Path
    imports: tuple[str, ...]


def pathtomodulename(path: Path):
    return (
        str(path.with_suffix(''))
        .replace('/', '.')
        .replace('.__init__', '')
    )


def moduledeps(name: str, path: Path, level: int = 1) -> ModuleImports:
    source = path.read_text()
    ast_ = ast.parse(source, filename=name)
    assert isinstance(ast_, ast.Module), ast_

    def imported(fromimport: ast.ImportFrom) -> tuple[str, ...]:
        if fromimport.module:
            return (fromimport.module,)
        return tuple(alias.name for alias in fromimport.names)

    imports = {
        imp
        for s in ast_.body
        if isinstance(s, ast.ImportFrom) and s.level >= level
        for imp in imported(s)
    }
    imports = tuple(sorted(imports))
    return ModuleImports(name=name, path=path, imports=imports)


def findeps(paths: list[Path], level:int = 1) -> list[ModuleImports]:
    modulepaths = sorted(
        (pathtomodulename(path), path)
        for path in paths
    )
    return [moduledeps(name, path, level=level) for name, path in modulepaths]


def main(filenames: list[str]) -> None:
    paths = [Path(filename) for filename in filenames]
    for module in findeps(paths):
        print(f'{module.name}: {module.imports}')


if __name__ == '__main__':
    if not sys.argv[1:]:
        print(f'usage:\n   python3 {Path(__file__).name} FILENAME...')
        sys.exit(1)
    main(sys.argv[1:])

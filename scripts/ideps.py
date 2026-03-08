# Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import NamedTuple

from rich import print
from rich.tree import Tree


class ModuleImports(NamedTuple):
    name: str
    path: Path
    imports: tuple[str, ...]


def pathtomodulename(path: Path):
    return str(path.with_suffix("")).replace("/", ".").replace(".__init__", "")


def moduledeps(name: str, path: Path, level: int = 1) -> ModuleImports:
    source = path.read_text()
    module = ast.parse(source, filename=name)
    assert isinstance(module, ast.Module), module

    def imported(fromimport: ast.ImportFrom) -> tuple[str, ...]:
        if fromimport.module:
            return (fromimport.module,)
        return tuple(alias.name for alias in fromimport.names)

    imports = {
        imp
        for s in module.body
        if isinstance(s, ast.ImportFrom) and s.level >= level
        for imp in imported(s)
    }
    imports = tuple(sorted(imports))
    return ModuleImports(name=name, path=path, imports=imports)


def findeps(paths: list[Path], level: int = 1) -> list[ModuleImports]:
    modulepaths = sorted((pathtomodulename(path), path) for path in paths)
    return [moduledeps(name, path, level=level) for name, path in modulepaths]


def render(results: list[ModuleImports]) -> Tree:
    root = Tree("[bold green]Module Dependencies[/bold green]")
    for module in results:
        module_label = module.name.split(".")[-1]
        branch = root.add(f"[bold blue]{module_label}[/bold blue]")

        for imp in module.imports:
            leaf_label = imp.split(".")[-1]
            branch.add(leaf_label)
    return root


def main(filenames: list[str]) -> None:
    paths = [Path(filename) for filename in filenames]
    results = findeps(paths)

    tree = render(results)
    print(tree)


if __name__ == "__main__":
    if not sys.argv[1:]:
        print(f"usage:\n   python3 {Path(__file__).name} FILENAME...")
        sys.exit(1)
    main(sys.argv[1:])

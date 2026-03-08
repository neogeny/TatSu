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


def moduledeps(name: str, path: Path, level: int = 0) -> ModuleImports:
    source = path.read_text()
    module = ast.parse(source, filename=name)
    assert isinstance(module, ast.Module), module

    def imported(fromimport: ast.ImportFrom) -> tuple[str, ...]:
        if fromimport.module:
            # Hack out __future__
            if fromimport.module == "__future__":
                return ()
            return (fromimport.module,)
        return tuple(alias.name for alias in fromimport.names if alias.name != "__future__")

    imports = {
        imp
        for s in module.body
        if isinstance(s, ast.ImportFrom) and s.level >= level
        for imp in imported(s)
    }
    imports = tuple(sorted(imports))
    return ModuleImports(name=name, path=path, imports=imports)


def findeps(paths: list[Path], level: int = 0) -> list[ModuleImports]:
    modulepaths = sorted((pathtomodulename(path), path) for path in paths)
    return [moduledeps(name, path, level=level) for name, path in modulepaths]


def add_path(tree: Tree, qualified_name: str, style: str = "") -> Tree:
    """Recursively adds a qualified name path to a tree node."""
    current = tree
    for part in qualified_name.split("."):
        # Check if the child already exists to avoid duplication
        found = next((child for child in current.children if str(child.label) == part), None)
        if found:
            current = found
        else:
            current = current.add(part, style=style)
    return current


def render(results: list[ModuleImports]) -> Tree:
    root = Tree("[bold green]Module Dependencies[/bold green]")

    for module in results:
        # Create the branch for the module being analyzed (e.g. tatsu.codegen.genmodel)
        # Using a bold blue style for the "source" modules
        module_branch = add_path(root, module.name, style="bold blue")

        # Add each import as a nested sub-structure under that module
        for imp in module.imports:
            add_path(module_branch, imp)

    return root


def main(filenames: list[str]) -> None:
    paths = [Path(filename) for filename in filenames]
    results = findeps(paths, level=0)

    tree = render(results)
    print(tree)


if __name__ == "__main__":
    if not sys.argv[1:]:
        print(f"usage:\n   python3 {Path(__file__).name} FILENAME...")
        sys.exit(1)
    main(sys.argv[1:])

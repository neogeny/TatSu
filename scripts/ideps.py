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
            # Hack out __future__ dependencies
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


def render(results: list[ModuleImports]) -> Tree:
    root = Tree("[bold green]Module Dependencies[/bold green]")

    for module in results:
        # Root node for the specific module being analyzed
        module_label = module.name.split(".")[-1]
        branch = root.add(f"[bold blue]{module_label}[/bold blue]")

        # Build a nested structure for the imports
        for imp in module.imports:
            parts = imp.split(".")
            current = branch
            for part in parts:
                # Add or find the existing node for this segment
                # We search existing children to avoid duplicate branches
                found = next((child for child in current.children if str(child.label) == part), None)
                if found:
                    current = found
                else:
                    current = current.add(part)

    return root


def main(filenames: list[str]) -> None:
    paths = [Path(filename) for filename in filenames]
    # Level 0 captures absolute imports
    results = findeps(paths, level=0)

    tree = render(results)
    print(tree)


if __name__ == "__main__":
    if not sys.argv[1:]:
        print(f"usage:\n   python3 {Path(__file__).name} FILENAME...")
        sys.exit(1)
    main(sys.argv[1:])

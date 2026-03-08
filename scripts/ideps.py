# Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import NamedTuple

from rich.console import Console
from rich.tree import Tree


class Dependency(NamedTuple):
    name: str
    is_relative: bool


class ModuleImports(NamedTuple):
    name: str
    path: Path
    imports: tuple[Dependency, ...]


def pathtomodulename(path: Path) -> str:
    return str(path.with_suffix("")).replace("/", ".").replace(".__init__", "")


def moduledeps(name: str, path: Path) -> ModuleImports:
    source = path.read_text()
    module = ast.parse(source, filename=name)
    assert isinstance(module, ast.Module), module

    found_imports: set[Dependency] = set()

    for node in module.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                found_imports.add(Dependency(alias.name, is_relative=False))
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue

            is_rel = node.level > 0
            if node.module:
                found_imports.add(Dependency(node.module, is_relative=is_rel))
            else:
                for alias in node.names:
                    found_imports.add(Dependency(alias.name, is_relative=is_rel))

    return ModuleImports(
        name=name,
        path=path,
        imports=tuple(sorted(found_imports, key=lambda x: x.name))
    )


def findeps(paths: list[Path]) -> list[ModuleImports]:
    module_data = sorted((pathtomodulename(path), path) for path in paths)
    return [moduledeps(name, path) for name, path in module_data]


def add_path(
    tree: Tree,
    qualified_name: str,
    is_internal_dependency: bool = False,
    internal_roots: set[str] | None = None,
    is_root_module: bool = False
) -> Tree:
    parts = qualified_name.split(".")
    current = tree
    roots = internal_roots or set()

    for i, part in enumerate(parts):
        is_leaf = i == len(parts) - 1
        prefix = ".".join(parts[: i + 1])

        # Internal if:
        # 1. It's the module we are currently analyzing (is_root_module)
        # 2. It was flagged as a relative import
        # 3. It starts with a known project root
        is_internal = (
            is_root_module or
            is_internal_dependency or
            any(prefix.startswith(root) for root in roots)
        )

        label = part
        style = "cyan" if is_internal else "white"

        if is_internal:
            if is_root_module and i == 0:
                label = f"◉ {part}"
        else:
            if is_leaf:
                label = f"⟨{label}⟩"

        # Find or create node
        found = next((child for child in current.children if str(child.label).strip("◉ ⟨⟩ ") == part), None)
        if found:
            current = found
        else:
            current = current.add(label, style=style)

    return current


def render(results: list[ModuleImports]) -> Tree:
    root = Tree("Module Dependency Analysis")
    internal_roots = {m.name.split(".")[0] for m in results}

    for module in results:
        # The module itself is always internal
        module_branch = add_path(
            root,
            module.name,
            is_root_module=True,
            internal_roots=internal_roots
        )

        for imp in module.imports:
            add_path(
                module_branch,
                imp.name,
                is_internal_dependency=imp.is_relative,
                internal_roots=internal_roots
            )
    return root


def main() -> None:
    args = sys.argv[1:]
    force_color = "--color" in args
    if force_color:
        args.remove("--color")

    if not args:
        print(f"usage:\n   python3 {Path(__file__).name} [--color] FILENAME...")
        sys.exit(1)

    console = Console(force_terminal=force_color or "FORCE_COLOR" in os.environ)

    paths = [Path(filename) for filename in args]
    results = findeps(paths)

    tree = render(results)
    console.print(tree)


if __name__ == "__main__":
    main()

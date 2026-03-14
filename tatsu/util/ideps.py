# Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import ast
import sys
from itertools import starmap
from pathlib import Path
from typing import NamedTuple

from rich.console import Console
from rich.tree import Tree

from .moduletools import pathtomodulename


class Dependency(NamedTuple):
    name: str
    is_relative: bool


class ModuleImports(NamedTuple):
    name: str
    path: Path
    imports: tuple[Dependency, ...]


class DependencyNodeKind(NamedTuple):
    symbol: str | None
    style: str
    prefix: str = ""
    suffix: str = ""
    sort_rank: int = 0

    @classmethod
    def sibling(cls) -> DependencyNodeKind:
        return cls("○", "cyan", "", "", 1)

    @classmethod
    def internal(cls) -> DependencyNodeKind:
        return cls("◉", "cyan", "", "", 2)

    @classmethod
    def external(cls) -> DependencyNodeKind:
        return cls(None, "white", "⟨", "⟩", 3)


def programfiles() -> list[Path]:
    """
    Return all Python files that belong to the current program's
    top-level package, if available.
    """
    if not __package__:
        return []

    import importlib

    rootpkgname = __package__.split(".")[0]
    rootpkg = importlib.import_module(rootpkgname)
    rootfile = getattr(rootpkg, "__file__", None)
    if not rootfile:
        return []

    rootpath = Path(rootfile).parent.relative_to(Path.cwd())
    return [p for p in rootpath.rglob("*.py") if p.is_file()]


def moduledeps(name: str, path: Path) -> ModuleImports:
    """
    Parses a Python file to find all its module-level imports, resolving
    relative imports to their fully qualified names.
    """
    source = path.read_text()
    module = ast.parse(source, filename=name)
    assert isinstance(module, ast.Module), module

    found_imports: set[Dependency] = set()

    package_name_parts = name.split('.')
    if path.name != '__init__.py':
        package_name_parts = package_name_parts[:-1]

    for node in module.body:
        if not isinstance(node, ast.Import | ast.ImportFrom):
            continue

        if isinstance(node, ast.Import):
            found_imports.update(
                Dependency(alias.name, is_relative=False) for alias in node.names
            )
            continue

        if node.module == "__future__":
            continue

        level = node.level
        if level == 0:
            if node.module:  # It's an absolute import
                found_imports.add(Dependency(str(node.module), is_relative=False))
            continue

        # It's a relative import
        dot_count = level - 1
        if dot_count > len(package_name_parts):
            continue

        relative_base_parts = package_name_parts[: len(package_name_parts) - dot_count]
        base = ".".join(relative_base_parts)

        if node.module:
            full_name = f"{base}.{node.module}" if base else node.module
            found_imports.add(Dependency(full_name, is_relative=True))
            continue

        for alias in node.names:
            full_name = f"{base}.{alias.name}" if base else alias.name
            found_imports.add(Dependency(full_name, is_relative=True))

    return ModuleImports(
        name=name,
        path=path,
        imports=tuple(sorted(found_imports, key=lambda x: x.name)),
    )


def findeps(paths: list[Path]) -> list[ModuleImports]:
    module_data = sorted((pathtomodulename(path), path) for path in paths)
    return list(starmap(moduledeps, module_data))


def add_dependency_node(
    parent: Tree,
    qualified_name: str,
    is_internal: bool,
    importer_name: str,
    internal_roots: set[str],
):
    """
    Adds a dependency as an intelligently-named leaf node to the tree.
    """
    if not is_internal:
        kind = DependencyNodeKind.external()
        label = f"{kind.prefix}{qualified_name}{kind.suffix}"
    else:
        kind = DependencyNodeKind.internal()
        display_name = qualified_name

        importer_parts = importer_name.split('.')
        importee_parts = qualified_name.split('.')

        common_len = 0
        min_len = min(len(importer_parts), len(importee_parts))
        while (
            common_len < min_len
            and importer_parts[common_len] == importee_parts[common_len]
        ):
            common_len += 1

        importer_pkg_depth = len(importer_parts) - 1

        if (
            common_len == importer_pkg_depth
            and len(importee_parts) == importer_pkg_depth + 1
        ):
            display_name = importee_parts[-1]
            kind = DependencyNodeKind.sibling()
        elif common_len == importer_pkg_depth - 1:
            suffix = ".".join(importee_parts[common_len:])
            display_name = f"..{suffix}"
        elif qualified_name.startswith(importer_name + '.'):
            display_name = qualified_name[len(importer_name) + 1 :]
        else:
            root_part = qualified_name.split('.', 1)[0]
            if root_part in internal_roots:
                display_name = qualified_name[len(root_part) + 1 :]
                display_name = display_name.removeprefix(".")

        if kind.sort_rank == 1:
            display_name = f".{display_name}"
        label = f"{kind.symbol} {display_name}"

    parent.add(label, style=kind.style)


def render(results: list[ModuleImports]) -> Tree:
    """
    Renders the complete dependency tree from the analysis results.
    """
    root = Tree("[bold green]Module Dependency Analysis[/bold green]")
    module_nodes: dict[str, Tree] = {}
    analyzed_module_names = {m.name for m in results}
    internal_roots = {m.name.split(".")[0] for m in results}

    for module_name in sorted(analyzed_module_names):
        current = root
        parts = module_name.split('.')
        for i, part in enumerate(parts):
            path_so_far = ".".join(parts[: i + 1])
            if path_so_far in module_nodes:
                current = module_nodes[path_so_far]
            else:
                new_node = current.add(part, style="cyan")
                module_nodes[path_so_far] = new_node
                current = new_node

    for module in results:
        module_node = module_nodes[module.name]
        for imp in module.imports:
            imp_parent = ".".join(imp.name.split('.')[:-1])
            if imp.name in analyzed_module_names and imp_parent == module.name:
                continue

            imp_root = imp.name.split(".")[0]
            is_internal_imp = imp.is_relative or (imp_root in internal_roots)
            add_dependency_node(
                module_node,
                imp.name,
                is_internal_imp,
                importer_name=module.name,
                internal_roots=internal_roots,
            )

    def sort_tree(tree: Tree):
        def sort_key(n: Tree):
            label = str(n.label)
            symbol_map = {
                DependencyNodeKind.sibling()
                .symbol: DependencyNodeKind.sibling()
                .sort_rank,
                DependencyNodeKind.internal()
                .symbol: DependencyNodeKind.internal()
                .sort_rank,
                DependencyNodeKind.external()
                .prefix: DependencyNodeKind.external()
                .sort_rank,
                None: 0,
            }
            key = label[0] if label else None
            return symbol_map.get(key, 0), label

        tree.children.sort(key=sort_key)
        for child in tree.children:
            sort_tree(child)

    sort_tree(root)

    if len(root.children) == 1:
        return root.children[0]

    return root


def main(*args) -> None:
    args = list(args)
    force_color = "--color" in args
    if force_color:
        args.remove("--color")

    console = Console(force_terminal=force_color or None)

    paths: list[Path] = []
    if not args and __package__:
        paths = programfiles()
    elif not args:
        prog = f"python {Path(__file__).name}"
        print(f"usage:\n   {prog} [--color] FILENAME_OR_GLOB...")
        raise SystemExit(1)

    for arg in args:
        if any(c in arg for c in "*?[]"):
            expanded = Path().glob(arg)
            paths.extend(Path(p) for p in expanded if Path(p).is_file())
        elif (path := Path(arg)) and path.is_file():
            paths.append(path)

    paths = sorted(set(paths))

    if not paths:
        print("No Python files found matching the given paths.", file=sys.stderr)
        raise SystemExit(1)

    results = findeps(paths)
    tree = render(results)
    console.print(tree)


if __name__ == "__main__":
    main(*sys.argv[1:])

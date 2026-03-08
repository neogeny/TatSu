# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import cast

from asciitree import LeftAligned
from rich import print
from rich.tree import Tree


type ASCIITree = dict[str, str | ASCIITree]

tree: ASCIITree = {
    'TatSu': {
        'parsers': {
            'base.py': {},
            'ebnf.py': {}
        },
        'codegen': {
            'python.py': {}
        }
    }
}


def print_ascii_tree(tree: ASCIITree) -> None:
    tr = LeftAligned()
    print(tr(tree))


def to_rich_tree(tree: ASCIITree, rich_tree: Tree | None = None) -> Tree:
    if rich_tree is None:
        # Assume the top-level dict has one key as the root
        root_name = next(iter(tree))
        rich_tree = Tree(root_name)
        to_rich_tree(cast(ASCIITree, tree[root_name]), rich_tree)
        return rich_tree

    for key, value in tree.items():
        if isinstance(value, dict):
            to_rich_tree(value, rich_tree.add(key))
        else:
            rich_tree.add(f"{key}: {value}" if value else key)
    return rich_tree


if __name__ == "__main__":
    print("[bold green]ASCII Tree Rendering:[/bold green]")
    print_ascii_tree(tree)

    print("\n[bold green]Rich Tree Rendering:[/bold green]")
    rich_tree = to_rich_tree(tree)
    print(rich_tree)

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
# by Big Pickle 2026-06-21
from __future__ import annotations

from typing import Any


__all__ = ["Tree"]


class Tree:
    def __init__(self, label: Any, children: list[Tree] | None = None):
        self.label = label
        self.children: list[Tree] = children or []

    def add(self, label: Any) -> Tree:
        child = Tree(label)
        return self.add_child(child)

    def add_child(self, child: Tree) -> Tree:
        self.children.append(child)
        return child

    def __str__(self) -> str:
        return self.render()

    def render(self) -> str:
        lines = [f"{self.label}"]
        if not self.children:
            return "\n".join(lines)

        for child in self.children[:-1]:
            sub = child.render().splitlines()
            lines.append("├── " + sub[0])
            for line in sub[1:]:
                lines += ["│   " + line]

        child = self.children[-1]
        sub = child.render().splitlines()
        lines.append("└── " + sub[0])
        for line in sub[1:]:
            lines += ["    " + line]

        return "\n".join(lines)

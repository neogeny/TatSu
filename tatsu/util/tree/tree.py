from __future__ import annotations


__all__ = ["Tree"]


class Tree:
    def __init__(self, label: str):
        self.label = label
        self.children: list[Tree] = []

    def add(self, label: str, style=None) -> Tree:
        child = Tree(label)
        self.children.append(child)
        return child

    def __str__(self) -> str:
        return self.render()

    def render(self) -> str:
        lines = [self.label]
        if not self.children:
            return "\n".join(lines)

        for child in self.children[:-1]:
            sub = child.render().splitlines()
            lines.append("├── " + sub[0])
            for line in sub[1:]:
                lines.append("│   " + line)

        child = self.children[-1]
        sub = child.render().splitlines()
        lines.append("└── " + sub[0])
        for line in sub[1:]:
            lines.append("    " + line)

        return "\n".join(lines)

#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["markdown-it-py"]
# ///
"""
Convert LAIA.md to LAIA.txt — plain text, 80 columns.

Usage:
    python3 scripts/md2txt.py LAIA.md LAIA.txt
    python3 scripts/md2txt.py LAIA.md > LAIA.txt
"""

import sys
import textwrap

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode


def justify(text: str, width: int) -> str:
    """Justify wrapped text so every line (except the last) is exactly *width* wide."""
    lines = text.split("\n")
    out: list[str] = []
    for i, line in enumerate(lines):
        if i == len(lines) - 1 or not line.strip() or len(line) >= width:
            out.append(line)
        else:
            words = line.split()
            if len(words) <= 1:
                out.append(line)
                continue
            char_total = sum(len(w) for w in words)
            gap_count = len(words) - 1
            space_total = width - char_total
            base = space_total // gap_count
            extra = space_total % gap_count
            justified = words[0]
            for j, w in enumerate(words[1:], 1):
                justified += " " * (base + (1 if j <= extra else 0)) + w
            out.append(justified)
    return "\n".join(out)


def render_inline(node: SyntaxTreeNode) -> str:
    """Render an inline SyntaxTreeNode to plain text."""
    parts: list[str] = []
    for child in node.children:
        t = child.type
        if t == "text":
            parts.append(child.content)
        elif t == "code_inline":
            parts.append(child.content)
        elif t in ("strong", "em", "s"):
            parts.append(render_inline(child))
        elif t == "link":
            parts.append("[" + render_inline(child) + "]")
        elif t == "softbreak":
            parts.append(" ")
        elif t == "hardbreak":
            parts.append("\n")
        elif t == "image":
            parts.append(child.content or "")
        elif t == "html_inline":
            if not child.content.startswith("<!--"):
                parts.append(child.content)
        else:
            parts.append(child.content or "")
    return "".join(parts)


def convert(md: str) -> str:
    parser = MarkdownIt("default", {"linkify": False, "typographer": False})
    parser.enable(["table"])
    tokens = parser.parse(md)
    root = SyntaxTreeNode(tokens)

    out: list[str] = []
    list_stack: list[str] = []

    def blank():
        """Add a blank line if the last output line is not already blank."""
        if not out:
            return
        if out[-1] == "":
            return
        out.append("")

    def enter(node: SyntaxTreeNode):
        nonlocal list_stack
        t = node.type

        # ── Headings ──────────────────────────────────────
        if t == "heading":
            level = int(node.tag[1]) if node.tag.startswith("h") else 2
            inline_child = _first_inline(node)
            text = render_inline(inline_child) if inline_child else ""
            blank()
            out.append(text.upper())
            blank()

        # ── Lists ─────────────────────────────────────────
        if t == "bullet_list":
            indent = "  " + "  " * len(list_stack) + "* "
            list_stack.append(indent)
        elif t == "ordered_list":
            indent = "  " + "  " * len(list_stack) + "1. "
            list_stack.append(indent)
        elif t == "list_item":
            pass

        # ── Paragraphs ────────────────────────────────────
        elif t == "paragraph":
            inline_child = _first_inline(node)
            if inline_child:
                text = render_inline(inline_child)
                if text.strip():
                    segments = text.split("\n")
                    if list_stack:
                        prefix = list_stack[-1]
                        avail = 80 - len(prefix)
                        if avail >= 20:
                            wrapped = []
                            for seg in segments:
                                w = textwrap.fill(seg, width=avail)
                                if w:
                                    w = justify(w, avail)
                                    for line in w.split("\n"):
                                        wrapped.append(prefix + line)
                            text_out = "\n".join(wrapped)
                        else:
                            text_out = prefix + text
                    else:
                        wrapped = []
                        for seg in segments:
                            w = textwrap.fill(seg, width=80)
                            if w:
                                wrapped.append(justify(w, 80))
                        text_out = "\n".join(wrapped)
                    out.append(text_out)
            blank()

        # ── Fenced code blocks ───────────────────────────
        elif t == "fence":
            content = node.content.rstrip("\n")
            if content:
                blank()
                for line in content.split("\n"):
                    out.append("    " + line)
                blank()

        # ── Indented code blocks ─────────────────────────
        elif t == "code_block":
            content = node.content.rstrip("\n")
            if content:
                blank()
                for line in content.split("\n"):
                    out.append("    " + line)
                blank()

        # ── Horizontal rules ─────────────────────────────
        elif t == "hr":
            blank()
            out.append("-" * 72)
            blank()

        # ── Tables ───────────────────────────────────────
        elif t == "table":
            blank()
            rows = []
            for child in node.children:
                if child.type in ("thead", "tbody"):
                    for row in child.children:
                        if row.type == "tr":
                            cells = []
                            for cell in row.children:
                                if cell.type in ("th", "td"):
                                    cells.append(render_inline(cell))
                            if cells:
                                rows.append("  " + " | ".join(cells))
            out.extend(rows)
            blank()

    def exit(node: SyntaxTreeNode):
        nonlocal list_stack
        t = node.type
        if t == "bullet_list" or t == "ordered_list":
            if list_stack:
                list_stack.pop()
            blank()
        elif t == "blockquote":
            blank()

    def walk(node: SyntaxTreeNode):
        enter(node)
        for child in node.children:
            walk(child)
        exit(node)

    walk(root)
    return "\n".join(out)


def _first_inline(node: SyntaxTreeNode) -> SyntaxTreeNode | None:
    for child in node.children:
        if child.type == "inline":
            return child
    return None


def main():
    if len(sys.argv) >= 3:
        with open(sys.argv[1]) as f:
            md = f.read()
        result = convert(md)
        with open(sys.argv[2], "w") as f:
            f.write(result)
            if not result.endswith("\n"):
                f.write("\n")
    elif len(sys.argv) == 2:
        with open(sys.argv[1]) as f:
            md = f.read()
        result = convert(md)
        sys.stdout.write(result)
        if not result.endswith("\n"):
            sys.stdout.write("\n")
    else:
        md = sys.stdin.read()
        result = convert(md)
        sys.stdout.write(result)
        if not result.endswith("\n"):
            sys.stdout.write("\n")


if __name__ == "__main__":
    main()

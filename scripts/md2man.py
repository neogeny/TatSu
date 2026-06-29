#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["markdown-it-py"]
# ///
"""
Convert markdown to plain text, manpage format.

Usage:
    md2txt [options] [input [output]]

If input is omitted, reads from stdin. If output is omitted, writes to stdout.
"""

import argparse
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


def convert(md: str, width: int = 80, do_justify: bool = True) -> str:
    parser = MarkdownIt("default", {"linkify": False, "typographer": False})
    parser.enable(["table"])
    tokens = parser.parse(md)
    root = SyntaxTreeNode(tokens)

    out: list[str] = []
    list_stack: list[str] = []

    def blank():
        if not out:
            return
        if out[-1] == "":
            return
        out.append("")

    def _do_justify(text: str, w: int) -> str:
        return justify(text, w) if do_justify else text

    def enter(node: SyntaxTreeNode):
        nonlocal list_stack
        t = node.type

        if t == "heading":
            level = int(node.tag[1]) if node.tag.startswith("h") else 2
            inline_child = _first_inline(node)
            text = render_inline(inline_child) if inline_child else ""
            blank()
            out.append(text.upper())
            blank()

        if t == "bullet_list":
            indent = "  " + "  " * len(list_stack) + "* "
            list_stack.append(indent)
        elif t == "ordered_list":
            indent = "  " + "  " * len(list_stack) + "1. "
            list_stack.append(indent)
        elif t == "list_item":
            pass

        elif t == "paragraph":
            inline_child = _first_inline(node)
            if inline_child:
                text = render_inline(inline_child)
                if text.strip():
                    segments = text.split("\n")
                    if list_stack:
                        prefix = list_stack[-1]
                        avail = width - len(prefix)
                        if avail >= 20:
                            wrapped = []
                            for seg in segments:
                                w = textwrap.fill(seg, width=avail)
                                if w:
                                    w = _do_justify(w, avail)
                                    for line in w.split("\n"):
                                        wrapped.append(prefix + line)
                            text_out = "\n".join(wrapped)
                        else:
                            text_out = prefix + text
                    else:
                        wrapped = []
                        for seg in segments:
                            w = textwrap.fill(seg, width=width)
                            if w:
                                wrapped.append(_do_justify(w, width))
                        text_out = "\n".join(wrapped)
                    out.append(text_out)
            blank()

        elif t == "fence":
            content = node.content.rstrip("\n")
            if content:
                blank()
                for line in content.split("\n"):
                    out.append("    " + line)
                blank()

        elif t == "code_block":
            content = node.content.rstrip("\n")
            if content:
                blank()
                for line in content.split("\n"):
                    out.append("    " + line)
                blank()

        elif t == "hr":
            blank()
            out.append("-" * 72)
            blank()

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
    parser = argparse.ArgumentParser(
        description="Convert markdown to plain text (manpage format).",
    )
    parser.add_argument("input", nargs="?", help="input file (stdin if omitted)")
    parser.add_argument("output", nargs="?", help="output file (stdout if omitted)")
    parser.add_argument(
        "-w", "--width", type=int, default=80, help="line width (default: 80)"
    )
    parser.add_argument(
        "--no-justify",
        action="store_false",
        dest="justify",
        help="disable line justification",
    )

    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            md = f.read()
    else:
        md = sys.stdin.read()

    result = convert(md, width=args.width, do_justify=args.justify)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
            if not result.endswith("\n"):
                f.write("\n")
    else:
        sys.stdout.write(result)
        if not result.endswith("\n"):
            sys.stdout.write("\n")


if __name__ == "__main__":
    main()

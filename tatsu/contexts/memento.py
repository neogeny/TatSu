# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from io import StringIO

from ..input import LineInfo
from ..util.strtools import slicetowidth
from ..util.ztyle import Color, Style
from .infos import RuleInfo


MEMENTO_DEFAULT_COLOR = Color.stderr()


class _ColorSet:
    def __init__(self, color: Color = MEMENTO_DEFAULT_COLOR):
        self.err = Style(bold=True, fg=1, color=color)
        self.loc = Style(fg=4, color=color)
        self.gut = Style(color=color).blue().bold()
        self.ar = Style(color=color).red().dim()
        self.nam = Style(color=color).white().bold()
        self.msg = Style(color=color).white().bold()
        self.num = Style(color=color).white().dim()


def memento(
    msg: str,
    text: str,
    info: LineInfo,
    stack: list[RuleInfo],
    color: Color = MEMENTO_DEFAULT_COLOR,
) -> str:
    c = _ColorSet(color)
    line, col = info.line, info.col
    source = info.source or '<unknown>'
    rulestack = [r.name for r in reversed(stack)]

    out = StringIO()
    s = Style(color=color)

    lines = text.splitlines()
    errmsg = f'{c.err("error:")} {c.msg(msg)}'
    print(errmsg, file=out)
    loc = s(f'[{line + 1}:{col + 1}]').dim()
    print(
        f'{c.gut("  ->")} {c.nam(source)}{loc}',
        file=out,
    )
    gut = c.gut("│")
    print(f'   {gut}', file=out)

    max_line_digits = len(str(line + 1))
    start_line_idx = max(0, line - 4)

    for i in range(start_line_idx, min(line + 1, len(lines))):
        current_line_num = i + 1
        content = lines[i].expandtabs()
        snum = c.num(f'{current_line_num:>{max_line_digits}}')
        print(
            f' {snum} {gut} {content}',
            file=out,
        )

    padding = ' ' * max(0, col)
    print(
        f' {" ":{max_line_digits + 1}}{gut}'
        f' {padding}{c.err("⌃ ")} {c.err(slicetowidth(msg, 40))}',
        file=out,
    )

    print(file=out)
    for call in rulestack:
        print(f'{c.ar("→")} {s(call).dim()}', file=out)

    return out.getvalue()

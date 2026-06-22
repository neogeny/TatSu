# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

"""Character-based progress bar visual using fill/empty markers."""

from .. import findfirst
from ..ztyle import Style


__all__ = ["Bar"]


class Bar:
    def __init__(
        self,
        /,
        total: int = 1,
        *,
        width: int = 0,
        fill: str = "=>.",  # pyright: ignore[reportRedeclaration]
        style: list[Style] | None = None,
    ):
        self.pos: int = 0
        self.total: int = total
        self.width: int = width
        self.fill: str = (fill + "...")[:3]

        self.style: list[Style] = style or []
        s = Style()
        if not self.style:
            self.style = [s] * 3
        elif len(self.style) == 2:
            self.style = [*self.style, s]
        else:
            self.style = [self.style[0]] * 2 + [s]

    def __str__(self) -> str:
        return self.render(max(1, self.total))

    def __len__(self) -> int:
        return self.width

    def __format__(self, fmt: str) -> str:
        ws = findfirst(r"(\d+).?", fmt)
        w = int(ws) if ws else self.total
        return self.render(w)

    def update(self, pos: int, total: int, fill: str | None = None) -> None:
        self.pos = pos
        self.total = total
        if fill is not None:
            self.fill = fill

    def render(self, budget: int) -> str:
        total = max(1, self.pos, self.total)

        pos = self.pos
        pos = max(0, min(total, self.pos))

        done_w = int(pos / total * budget)
        todo_w = budget - done_w

        dones = self.render_done(done_w)
        todos = self.render_todo(todo_w)

        return self.trim_to_width(budget, f"{dones}{todos}")

    def render_done(self, w: int) -> str:
        done = self.fill[0]
        sd = self.style[0]
        if self.pos >= self.total:
            return sd.apply(done * w)

        head = self.fill[1]
        sh = self.style[1]
        if sh == sd:
            return sd.apply(done * (w - 1) + head)
        return sd.apply(done * (w - 1)) + sh.apply(head)

    def render_todo(self, w: int) -> str:
        todo = self.fill[2]
        st = self.style[2]
        return st.apply(todo * w)

    def trim_to_width(self, budget: int, rendered: str) -> str:
        from ..ztyle import visual_len as vlen

        while (w := vlen(rendered)) > budget:
            chars = [
                self.fill[1],
                self.fill[2],
                self.fill[0],
                "█",
                "░",
                ">",
                "-",
                "=",
                ".",
            ]
            for char in chars:
                rendered = rendered.replace(char, "", 1)
                if vlen(rendered) < w:
                    break
        return rendered

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import random
import threading
import time
from typing import Any

from ..ztyle import Color, Style  # noqa: F401
from .bar import Bar
from .multi import Multi
from .row import BarRow, Col


def main() -> None:
    """Visual test — run with ``python -m tatsu.util.bars``."""
    c = Color(True)

    class StyleRow(BarRow):
        def render(self, metrics: dict[Col, Any]) -> list[Any]:
            s = Style()
            m = metrics
            bar = Bar(
                fill="=>`",
                style=[s.green(), s.green(), s.white().dim()],
            )
            bar.update(m[Col.pos], m[Col.total])
            return [
                f"{s(m[Col.label], fmt=">20s")} ",
                bar,
                f"{100 * m[Col.pct]:3.0f}% ",
                # f"{m[Col.elapsed]:4.1f}s",
                f"{m[Col.m]:02d}:{m[Col.s]:02d}.{m[Col.ms]:03d}",
            ]

    s = c.style()
    red = s.red()
    green = s.green()
    blue = s.blue().bold()

    overall = BarRow(
        label="overall: ",
        fill="--_",
        style=[green, green, s.dim()],
    )
    bars: list[BarRow] = [
        overall,
        StyleRow(label=red("lexing"), style=[red]),
        BarRow(label="parsing"),
        BarRow(label="semantics", total=200),
        StyleRow(label="codegen", total=500, style=[blue]),
        BarRow(label="testing", total=50),
    ]
    overall.update(0, len(bars))

    m = Multi(bars)

    def worker(bar: BarRow, delay: float, step: int, overall: BarRow):
        bar.start()
        m.print(f"starting {bar.label}")
        while bar.pos < bar.total:
            time.sleep(delay)
            bar.update(min(bar.pos + random.randint(1, step), bar.total))  # noqa: S311
        m.print(blue(f"{step} finished {bar.label}"))
        overall.update(overall.pos + 1)

    threads = [
        threading.Thread(target=worker, args=(b, d, s, overall), daemon=True)
        for b, d, s in [
            (bars[1], 0.10, 8),
            (bars[2], 0.16, 5),
            (bars[3], 0.20, 10),
            (bars[4], 0.08, 4),
            (bars[5], 0.30, 2),
        ]
    ]

    m.print(red("workers starting up"))
    m.print(blue("pipeline warming"))

    m.start()

    for b in bars:
        b.start()
    try:
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    m.stop()


if __name__ == "__main__":
    main()

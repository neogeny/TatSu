# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import random
import threading
import time
from typing import Any

from ..style import Color, Style  # noqa: F401
from .bar import Bar, BarRow, Col
from .multi import Multi


def main() -> None:
    """Visual test — run with ``python -m tatsu.util.bars``."""
    c = Color(True)

    class StyleRow(BarRow):
        def render(self, metrics: dict[Col, Any]) -> list[Any]:
            s = Style()
            m = metrics
            bar = Bar(
                fill="-?`",
                style=[s.green(), s.green(), s.dim()],
            )
            bar.update(m[Col.pos], m[Col.total])
            return [
                f"{s(m[Col.label], fmt=">20s")} ",
                bar,
                f"{100 * m[Col.pct]:3.0f}% ",
                f"{m[Col.h]:02}:{m[Col.m]:02}:{m[Col.s]:02}",
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
        m.print(f"starting {bar.label}")
        while bar.pos < bar.total:
            time.sleep(delay)
            bar.update(min(bar.pos + random.randint(1, step), bar.total))  # noqa: S311
        m.print(blue(f"{step} finished {bar.label}"))
        overall.update(overall.pos + 1)

    threads = [
        threading.Thread(target=worker, args=(b, d, s, overall), daemon=True)
        for b, d, s in [
            (bars[1], 0.16, 8),
            (bars[2], 0.24, 5),
            (bars[3], 0.40, 10),
            (bars[4], 0.12, 4),
            (bars[5], 0.60, 2),
        ]
    ]

    m.print(red("workers starting up"))
    m.print(blue("pipeline warming"))

    m.start()

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

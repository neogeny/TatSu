# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .bar import *  # noqa: F403
from .line import *  # noqa: F403
from .multi import *  # noqa: F403


def main():
    """Visual test — run with ``python -m tatsu.util.bars``."""
    import random
    import threading
    import time
    from dataclasses import dataclass

    from tatsu.util.bars import (
        Bar,
        Col,
        FillWidth,
        LeftJust,
        Line,
        Multi,
        RightJust,
    )
    from tatsu.util.colorize import Color, Style  # noqa: F401

    c = Color(True)

    @dataclass
    class StyleBar(Bar):
        style: Style

        def render(self, m: Bar.Metrics) -> Line:
            return [
                # Col(LeftJust(20), self.style(self.label)),
                Col(LeftJust(20), self.label),
                Col(RightJust(8), f"{100 * m.pct:3.0f}%"),
                Col(FillWidth, m.bart()),
            ]

    s = c.style()
    red = s.red()
    blue = s.blue().bold()

    bars: list[Bar] = [
        StyleBar(label="lexing", style=red),
        Bar(label="parsing"),
        Bar(label="semantics", total=200),
        StyleBar(label="codegen", total=500, style=blue),
        Bar(label="testing", total=50),
    ]

    m = Multi(bars)
    m.start()

    def worker(bar: Bar, delay: float, step: int):
        while bar.done < bar.total:
            time.sleep(delay)
            bar.update(min(bar.done + random.randint(1, step), bar.total))  # noqa: S311

    threads = [
        threading.Thread(target=worker, args=(b, d, s), daemon=True)
        for b, d, s in [
            (bars[0], 0.04, 8),
            (bars[1], 0.06, 5),
            (bars[2], 0.10, 10),
            (bars[3], 0.03, 4),
            (bars[4], 0.15, 2),
        ]
    ]

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

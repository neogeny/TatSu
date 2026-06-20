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
    from dataclasses import dataclass, field

    from tatsu.util.bars import (
        Bar,
        Col,
        FillWidth,
        FixedWidth,
        LeftJust,
        Line,
        Multi,
        RightJust,
    )
    from tatsu.util.style import Color, Style  # noqa: F401

    c = Color(True)

    @dataclass
    class StyleBar(Bar):
        style: Style = field(default_factory=Style)

        def render(self, m: Bar.Metrics) -> Line:
            return [
                # Col(LeftJust(20), self.style(self.label)),
                Col(LeftJust(20), self.label),
                Col(RightJust(8), f"{100 * m.pct:3.0f}%"),
                Col(FillWidth, m.bart(done=s("-").green(), todo=".")),
                # Col(FillWidth, m.bart(done=("-"), todo=".")),
            ]

    @dataclass
    class TopBar(StyleBar):
        def render(self, m: Bar.Metrics) -> Line:
            return [
                Col(
                    FixedWidth(20),
                    m.bart(
                        done=s("-").yellow().bold(),
                        todo=s("-").basic_white().dim(),
                    ),
                ),
            ]

    s = c.style()
    red = s.red()
    blue = s.blue().bold()

    bars: list[Bar] = [
        StyleBar(label="lexing", style=red),
        StyleBar(label="parsing"),
        Bar(label="semantics", top=200),
        StyleBar(label="codegen", top=500, style=blue),
        Bar(label="testing", top=50),
    ]

    overall = TopBar(top=len(bars))
    bars.insert(0, overall)

    m = Multi(bars)
    m.print(red("lexing engines warming up"))
    m.print(blue("parsing pipeline ready"))
    m.start()

    def worker(multi: Multi, bar: Bar, delay: float, step: int, overall: Bar):
        multi.print(f"starting {bar.label}")
        while bar.pos < bar.top:
            time.sleep(delay)
            bar.update(min(bar.pos + random.randint(1, step), bar.top))  # noqa: S311
        multi.print(blue(f"finished {bar.label}"))
        overall.update(overall.pos + 1)

    threads = [
        threading.Thread(target=worker, args=(m, b, d, s, overall), daemon=True)
        for b, d, s in [
            (bars[1], 0.08, 8),
            (bars[2], 0.12, 5),
            (bars[3], 0.20, 10),
            (bars[4], 0.06, 4),
            (bars[5], 0.30, 2),
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

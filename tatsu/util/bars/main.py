# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations


def main() -> None:
    """Visual test — run with ``python -m tatsu.util.bars``."""
    import random
    import threading
    import time
    from typing import Any

    from tatsu.util.bars import BarRow, Multi
    from tatsu.util.style import Color, Style  # noqa: F401

    c = Color(True)

    class StyleRow(BarRow):
        style: Style

        def __init__(
            self,
            label: str,
            style: Style,
            *,
            total: int = 0,
        ):
            super().__init__(label, fill=('-', '-', '.'))
            self.style = style

        def render(self, m: BarRow.Metrics) -> list[Any]:
            return [
                f"{self.style(m.label, fmt=">20s")} ",
                self.bar,
                f"{100 * m.pct:3.0f}% ",
                "{h:02}:{m:02}",
            ]

    s = c.style()
    red = s.red()
    blue = s.blue().bold()

    overall = BarRow(
        label="total",
        fill=(str(s('-').green()), '-', s('-').dim()),
    )
    bars: list[BarRow] = [
        overall,
        StyleRow(label="lexing", style=red),
        BarRow(label="parsing"),
        BarRow(label="semantics", total=200),
        StyleRow(label="codegen", total=500, style=blue),
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
            (bars[1], 0.08, 8),
            (bars[2], 0.12, 5),
            (bars[3], 0.20, 10),
            (bars[4], 0.06, 4),
            (bars[5], 0.30, 2),
        ]
    ]

    m.print(red("workers starting up"))
    m.print(blue("pipeline warming"))

    # import sys
    # sys.stderr.write("\033[2J\033[H")
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

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations


def main() -> None:
    """Visual test — run with ``python -m tatsu.util.bars``."""
    import random
    import threading
    import time
    from typing import Any

    from tatsu.util.bars import Multi, Row
    from tatsu.util.style import Color, Style  # noqa: F401

    c = Color(True)

    class StyleRow(Row):
        style: Style

        def __init__(
            self,
            label: str,
            style: Style,
            *,
            top: int = 0,
        ):
            super().__init__(label, fill=('-', '-', ' '))
            self.style = style

        def render(self, m: Row.Metrics) -> list[Any]:
            return [
                f"{self.style(m.label, fmt=">20s")} ",
                self.bar,
                f"{100 * m.pct:3.0f}% ",
                "{h:02}:{m:02}",
            ]

    s = c.style()
    red = s.red()
    blue = s.blue().bold()

    bars: list[Row] = [
        StyleRow(label="lexing", style=red),
        Row(label="parsing"),
        Row(label="semantics", top=200),
        StyleRow(label="codegen", top=500, style=blue),
        Row(label="testing", top=50),
    ]

    overall = Row(label="total", top=len(bars), fill=(str(s('-').green()), '-', '.'))
    bars.insert(0, overall)

    m = Multi(bars)
    m.start()

    def worker(bar: Row, delay: float, step: int, overall: Row):
        while bar.pos < bar.top:
            time.sleep(delay)
            bar.update(min(bar.pos + random.randint(1, step), bar.top))  # noqa: S311
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

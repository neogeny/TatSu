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

    from .bar import Bar
    from .multi import Multi

    bars = [
        Bar(label="lexing"),
        Bar(label="parsing"),
        Bar(label="semantics", total=200),
        Bar(label="codegen", total=500),
        Bar(label="testing", total=50),
    ]

    m = Multi(bars)
    m.start()

    def worker(bar: Bar, delay: float, step: int):
        while bar.current < bar.total:
            time.sleep(delay)
            bar.update(min(bar.current + random.randint(1, step), bar.total))  # noqa: S311

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
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    time.sleep(0.5)
    m.stop()


if __name__ == "__main__":
    main()

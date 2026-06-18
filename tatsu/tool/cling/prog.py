# Copyright © 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any

from ...util import parproc
from .sum import Printer


def make_progressbar() -> Any:
    from rich.progress import (  # pyright: ignore[reportMissingImports]
        BarColumn,
        Progress,
        TaskID,
        TextColumn,
    )
    from rich.table import Table

    class DualProgress(Progress, parproc.Progress, Printer):
        def __init__(self, *columns, **kwargs) -> None:
            super().__init__(*columns, transient=True, **kwargs)
            self._file_cols = [
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="green"),
                # TaskProgressColumn(style="green"),
            ]
            self._main_id: TaskID | None = None

        def set_main(self, tid: TaskID) -> None:
            self._main_id = tid

        def get_renderables(self):
            for task in self.tasks:
                if not task.visible:
                    continue
                columns = self.columns if task.id == self._main_id else self._file_cols
                table = Table.grid(padding=(0, 1))
                for _ in columns:
                    table.add_column(no_wrap=True)
                table.add_row(*(c.render(task) for c in columns))  # pyright: ignore[reportAttributeAccessIssue]
                yield table

    return DualProgress(
        # TaskProgressColumn(),
        # TimeElapsedColumn(),
        # TimeRemainingColumn(),
        # TextColumn("[name][progress.description]"),
        # TextColumn("[progress.description][task.description]"),
        BarColumn(
            bar_width=None,
            complete_style="yellow",
        ),
        refresh_per_second=1,
        speed_estimate_period=30.0,
    )

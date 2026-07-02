# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import threading
import time

from ..packetz import Packet, PacketzQueue
from .multi import Multi
from .row import BarRow


class BarBroker:
    def __init__(self, multi: Multi, fps: float = 60):
        self.multi = multi
        self.queue: PacketzQueue = PacketzQueue()
        self.reader: threading.Thread | None = None
        self.alive = False
        self.fps = fps

    def start(self):
        """Starts the completely isolated background rendering thread."""
        self.alive = True
        self.multi.start()

        self.reader = threading.Thread(target=self._read_queue, daemon=True)
        self.reader.start()

    def updated(self, row: BarRow):
        self.queue.send(data=row)

    def _read_queue(self):
        while self.alive:
            for value in self.queue.receive():
                if value is None:
                    continue
                match value:
                    case Packet(data=BarRow() as row):
                        self.multi.update_row(row.snap())
                    case _:
                        continue

            time.sleep(1 / self.fps)

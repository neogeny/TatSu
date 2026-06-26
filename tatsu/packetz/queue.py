# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sys
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import IO, Any

from ..util import alpha_timestamp
from .packet import (
    BadPacketError,
    Packet,
    PacketHashError,
    PacketLike,
    pack,
    unpack,
)


PACKETZ_DIR = Path(f"./.{__name__.split('.')[-2]}")


def new_file_path() -> Path:
    return PACKETZ_DIR / f"{alpha_timestamp()}.pktz.jsonl"


class PacketzQueue:
    """File-backed packet queue.

    Instantiate with a path, or let it generate a timestamped file
    under ``.packetz/``.
    """

    path: Path = Path("/dev/null")
    _told: int = 0
    _seen: dict[str, PacketLike] = {}  # noqa: RUF012
    _queue: IO[str] | None = None

    def __init__(self, path: Path | str | None = None):
        if path is None:
            path = new_file_path()
        self.path = Path(path)

        PACKETZ_DIR.mkdir(parents=True, exist_ok=True)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self.path.touch(exist_ok=True)
            self._told = 0

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        state["_queue"] = None  # Force re-opening on the other side
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)

    def _queue_healthy(self) -> bool:
        q = self._queue
        if q is sys.stdin or q is sys.stdout:
            return False
        if q is None or q.closed:
            return False
        return os.fstat(q.fileno()).st_nlink > 0

    def _ensure_open(self) -> None:
        if self._queue_healthy():
            return
        self._queue = self.path.open(
            "rt",
            encoding="utf-8",
            buffering=32 * 1024,
        )
        self.reset()

    def get_queue(self) -> IO[str]:
        self._ensure_open()
        assert self._queue is not None
        return self._queue

    def tell(self, check: bool = True) -> None:
        assert self._queue is not None
        t = self._queue.tell()
        assert (check and t > self._told) or (not check and t >= self._told)
        self._told = t

    def reset(self):
        if self._queue:
            self._queue.seek(self._told)

    @contextlib.contextmanager
    def reader(self) -> Generator[IO[str], None, None]:
        q = self.get_queue()
        q.seek(self._told)
        try:
            yield q
        finally:
            self.tell(False)

    @contextlib.contextmanager
    def writer(self) -> Generator[IO[str], None, None]:
        with self.path.open("at", encoding="utf-8", buffering=1) as queue:
            yield queue

    def send(self, *, to: str | None = None, data: Any = None) -> PacketLike:
        packet = Packet(to=to, data=data)
        serial = pack(packet)
        with self.writer() as queue:
            queue.write(serial + "\n")
        return packet

    def receive(self) -> Generator[PacketLike, None, None]:
        with self.reader() as queue:
            for serial in queue.readlines():
                try:
                    packet = unpack(serial)
                except (BadPacketError, json.JSONDecodeError, TypeError):
                    break  # NOTE Incomplete? Wait and retry
                except (PacketHashError, ValueError):
                    continue  # NOTE Skip and continue!
                if packet.id in self._seen:
                    continue
                self._seen[packet.id] = packet
                yield packet
            self.tell(False)

    async def receive_async(self) -> AsyncGenerator[PacketLike, None]:
        try:
            while True:
                for msg in self.receive():
                    yield msg
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:  # noqa: TRY203
            raise

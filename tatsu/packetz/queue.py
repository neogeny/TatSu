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

from tatsu.util.fromjson import JSONBase

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


class PacketzQueue(JSONBase):
    """File-backed packet queue.

    Instantiate with a path, or let it generate a timestamped file
    under ``.packetz/``.
    """

    def __init__(self, path: Path | str | None = None):
        if path is None:
            path = new_file_path()
        self.path = Path(path)

        PACKETZ_DIR.mkdir(parents=True, exist_ok=True)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self.path.touch(exist_ok=True)
        self._told = 0
        self._seen: set[str] = set()

    def _queue_healthy(self, q: IO[str] | None) -> bool:
        if q is sys.stdin or q is sys.stdout:
            return False
        if q is None or q.closed:
            return False
        return os.fstat(q.fileno()).st_nlink > 0

    def _ensure_open(self) -> IO[str]:
        q = self.path.open(
            "rt",
            encoding="utf-8",
            buffering=1024 * 256,
        )
        assert self._queue_healthy(q)
        return q

    def _get_queue(self) -> IO[str]:
        return self._ensure_open()

    def tell(self, q: IO[str], check: bool = True) -> None:
        t = q.tell()
        assert (check and t > self._told) or (not check and t >= self._told)
        self._told = t

    @contextlib.contextmanager
    def reader(self) -> Generator[IO[str], None, None]:
        with self._get_queue() as q:
            try:
                q.seek(self._told)
                yield q
            finally:
                self.tell(q, False)

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
            lines = queue.readlines()
        for serial in lines:
            try:
                packet = unpack(serial)
            except (BadPacketError, json.JSONDecodeError, TypeError):
                continue  # NOTE Incomplete? Wait and retry
            except (PacketHashError, ValueError):
                continue  # NOTE Skip and continue!
            if packet.id in self._seen:
                continue
            self._seen.add(packet.id)
            yield packet

    async def receive_async(self) -> AsyncGenerator[PacketLike, None]:
        try:
            while True:
                for msg in self.receive():
                    yield msg
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:  # noqa: TRY203
            raise

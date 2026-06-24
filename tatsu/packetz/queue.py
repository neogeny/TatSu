# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import asyncio
import contextlib
import json
import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import IO, Any, ClassVar

from ..util import alpha_timestamp
from .packet import Packet, PacketLike, pack, unpack


class QueueState:
    """Encapsulates the shared file-backed queue state.

    Class variables serve as the module-level singleton state, accessible
    from all processes (or within a single process) that import this module.
    """

    path: ClassVar[Path] = Path(f"./{__name__.split('.')[-2]}.jsonl")
    _queue: ClassVar[IO[str] | None] = None
    _told: ClassVar[int] = 0
    _seen: ClassVar[dict[str, PacketLike]] = {}

    @staticmethod
    def new_queue_file_name() -> str:
        name = __name__.split('.')[-2]
        dir = f"./.{name}"
        Path(dir).mkdir(parents=True, exist_ok=True)
        return f"{dir}/{alpha_timestamp()}.pktz.jsonl"

    @classmethod
    def init(cls) -> None:
        if cls.is_queue_healthy():
            return

        if cls.path.is_file():
            cls._queue = cls.path.open(
                "rt+",
                encoding="utf-8",
                buffering=32 * 1024,
            )
            cls._queue.seek(cls._told)
            return

        name = __name__.split('.')[-2]
        dir = f"./.{name}"
        Path(dir).mkdir(parents=True, exist_ok=True)

        # NOTE A totally new file
        cls.path = Path(cls.new_queue_file_name())
        with cls.path.open("w+", encoding="utf-8") as _q:
            cls._told = 0

    @classmethod
    def is_queue_healthy(cls) -> bool:
        """Return whether the queue is healthy (i.e., not closed or deleted)."""
        q = cls._queue
        return q is not None and not q.closed and os.fstat(q.fileno()).st_nlink > 0

    @classmethod
    def get_queue(cls) -> IO[str]:
        """Return the read handle if healthy, raise otherwise."""
        if not cls.is_queue_healthy():
            cls.init()
        assert cls._queue is not None
        return cls._queue

    @classmethod
    def tell(cls, check: bool = True) -> None:
        """Mark the current read position in the queue."""
        q = cls._queue
        assert q is not None
        t = q.tell()
        assert (check and t > cls._told) or (not check and t >= cls._told)
        cls._told = t

    @classmethod
    @contextlib.contextmanager
    def reader(cls) -> Generator[IO[str], None, None]:
        """Context manager for the read handle, initializing if necessary."""
        q = cls.get_queue()
        try:
            yield q
        finally:
            cls.tell(False)

    @classmethod
    @contextlib.contextmanager
    def writer(cls) -> Generator[IO[str], None, None]:
        """Context manager for the write handle, initializing if necessary."""
        with cls.path.open("at", encoding="utf-8", buffering=1) as queue:
            yield queue

    @classmethod
    def send(cls, *, to: str | None = None, data: Any = None) -> PacketLike:
        """Push a packet onto the shared process-safe queue."""
        packet = Packet(to=to, data=data)
        serial = pack(packet)
        with cls.writer() as queue:
            queue.write(serial + "\n")
        return packet

    @classmethod
    def receive(cls) -> Generator[PacketLike, None, None]:
        """Drain all currently available packets from the queue."""
        with cls.reader() as queue:
            for serial in queue.readlines():
                try:
                    packet = unpack(serial)
                except (json.JSONDecodeError, TypeError):
                    break  # NOTE Assume incomplete line???
                except ValueError:
                    continue
                cls.tell(False)
                if packet.id in cls._seen:
                    continue
                cls._seen[packet.id] = packet
                yield packet

    @classmethod
    async def receive_async(cls) -> AsyncGenerator[PacketLike, None]:
        """Drain available packets in bursts, yielding control to the event loop when empty."""
        try:
            while True:
                for msg in cls.receive():
                    yield msg
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:  # noqa: TRY203
            raise

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Process-safe packet queue for cross-worker communication.

Defines a Packet protocol, a default dataclass implementation, and
sync/async receivers for draining a multiprocessing.Queue.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any, ClassVar, TextIO

from ..util.asjson import AsJSONMixin, asjson
from ..util.fromjson import JSONBase, fromjson
from ..util.misc import new_id


# -- Packet types ------------------------------------------------------------


class HasID(AsJSONMixin):
    id: str


class PacketLike(HasID):
    to: str | None
    data: Any


class WithID(HasID, JSONBase):
    id: str = "0xBAAD"

    def __new__(cls, *args, **kwargs):
        new = super().__new__(cls)
        new.id = new_id()
        return new


class Packet(PacketLike, WithID):
    to: str | None = None
    data: Any = None

    def __init__(self, /, *, to: str | None = None, data: Any = None):
        if to is not None:
            self.to = to
        if data is not None:
            self.data = data


class PacketQueueState:
    """Encapsulates the shared file-backed queue state.

    Class variables serve as the module-level singleton state, accessible
    from all processes (or within a single process) that import this module.
    """

    path: ClassVar[Path] = Path(f"./{__name__.split('.')[-1]}.jsonl")
    _queue: ClassVar[TextIO | None] = None
    _told: ClassVar[int] = 0
    _seen: ClassVar[dict[str, PacketLike]] = {}

    # -- lifecycle -----------------------------------------------------------

    @classmethod
    def init(cls) -> None:
        if cls._queue is None:
            # NOTE Erase the file
            with cls.path.open("w+", encoding="utf-8") as _f:
                cls._told = 0
            cls.path.touch()
        cls._queue = cls.path.open(
            "rt",
            encoding="utf-8",
            buffering=32 * 1024,
        )
        cls._queue.seek(cls._told)

    # -- file-handle health --------------------------------------------------

    @classmethod
    def get_queue(cls) -> TextIO:
        """Return the read handle if healthy, raise otherwise."""
        q = cls._queue
        if q is None or q.closed or os.fstat(q.fileno()).st_nlink == 0:
            cls.init()
            q = cls._queue
        assert q is not None
        return q

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
    def reader(cls) -> Generator[TextIO, None, None]:
        """Context manager for the read handle, initializing if necessary."""
        q = cls.get_queue()
        try:
            yield q
        finally:
            cls.tell(False)

    # -- send / receive ------------------------------------------------------

    @classmethod
    def send(cls, *, to: str | None = None, data: Any = None) -> PacketLike:
        """Push a packet onto the shared process-safe queue."""
        packet = Packet(to=to, data=data)
        serial = pack(packet)
        with cls.path.open("at", encoding="utf-8", buffering=1) as queue:
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


# -- Initialise the queue at import time -------------------------------------

PacketQueueState.init()

# -- Backward-compatible module-level aliases with full typing ---------------

PACKETZ_QUEUE: Path = PacketQueueState.path


def send(*, to: str | None = None, data: Any = None) -> PacketLike:
    return PacketQueueState.send(to=to, data=data)


def receive() -> Generator[PacketLike, None, None]:
    return PacketQueueState.receive()


async def receive_async() -> AsyncGenerator[PacketLike, None]:
    async for pkt in PacketQueueState.receive_async():
        yield pkt


# -- Wire transforms ---------------------------------------------------------


def tty_escape(s: str) -> str:
    return s.replace('\\u001b', '\\e')


def tty_unescape(s: str) -> str:
    return s.replace('\\e', '\\u001b')


def class_escape(s: str) -> str:
    return s.replace(r'{"__class__":', '{"@":')


def class_unescape(s: str) -> str:
    return s.replace(r'{"@":', r'{"__class__":')


def pack(packet: PacketLike) -> str:
    value = asjson(packet)
    serial = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    escaped = tty_escape(serial)
    return class_escape(escaped)


def unpack(serial: str) -> PacketLike:
    escaped = class_unescape(serial)
    serial = tty_unescape(escaped)
    value = json.loads(serial)
    packet = fromjson(value)
    return packet

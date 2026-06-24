# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import json
from typing import Any

from ..util.asjson import AsJSONMixin, asjson
from ..util.debugging import WARNING_print
from ..util.fromjson import JSONBase, fromjson
from ..util.misc import hash_2str, new_id
from .compact import compact_value, decompact_value


class HasID(AsJSONMixin):
    id: str


class PacketLike(HasID):
    to: str | None
    data: Any
    hash: str


class WithID(HasID, JSONBase):
    id: str = "0xBAAD"

    def __new__(cls, *_args, **_kwargs):
        new = super().__new__(cls)
        new.id = new_id()
        return new


class Packet(PacketLike, WithID):
    to: str | None = None
    data: Any = None
    hash: str = ""

    def __init__(self, /, *, to: str | None = None, data: Any = None):
        if to is not None:
            self.to = to
        if data is not None:
            self.data = data


def validate(expected: str, actual: str) -> bool:
    if expected != actual:
        WARNING_print(f"checksum mismatch: {expected} != {actual}")
        raise RuntimeError("checksum mismatch")
        return False
    return True


def pack(packet: PacketLike) -> str:
    value = asjson(packet)
    compact = compact_value(value)
    compact["hash"] = hash_2str(value)
    serial = json.dumps(compact, separators=(",", ":"), ensure_ascii=False)
    escaped = tty_escape(serial)
    return class_escape(escaped)


def unpack(serial: str) -> PacketLike:
    escaped = class_unescape(serial)
    serial = tty_unescape(escaped)
    compact = json.loads(serial)
    _expected_hash = compact["hash"]
    value = decompact_value(compact)
    _actual_hash = hash_2str(value)
    # validate(_expected_hash, _actual_hash)
    packet = fromjson(value)
    return packet


def tty_escape(s: str) -> str:
    return s.replace('\\u001b', '\\e')


def tty_unescape(s: str) -> str:
    return s.replace('\\e', '\\u001b')


def class_escape(s: str) -> str:
    return s.replace(r'{"__class__":', '{"@":')


def class_unescape(s: str) -> str:
    return s.replace(r'{"@":', r'{"__class__":')

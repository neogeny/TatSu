# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""Approximate benchmarks for the file-backed packet queue.

Runs with ``python -m tatsu.parproc.test_packetz``.
Also compatible with ``pytest`` if available.
"""

from __future__ import annotations

import gc
import time
from pathlib import Path
from typing import Any

from . import api


QUEUE = Path(api.PACKETZ_QUEUE)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _cleanup():
    import importlib
    import sys

    global api  # noqa: PLW0602, PLW0603
    api.PACKETZ_QUEUE.unlink(missing_ok=True)
    del sys.modules["tatsu.parproc.packetz"]
    importlib.import_module("tatsu.parproc.packetz")
    from . import api  # noqa: F811

    gc.collect()


def _make_payload(n: int) -> str:
    if n == 0:
        return ""
    chunk = "The quick brown fox jumps over the lazy dog. " * ((n // 44) + 1)
    return chunk[:n]


_SENTINEL = object()


def _write_batch(n: int, payload: Any = _SENTINEL) -> tuple[float, int]:
    start = time.perf_counter()
    for _ in range(n):
        if payload is _SENTINEL:
            api.send()
        else:
            api.send(data=payload)
    elapsed = time.perf_counter() - start
    size = QUEUE.stat().st_size
    return elapsed, size


def _read_all() -> tuple[list[api.PacketLike], float]:
    start = time.perf_counter()
    packets = list(api.receive())
    elapsed = time.perf_counter() - start
    return packets, elapsed


# ---------------------------------------------------------------------------
# benchmark cases
# ---------------------------------------------------------------------------


def bench_write_small():
    _cleanup()
    for n in (1, 10, 100, 1000):
        elapsed, size = _write_batch(n)
        rate = f"{n / elapsed:.0f}/s" if elapsed else "∞"
        print(f"  write {n:>5} pkts  {elapsed:.3f}s  {rate:>8}  file={size:,}B")


def bench_write_payload_size():
    _cleanup()
    n = 100
    for label, kb in (("empty", 0), ("1KB", 1), ("10KB", 10), ("100KB", 100)):
        payload = _make_payload(kb * 1024)
        elapsed, size = _write_batch(n, payload=payload)
        rate = f"{n / elapsed:.0f}/s" if elapsed else "∞"
        print(f"  {label:>6}  {n:>3} pkts  {elapsed:.3f}s  {rate:>8}  file={size:,}B")
        _cleanup()


def bench_read():
    for label, n in (
        ("1 pkt", 1),
        ("10 pkts", 10),
        ("100 pkts", 100),
        ("1000 pkts", 1000),
    ):
        _cleanup()
        _write_batch(n, payload=_make_payload(256))
        _packets, elapsed = _read_all()
        rate = f"{n / elapsed:.0f}/s" if elapsed else "∞"
        print(f"  read {label:>10}  {elapsed:.4f}s  {rate:>8}")


def bench_growth_penalty():
    _cleanup()
    payload = _make_payload(256)
    for round_ in range(4):
        _write_batch(500, payload=payload)
        packets, elapsed = _read_all()
        size = QUEUE.stat().st_size
        rate = f"{len(packets) / elapsed:.0f}/s" if elapsed else "∞"
        print(
            f"  growth round {round_}: file={size:,}B  read {len(packets)} pkts @ {rate}"
        )


def bench_round_trip():
    _cleanup()
    payloads = [
        None,
        "",
        42,
        3.14,
        "hello world",
        _make_payload(1024),
        {"nested": ["list", {"key": "value"}]},
    ]
    sent_ids = []
    for p in payloads:
        pkt = api.send(data=p, to="bench")
        sent_ids.append(pkt.id)
    packets, elapsed = _read_all()
    ok = [p.id for p in packets] == sent_ids
    print(
        f"  sent {len(sent_ids)} pkts, received {len(packets)} in {elapsed:.3f}s  ids_match={ok}"
    )


def bench_dedup():
    _cleanup()
    from .packet import Packet, pack

    pkt = Packet(data="dedup-test", to="check")
    raw = pack(pkt) + "\n"
    for _ in range(2):
        with QUEUE.open("at", encoding="utf-8") as f:
            f.write(raw)
    packets, elapsed = _read_all()
    ok = len(packets) == 1
    print(
        f"  wrote 2 identical lines, got {len(packets)} unique ({'PASS' if ok else 'FAIL'}) in {elapsed:.3f}s"
    )


def bench_transforms_wire_size():
    """Compare wire size: raw JSON vs. current pack() transforms."""
    _cleanup()
    import json

    from ..util.asjson import asjson
    from .packet import Packet, pack

    pkt = Packet(data=_make_payload(256), to="size-test")
    raw = json.dumps(asjson(pkt), separators=(",", ":"), ensure_ascii=False)
    cooked = pack(pkt)
    ratio = f"{len(cooked) / len(raw) * 100:.0f}%" if raw else "N/A"
    print(f"  raw JSON        {len(raw):>6}B")
    print(f"  after pack()    {len(cooked):>6}B  ({ratio})")


def bench_bloat():
    _cleanup()
    cases = [
        ("empty", ""),
        ("5KB_text", "x" * 5000),
        ("5KB_spaces", " " * 5000),
        ("4KB_repeat", "x y z " * 1000),
    ]
    n = 100
    for label, payload in cases:
        _elapsed, size = _write_batch(n, payload=payload)
        raw_data_size = n * (len(payload) if payload else 0)
        ratio = f"{size / max(raw_data_size, 1):.1f}x"
        print(
            f"  {label:>12}  {n:>3} pkts  wire={size:,}B  raw-data={raw_data_size:,}B  bloat={ratio}"
        )
        _cleanup()


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------


def main():
    BENCHMARKS = [
        ("Write throughput (small payload)", bench_write_small),
        ("Write throughput (varying payload size)", bench_write_payload_size),
        ("Read throughput", bench_read),
        ("Queue growth penalty", bench_growth_penalty),
        ("Round-trip value fidelity", bench_round_trip),
        ("Duplicate dedup", bench_dedup),
        ("Serialization transforms wire size", bench_transforms_wire_size),
        ("Serialization bloat factor", bench_bloat),
    ]
    print(f"packetz queue: {api.PACKETZ_QUEUE}")
    print()
    for title, fn in BENCHMARKS:
        print(f"[{title}]")
        try:
            fn()
        except Exception as e:
            print(f"  ERROR: {e}")
        print()


if __name__ == "__main__":
    main()

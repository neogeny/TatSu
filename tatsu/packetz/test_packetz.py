# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""Approximate benchmarks for the file-backed packet queue.

Runs with ``python -m tatsu.packetz.test_packetz``.
Also compatible with ``pytest`` if available.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .packet import Packet, PacketLike, pack
from .queue import QueueState


QUEUE_PATH = Path("test_packetz.jsonl")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _new_queue():
    QUEUE_PATH.unlink(missing_ok=True)
    return QueueState(path=QUEUE_PATH)


def _make_payload(n: int) -> str:
    if n == 0:
        return ""
    chunk = "The quick brown fox jumps over the lazy dog. " * ((n // 44) + 1)
    return chunk[:n]


_SENTINEL = object()


def _write_batch(q: QueueState, n: int, payload: Any = _SENTINEL) -> tuple[float, int]:
    start = time.perf_counter()
    for _ in range(n):
        if payload is _SENTINEL:
            q.send()
        else:
            q.send(data=payload)
    elapsed = time.perf_counter() - start
    size = QUEUE_PATH.stat().st_size
    return elapsed, size


def _read_all(q: QueueState) -> tuple[list[PacketLike], float]:
    start = time.perf_counter()
    packets = list(q.receive())
    elapsed = time.perf_counter() - start
    return packets, elapsed


# ---------------------------------------------------------------------------
# benchmark cases
# ---------------------------------------------------------------------------


def bench_write_small():
    q = _new_queue()
    for n in (1, 10, 100, 1000):
        elapsed, size = _write_batch(q, n)
        rate = f"{n / elapsed:.0f}/s" if elapsed else "∞"
        print(f"  write {n:>5} pkts  {elapsed:.3f}s  {rate:>8}  file={size:,}B")


def bench_write_payload_size():
    n = 100
    for label, kb in (("empty", 0), ("1KB", 1), ("10KB", 10), ("100KB", 100)):
        q = _new_queue()
        payload = _make_payload(kb * 1024)
        elapsed, size = _write_batch(q, n, payload=payload)
        rate = f"{n / elapsed:.0f}/s" if elapsed else "∞"
        print(f"  {label:>6}  {n:>3} pkts  {elapsed:.3f}s  {rate:>8}  file={size:,}B")


def bench_read():
    for label, n in (
        ("1 pkt", 1),
        ("10 pkts", 10),
        ("100 pkts", 100),
        ("1000 pkts", 1000),
    ):
        q = _new_queue()
        _write_batch(q, n, payload=_make_payload(256))
        _packets, elapsed = _read_all(q)
        rate = f"{n / elapsed:.0f}/s" if elapsed else "∞"
        print(f"  read {label:>10}  {elapsed:.4f}s  {rate:>8}")


def bench_growth_penalty():
    q = _new_queue()
    payload = _make_payload(256)
    for round_ in range(4):
        _write_batch(q, 500, payload=payload)
        packets, elapsed = _read_all(q)
        size = QUEUE_PATH.stat().st_size
        rate = f"{len(packets) / elapsed:.0f}/s" if elapsed else "∞"
        print(
            f"  growth round {round_}: file={size:,}B  read {len(packets)} pkts @ {rate}"
        )


def bench_round_trip():
    q = _new_queue()
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
        pkt = q.send(data=p, to="bench")
        sent_ids.append(pkt.id)
    packets, elapsed = _read_all(q)
    ok = [p.id for p in packets] == sent_ids
    print(
        f"  sent {len(sent_ids)} pkts, received {len(packets)} in {elapsed:.3f}s  ids_match={ok}"
    )


def bench_dedup():
    q = _new_queue()
    pkt = Packet(data="dedup-test", to="check")
    raw = pack(pkt) + "\n"
    for _ in range(2):
        with QUEUE_PATH.open("at", encoding="utf-8") as f:
            f.write(raw)
    packets, elapsed = _read_all(q)
    ok = len(packets) == 1
    print(
        f"  wrote 2 identical lines, got {len(packets)} unique ({'PASS' if ok else 'FAIL'}) in {elapsed:.3f}s"
    )


def bench_transforms_wire_size():
    """Compare wire size: raw JSON vs. current pack() transforms."""
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
    cases = [
        ("empty", ""),
        ("5KB_text", "x" * 5000),
        ("5KB_spaces", " " * 5000),
        ("4KB_repeat", "x y z " * 1000),
    ]
    n = 100
    for label, payload in cases:
        q = _new_queue()
        _elapsed, size = _write_batch(q, n, payload=payload)
        raw_data_size = n * (len(payload) if payload else 0)
        ratio = f"{size / max(raw_data_size, 1):.1f}x"
        print(
            f"  {label:>12}  {n:>3} pkts  wire={size:,}B  raw-data={raw_data_size:,}B  bloat={ratio}"
        )


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
    print(f"packetz queue: {QUEUE_PATH}")
    print()
    for title, fn in BENCHMARKS:
        print(f"[{title}]")
        try:
            fn()
        except Exception as e:
            print(f"  ERROR: {e}")
        print()
    # cleanup
    QUEUE_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

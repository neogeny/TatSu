# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import sysconfig
import time
from collections.abc import Callable, Iterable
from itertools import batched
from pickle import PickleError, PicklingError
from typing import Any

from . import packetz
from .packetz import Packet
from .task import Event, Func


GIL_DISABLED = sysconfig.get_config_var("Py_GIL_DISABLED")
HAS_MULTITHREADING_SUPPORT = GIL_DISABLED


def active_pmap() -> Callable[
    [Event, Func, Iterable[Any], int | None], Iterable[Packet]
]:
    import multiprocessing
    from concurrent.futures import (
        Executor,
        # NOTE from Python 3.14 onwards
        ProcessPoolExecutor,
        ThreadPoolExecutor,
    )

    def executor_pmap(
        executorcls: type[Executor],
        stop_event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[Packet]:
        # by Copilot 2026-03-06

        if not tasks:
            return

        for batch in batched(tasks, 8):
            yield from packetz.receive()
            with executorcls(max_workers=max_workers) as ex:  # type: ignore
                try:
                    futures = [ex.submit(process, task) for task in batch]
                    while futures:
                        yield from packetz.receive()
                        finished = [f for f in futures if f.done()]
                        for f in finished:
                            futures.remove(f)
                            yield f.result()
                        if futures:
                            time.sleep(0.01)
                    yield from packetz.receive()
                    # futures = [ex.submit(process, task) for task in tasks]
                    # yield from packetz.receive()
                    # for future in as_completed(futures):
                    #     yield from packetz.receive()
                    #     yield future.result()
                except KeyboardInterrupt:
                    stop_event.set()

                    print(file=sys.stderr)
                    print(file=sys.stderr)
                    print("Wait...", file=sys.stderr)
                    sys.stderr.flush()

                    ex.shutdown(wait=False, cancel_futures=True)

                    print("           ", end="\r", file=sys.stderr)
                    sys.stderr.flush()

                    raise
        yield from packetz.receive()

    def thread_pmap(
        event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[Packet]:
        yield from executor_pmap(
            ThreadPoolExecutor,
            event,
            process,
            tasks,
            max_workers=max_workers or multiprocessing.cpu_count(),
        )

    def process_pmap(
        event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[Packet]:
        try:
            yield from executor_pmap(
                ProcessPoolExecutor,
                event,
                process,
                tasks,
                max_workers=max_workers or multiprocessing.cpu_count(),
            )
        except (TypeError, PicklingError, PickleError):
            raise
            # yield from thread_pmap(event, process, tasks, max_workers)
        except KeyboardInterrupt:
            return

    if sys.version_info >= (3, 14):
        from concurrent.futures import (
            InterpreterPoolExecutor,  # pyright: ignore[reportAttributeAccessIssue]
        )

        def interpreter_pmap(
            event: Event,
            process: Func,
            tasks: Iterable[Any],
            max_workers: int | None = None,
        ) -> Iterable[Packet]:
            try:
                yield from executor_pmap(
                    InterpreterPoolExecutor,
                    event,
                    process,
                    tasks,
                    max_workers=max_workers or multiprocessing.cpu_count(),
                )
            except (TypeError, PicklingError, PickleError):
                yield from thread_pmap(event, process, tasks, max_workers)

    def imap_pmap(process: Func, tasks: Iterable[Any]) -> Iterable[Packet]:
        tasks = list(tasks)
        nworkers = 4 * max(1, multiprocessing.cpu_count())

        n = nworkers * 4
        chunks = batched(tasks, n)

        count = 0
        with multiprocessing.Pool(processes=nworkers) as pool:
            for chunk in chunks:
                count += len(chunk)
                yield from pool.imap_unordered(process, chunk)
        if len(tasks) != count:
            raise RuntimeError(
                'number of chunked tasks different %d != %d' % (len(tasks), count),
            )

    if HAS_MULTITHREADING_SUPPORT:
        return thread_pmap
    # return thread_pmap
    return process_pmap

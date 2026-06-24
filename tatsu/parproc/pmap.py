# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import sysconfig
from collections.abc import Callable, Iterable
from pickle import PickleError, PicklingError
from typing import Any

from ..packetz import PacketLike, QueueState
from .task import Event, Func


GIL_DISABLED = sysconfig.get_config_var("Py_GIL_DISABLED")
HAS_MULTITHREADING_SUPPORT = GIL_DISABLED


def active_pmap() -> Callable[
    [QueueState, Event, Func, Iterable[Any], int | None], Iterable[PacketLike]
]:
    import multiprocessing
    from concurrent.futures import (
        Executor,
        ProcessPoolExecutor,
        ThreadPoolExecutor,
    )

    def executor_pmap(
        executorcls: type[Executor],
        queue: QueueState,
        stop_event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[PacketLike]:
        # by Copilot 2026-03-06

        if not tasks:
            return

        yield from queue.receive()
        with executorcls(max_workers=max_workers) as ex:  # type: ignore
            # with executorcls(None) as ex:  # type: ignore
            try:
                futures = [ex.submit(process, task) for task in tasks]
                while futures:
                    yield from queue.receive()
                    finished = {f for f in futures if f.done()}
                    for f in finished:
                        futures.remove(f)
                        yield f.result()
                        yield from queue.receive()
                        finished = {f for f in futures if f.done()}
                    # if futures:
                    #     time.sleep(0.01)
                # yield from packetz.receive()
                # for future in as_completed(futures):
                #     yield from packetz.receive()
                #     yield future.result()
                #     yield from packetz.receive()
                yield from queue.receive()
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
        yield from queue.receive()

    def thread_pmap(
        queue: QueueState,
        event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[PacketLike]:
        yield from executor_pmap(
            ThreadPoolExecutor,
            queue,
            event,
            process,
            tasks,
            max_workers=max_workers or multiprocessing.cpu_count(),
        )

    def process_pmap(
        queue: QueueState,
        event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[PacketLike]:
        try:
            yield from executor_pmap(
                ProcessPoolExecutor,
                queue,
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
        ) -> Iterable[PacketLike]:
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

    def imap_pmap(process: Func, tasks: Iterable[Any]) -> Iterable[PacketLike]:
        tasks = list(tasks)
        nworkers = 4 * max(1, multiprocessing.cpu_count())

        count = len(tasks)
        with multiprocessing.Pool(processes=nworkers) as pool:
            yield from pool.imap_unordered(process, tasks)
        if len(tasks) != count:
            raise RuntimeError(
                'number of chunked tasks different %d != %d' % (len(tasks), count),
            )

    if HAS_MULTITHREADING_SUPPORT:
        return thread_pmap
    # return thread_pmap
    return process_pmap

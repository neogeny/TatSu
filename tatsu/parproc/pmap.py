# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import sysconfig
from collections.abc import Callable, Iterable
from concurrent.futures import as_completed
from itertools import islice
from pickle import PickleError, PicklingError
from typing import Any

from .result import Result
from .task import Event, Func


GIL_DISABLED = sysconfig.get_config_var("Py_GIL_DISABLED")
HAS_MULTITHREADING_SUPPORT = GIL_DISABLED


def active_pmap() -> Callable[
    [Event, Func, Iterable[Any], int | None], Iterable[Result]
]:
    import multiprocessing
    from concurrent.futures import (
        Executor,
        ProcessPoolExecutor,
        ThreadPoolExecutor,
    )

    def executor_pmap(
        executorcls: type[Executor],
        stop_event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[Result]:
        # by Copilot 2026-03-06

        if not tasks:
            return

        with executorcls(max_workers=max_workers) as ex:  # type: ignore
            # with executorcls(None) as ex:  # type: ignore
            try:
                n = 8
                taskiter = iter(tasks)
                futures = {
                    ex.submit(process, task): task for task in islice(taskiter, n)
                }
                while futures:
                    for future in as_completed(futures):
                        yield future.result()
                        _task = futures.pop(future)
                        for task in islice(taskiter, 1):
                            new_future = ex.submit(process, task)
                            futures[new_future] = task
                # while futures:
                #     finished = {f for f in futures if f.done()}
                #     for f in finished:
                #         futures.remove(f)
                #         yield f.result()
                #         finished = {f for f in futures if f.done()}
                # if futures:
                #     time.sleep(0.01)
                # yield from packetz.receive()
                # for future in as_completed(futures):
                #     yield from packetz.receive()
                #     yield future.result()
                #     yield from packetz.receive()
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

    def thread_pmap(
        event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[Result]:
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
    ) -> Iterable[Result]:
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
        ) -> Iterable[Result]:
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

    def imap_pmap(process: Func, tasks: Iterable[Any]) -> Iterable[Result]:
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
    return process_pmap

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from threading import Event
from typing import Any, NamedTuple

from ..packetz import api as _packetz_api
from ..packetz.queue import PacketzQueue
from ..util import memory_use
from .payload import VisualPayload
from .result import Result


type Func = Callable[..., Any]
type VisualFunc = Func


class TaskStop(Exception):
    pass


class Task(NamedTuple):
    queue: PacketzQueue
    stop: Event
    func: Func
    payload: Any
    pickable: Callable
    reraise: bool
    args: Iterable[Any]
    kwargs: Mapping[str, Any]


def taskproc(task: Task) -> Result:
    if task.stop.is_set():
        return Result(task.stop, task.payload)
    _packetz_api.init_queue(task.queue)

    result = Result(task.stop, task.payload)
    outcome: Any = None
    elapsed: float = 0.0
    prev_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(2**16)
    try:
        start_time = time.thread_time()
        try:
            outcome = task.func(task.payload, *task.args, **task.kwargs)
        except TypeError:
            if not isinstance(task.payload, VisualPayload):
                raise

            # HACK add backwards compatibility
            outcome = task.func(task.payload.path, *task.args, **task.kwargs)

        elapsed = time.thread_time() - start_time
    except RuntimeError:
        raise
    except (Exception, RecursionError) as e:
        result.exception = e
        if task.reraise or (
            (raises := task.payload.raises())
            and not any(isinstance(e, r) for r in raises)
        ):
            raise
    finally:
        sys.setrecursionlimit(prev_limit)
        result.runtime = elapsed
        result.outcome = task.pickable(outcome)
    result.linecount = getattr(outcome, 'linecount', 0)
    result.memory = memory_use()
    return result

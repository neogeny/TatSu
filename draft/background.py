# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import threading
from collections.abc import Generator
from contextlib import contextmanager


@contextmanager
def background() -> Generator[None, None, None]:
    """Executes the inner code block on a separate thread using shared memory.
    Guarantees thread cleanup and exception propagation."""

    thread_exception = []
    block_generator = yield

    def run_target():
        try:
            next(block_generator)
        except StopIteration:
            pass
        except Exception:
            thread_exception.append(sys.exc_info())

    worker = threading.Thread(target=run_target, daemon=True)
    worker.start()

    worker.join()
    if thread_exception:
        _exc_type, exc_val, exc_tb = thread_exception[0]
        raise exc_val.with_traceback(exc_tb)

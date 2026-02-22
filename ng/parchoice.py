# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any


# Sentinels/Signals
class OptionSucceeded(Exception):
    pass


class ChoiceContext:
    def __init__(self, ctx: Any, parallel: bool = False):
        self.ctx = ctx
        self.parallel: bool = parallel
        self.options: list[Callable[[], None]] = []
        self.expected: list[str] = []

    def option(self, func: Callable[[], None]) -> Callable[[], None]:
        """Decorator to register a grammar branch."""
        self.options.append(func)
        return func

    def expecting(self, *tokens: str) -> None:
        """Register tokens for error reporting if all options fail."""
        self.expected.extend(tokens)

    def _worker(self, opt: Callable[[], None]) -> None:
        """Isolated execution for a single option within a thread."""
        with self.ctx._option():
            opt()

    def run(self) -> None:
        """
        Orchestrates the execution of registered options.
        Dispatches to sequential or parallel implementations.
        """
        if not self.options:
            return

        if self.parallel:
            self._run_parallel()
        else:
            self._run_sequential()

        # If we reach here, no options succeeded.
        raise self.ctx.newexcept(f"Expected one of: {', '.join(self.expected)}")

    def _run_sequential(self) -> None:
        """Standard PEG backtracking: one option at a time."""
        for opt in self.options:
            with self.ctx._option():
                opt()

    def _run_parallel(self) -> None:
        """Concurrent execution: all options at once, resolved in order."""
        executor = ThreadPoolExecutor()
        try:
            # Dispatch all options to the pool immediately
            futures: list[Future] = [
                executor.submit(self._worker, opt)
                for opt in self.options
            ]

            # Iterate in registration order to preserve PEG semantics
            for future in futures:
                try:
                    # Re-raises OptionSucceeded, FailedParse, or unknown Errors
                    future.result()

                    # If the worker finished without raising a signal,
                    # we treat it as a success.
                    raise OptionSucceeded()

                except FailedParse:
                    # Expected failure: move to the next future in order
                    continue

                # OptionSucceeded and unknown exceptions escape the loop
                # and the try block, triggering the finally cleanup.
        finally:
            # Stop pending work and shut down resources immediately
            executor.shutdown(wait=False, cancel_futures=True)

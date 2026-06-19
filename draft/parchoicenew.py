# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import concurrent.futures
from collections.abc import Callable
from typing import Any


# Sentinels/Signals
class OptionSucceeded(Exception):
    pass


class FailedParse(Exception):
    pass


class ChoiceContext:
    def __init__(self, ctx: Any, parallel: bool = False):
        self.ctx = ctx
        self.parallel: bool = parallel
        self.options: list[Callable[[Any], None]] = []
        self.expected: list[str] = []

    def option(self, func: Callable[[Any], None]) -> Callable[[Any], None]:
        """Expression to register a grammar branch."""
        self.options.append(func)
        return func

    def expecting(self, *tokens: str) -> None:
        """Register tokens for error reporting if all options fail."""
        self.expected.extend(tokens)

    @staticmethod
    def _worker(ctx: Any, opt: Callable[[Any], None], ss: Any) -> Any:
        """
        Isolated execution for a single option.
        Returns the mutated 'ss' on success, or the Exception on failure.
        """
        try:
            # Note: Using ctx._option(ss) here to handle the state-push/pop
            # for the individual branch within the worker thread.
            with ctx._option(ss):
                opt(ss)
            return ss
        except Exception as e:
            return e

    def run(self, ss: Any) -> None:
        """
        Orchestrates the execution of registered options.
        Invoked automatically at the end of the 'with self._choice()' block.
        """
        if not self.options:
            return

        if self.parallel:
            self._run_parallel(ss)
        else:
            self._run_sequential(ss)

        # If we reach here, no options succeeded.
        raise self.ctx.newexcept(f"Expected one of: {', '.join(self.expected)}")

    def _run_sequential(self, ss: Any) -> None:
        """Standard PEG backtracking: one option at a time."""
        for opt in self.options:
            try:
                with self.ctx._option(ss):
                    opt(ss)
                raise OptionSucceeded()
            except FailedParse:
                continue

    def _run_parallel(self, ss: Any) -> None:
        """
        Concurrent execution using the shared engine executor.
        Resolves in registration order to preserve PEG priority.
        """
        executor: concurrent.futures.ThreadPoolExecutor = self.ctx.executor
        futures: list[concurrent.futures.Future] = []

        try:
            # 1. Dispatch branches with isolated state stacks
            for opt in self.options:
                futures.append(
                    executor.submit(self._worker, self.ctx, opt, ss.branch())
                )

            # 2. Resolve in registration order
            for future in futures:
                try:
                    result = future.result()

                    if isinstance(result, Exception):
                        raise result

                    # 3. Success: Merge worker progress into the main 'ss'
                    self.ctx.merge_state(ss, result)
                    raise OptionSucceeded()

                except FailedParse:
                    continue
                except (OptionSucceeded, Exception):
                    self._cancel_all(futures)
                    raise

        finally:
            self._cancel_all(futures)

    def _cancel_all(self, futures: list[concurrent.futures.Future]) -> None:
        """Stop pending work for this choice point."""
        for f in futures:
            if not f.done():
                f.cancel()

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any, Protocol

from ..config import ParserConfig
from ..exceptions import FailedLeftRecursion
from ..util import color, info
from ..util.unicode_characters import C_CUT, C_ENTRY, C_FAILURE, C_RECURSION, C_SUCCESS
from .ctx import Ctx


class EventColor(color.Color):
    def __init__(self):
        self.ENTRY = self.YELLOW + self.BRIGHT + C_ENTRY
        self.SUCCESS = self.GREEN + self.BRIGHT + C_SUCCESS
        self.FAILURE = self.RED + self.BRIGHT + C_FAILURE
        self.RECURSION = self.RED + self.BRIGHT + C_RECURSION
        self.CUT = self.MAGENTA + self.BRIGHT + C_CUT


C = EventColor()


class Tracer(Protocol):
    def trace(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    def trace_event(self, ctx: Ctx, event: str) -> None: ...

    def trace_entry(self, ctx: Ctx) -> None: ...

    def trace_success(self, ctx: Ctx) -> None: ...

    def trace_failure(self, ctx, ex: Exception | None = None) -> None: ...

    def trace_recursion(self, ctx: Ctx) -> None: ...

    def trace_cut(self, ctx: Ctx) -> None: ...

    def trace_match(
        self,
        ctx: Ctx,
        token: Any,
        name: str | None = None,
        failed: bool = False,
    ) -> None: ...

    def trace_no_match(
        self,
        ctx: Ctx,
        token: Any,
        name: str | None = None,
    ) -> None:
        self.trace_match(ctx, token, name=name, failed=True)

    def rulestack(self, ctx: Ctx) -> str: ...


class ConsoleTracer(Tracer):
    def __init__(
        self,
        *,
        config: ParserConfig | None = None,
        **settings: Any,
    ) -> None:
        self.config = ParserConfig.new(config, **settings)

        if self.config.colorize:
            color.init()
        global C  # noqa: PLW0603
        C = EventColor()

    def trace(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if not self.config.trace:
            return

        info(msg, *args, **kwargs)

    def trace_event(self, ctx: Ctx, event: str) -> None:
        if not self.config.trace:
            return

        cursor = ctx.cursor

        source = ''
        if self.config.trace_filename:
            source = cursor.lineinfo().source
        if source:
            source += '\n'

        lookahead = cursor.lookahead().rstrip()
        # lookahead = '\n' + lookahead if lookahead else ''

        pos = cursor.lookahead_pos()

        message = (
            f'{event}{self.rulestack(ctx)}'
            f' {C.DIM}{source}'
            # f'{C.RESET}'
            f'\n{pos}⇥{C.RESET_ALL}{lookahead}{C.RESET_ALL}'
        )
        self.trace(message)

    def trace_entry(self, ctx: Ctx) -> None:
        self.trace_event(ctx, f'{C.ENTRY}')

    def trace_success(self, ctx: Ctx) -> None:
        self.trace_event(ctx, f'{C.SUCCESS}')

    def trace_failure(self, ctx: Ctx, ex: Exception | None = None) -> None:
        if isinstance(ex, FailedLeftRecursion):
            self.trace_recursion(ctx)
        else:
            self.trace_event(ctx, f'{C.FAILURE}')

    def trace_recursion(self, ctx: Ctx) -> None:
        self.trace_event(ctx, f'{C.RECURSION}')

    def trace_cut(self, ctx: Ctx) -> None:
        self.trace_event(ctx, f'{C.CUT}')

    def trace_match(
        self,
        ctx: Ctx,
        token: Any,
        name: str | None = None,
        failed: bool = False,
    ) -> None:
        if not self.config.trace:
            return

        cursor = ctx.cursor

        name_str = f'/{name}/' if name else ''
        if self.config.trace_filename:
            source = cursor.lineinfo().source + '\n'
        else:
            source = ''

        mark = f'{C.FAILURE}' if failed else f'{C.SUCCESS}'

        lookahead = cursor.lookahead().rstrip()
        lookahead = '\n' + lookahead if lookahead else lookahead

        message = (
            f'{mark}'
            f"'{token}{name_str}"
            f'{C.DIM}{source}'
            f'{C.RESET_ALL}{lookahead}{C.RESET_ALL}'
        )
        self.trace(message)

    def rulestack(self, ctx: Ctx) -> str:
        ruleinfos = ctx.callstack
        rulestack = [f'{r.name}' for r in reversed(ruleinfos)]
        stack = self.config.trace_separator.join(rulestack)
        if (
            max((len(s) for s in stack.splitlines()), default=0)
            > self.config.trace_length
        ):
            stack = stack[: self.config.trace_length]
            stack = stack.rsplit(self.config.trace_separator, 1)[0]
            stack += self.config.trace_separator
        return stack


class NullTracer(Tracer):
    def trace(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass

    def trace_event(self, ctx: Ctx, event: str) -> None:
        pass

    def trace_entry(self, ctx: Ctx) -> None:
        pass

    def trace_success(self, ctx: Ctx) -> None:
        pass

    def trace_failure(self, ctx: Ctx, ex: Exception | None = None) -> None:
        pass

    def trace_recursion(self, ctx: Ctx) -> None:
        pass

    def trace_cut(self, ctx: Ctx) -> None:
        pass

    def trace_match(
        self,
        ctx: Ctx,
        token: Any,
        name: str | None = None,
        failed: bool = False,
    ) -> None:
        pass

    def rulestack(self, ctx) -> str:
        return ""

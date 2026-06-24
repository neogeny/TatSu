# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any, Protocol

from ..config import ParserConfig
from ..exceptions import FailedLeftRecursion
from ..util.common import is_posix
from ..util.debugging import INFO_print
from ..ztyle import Color, Style
from .ctx import Ctx


if not is_posix():
    C_ENTRY = '<'
    C_SUCCESS = '>'
    C_FAILURE = '!'
    C_RECURSION = 'r '
    C_CUT = '~'
else:
    C_ENTRY = '↙'
    C_SUCCESS = '≡'
    C_FAILURE = '≢'
    C_RECURSION = '⟲\u2005'
    C_CUT = '⚔'


class EventColor:
    def __init__(self, color: Color | None = None):
        if color is None:
            color = Color.tty()
        self.entry = Style(C_ENTRY, bold=True, fg=3, color=color)
        self.success = Style(C_SUCCESS, bold=True, fg=2, color=color)
        self.failure = Style(C_FAILURE, bold=True, fg=1, color=color)
        self.recursion = Style(C_RECURSION, bold=True, fg=1, color=color)
        self.cut = Style(C_CUT, bold=True, fg=5, color=color)
        self.dim = Style(dim=True, color=color)


class Tracer(Protocol):
    def trace(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    def trace_event(self, ctx: Ctx, event: Style | str) -> None: ...

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
        color = Color.tty() if self.config.colorize else Color.never()
        self.ec = EventColor(color)

    def trace(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if not self.config.trace:
            return

        INFO_print(msg, *args, **kwargs)

    def trace_event(self, ctx: Ctx, event: Style | str) -> None:
        if not self.config.trace:
            return

        cursor = ctx.cursor

        source = ''
        if self.config.trace_filename:
            source = cursor.lineinfo().source
        if source:
            source += '\n'

        lookahead = cursor.lookahead().rstrip()

        pos = cursor.lookahead_pos()

        message = (
            f'{event}{self.rulestack(ctx)}'
            f' {self.ec.dim.apply(source)}'
            f'\n{pos}⇥{lookahead}'
        )
        self.trace(message)

    def trace_entry(self, ctx: Ctx) -> None:
        self.trace_event(ctx, self.ec.entry)

    def trace_success(self, ctx: Ctx) -> None:
        self.trace_event(ctx, self.ec.success)

    def trace_failure(self, ctx: Ctx, ex: Exception | None = None) -> None:
        if isinstance(ex, FailedLeftRecursion):
            self.trace_recursion(ctx)
        else:
            self.trace_event(ctx, self.ec.failure)

    def trace_recursion(self, ctx: Ctx) -> None:
        self.trace_event(ctx, self.ec.recursion)

    def trace_cut(self, ctx: Ctx) -> None:
        self.trace_event(ctx, self.ec.cut)

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

        mark = self.ec.failure if failed else self.ec.success

        lookahead = cursor.lookahead().rstrip()
        lookahead = '\n' + lookahead if lookahead else lookahead

        message = f'{mark}\'{token}{name_str}{self.ec.dim.apply(source)}{lookahead}'
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

    def trace_event(self, ctx: Ctx, event: Style | str) -> None:
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

    def rulestack(self, ctx: Ctx) -> str:
        _ = ctx
        return ""

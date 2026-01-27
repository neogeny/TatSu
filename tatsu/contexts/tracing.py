from __future__ import annotations

from typing import Any

from ..exceptions import FailedLeftRecursion
from ..infos import RuleInfo
from ..parserconfig import ParserConfig
from ..tokenizing import Tokenizer
from ..util import color, info
from ..util.unicode_characters import (
    C_CUT,
    C_ENTRY,
    C_FAILURE,
    C_RECURSION,
    C_SUCCESS,
)


class EventColor(color.Color):
    def __init__(self):
        self.ENTRY = self.YELLOW + self.BRIGHT + C_ENTRY
        self.SUCCESS = self.GREEN + self.BRIGHT + C_SUCCESS
        self.FAILURE = self.RED + self.BRIGHT + C_FAILURE
        self.RECURSION = self.RED + self.BRIGHT + C_RECURSION
        self.CUT = self.MAGENTA + self.BRIGHT + C_CUT


C = EventColor()


class EventTracer:
    def trace(self, msg: str, *args: Any, **kwargs: Any) -> None:
        ...

    def trace_event(self, event: str) -> None:
        ...

    def trace_entry(self) -> None:
        ...

    def trace_success(self) -> None:
        ...

    def trace_failure(self, ex: Exception | None = None) -> None:
        ...

    def trace_recursion(self) -> None:
        ...

    def trace_cut(self) -> None:
        ...

    def trace_match(self, token: Any, name: str | None = None, failed: bool = False) -> None:
        ...


class EventTracerImpl(EventTracer):
    def __init__(
            self,
            tokenizer: Tokenizer,
            ruleinfos: list[RuleInfo],
            *,
            config: ParserConfig | None = None,
            **settings: Any,
    ) -> None:
        self.config = ParserConfig.new(config, **settings)
        self.tokenizer = tokenizer

        # NOTE: not copying / sharing same list with caller
        self.ruleinfos = ruleinfos

        if self.config.colorize:
            color.init()
        global C  # noqa: PLW0603
        C = EventColor()

    def trace(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if not self.config.trace:
            return

        info(msg, *args, **kwargs)

    def trace_event(self, event: str) -> None:
        if not self.config.trace:
            return

        fname = ''
        if self.config.trace_filename:
            fname = self.tokenizer.line_info().filename
        if fname:
            fname += '\n'

        lookahead = self.tokenizer.lookahead().rstrip()
        lookahead = '\n' + lookahead if lookahead else ''

        message = (
            f'{event}{self.rulestack()}'
            f' {C.DIM}{fname}'
            f'{self.tokenizer.lookahead_pos()}{C.RESET}'
            f'{C.RESET_ALL}{lookahead}{C.RESET_ALL}'
        )
        self.trace(message)

    def trace_entry(self) -> None:
        self.trace_event(f'{C.ENTRY}')

    def trace_success(self) -> None:
        self.trace_event(f'{C.SUCCESS}')

    def trace_failure(self, ex: Exception | None = None) -> None:
        if isinstance(ex, FailedLeftRecursion):
            self.trace_recursion()
        else:
            self.trace_event(f'{C.FAILURE}')

    def trace_recursion(self) -> None:
        self.trace_event(f'{C.RECURSION}')

    def trace_cut(self) -> None:
        self.trace_event(f'{C.CUT}')

    def trace_match(self, token: Any, name: str | None = None, failed: bool = False) -> None:
        if not self.config.trace:
            return

        name_str = f'/{name}/' if name else ''
        if self.config.trace_filename:
            fname = self.tokenizer.line_info().filename + '\n'
        else:
            fname = ''

        mark = f'{C.FAILURE}' if failed else f'{C.SUCCESS}'

        lookahead = self.tokenizer.lookahead().rstrip()
        lookahead = '\n' + lookahead if lookahead else lookahead

        message = (
            f'{mark}'
            f"'{token}{name_str}"
            f'{C.DIM}{fname}'
            f'{C.RESET_ALL}{lookahead}{C.RESET_ALL}'
        )
        self.trace(message)

    def rulestack(self) -> str:
        rulestack = [r.name for r in reversed(self.ruleinfos)]
        stack = self.config.trace_separator.join(rulestack)
        if max((len(s) for s in stack.splitlines()), default=0) > self.config.trace_length:
            stack = stack[:self.config.trace_length]
            stack = stack.rsplit(self.config.trace_separator, 1)[0]
            stack += self.config.trace_separator
        return stack

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .contexts.infos import RuleInfo
from .contexts.memento import MEMENTO_DEFAULT_COLOR, memento
from .input import Cursor, LineInfo
from .ztyle import Color, Style


class TatSuException(Exception):
    pass


class ParseException(TatSuException):
    pass


class OptionSucceeded(ParseException):
    pass


class ParseError(ParseException):
    def __str__(self):
        msg = str(self.args[0]) if self.args else ''
        if not msg:
            return ''
        lines = msg.split('\n', 1)
        first = lines[0]
        rest = lines[1] if len(lines) > 1 else ''

        c = Color.stderr()
        err = Style(bold=True, fg=1, color=c)
        bold = Style(bold=True, color=c)

        result = f"{err('error:')} {bold(first)}"
        if rest:
            result += f"\n{rest}"
        return result


class HeartDied(ParseError):
    pass


class GrammarError(ParseError):
    pass


class CodegenError(ParseError):
    pass


class FailedSemantics(ParseException):
    pass


class FailedParse(ParseException):
    def __init__(self, cursor: Cursor, stack: list[RuleInfo], msg: str):
        # NOTE:
        #  Pass all arguments to super() to avoid pickling problems
        #  https://stackoverflow.com/a/28335286/545637
        super().__init__(cursor, stack, msg)

        self.cursor = cursor.clone()
        self.info: LineInfo = cursor.lineinfo()
        self.stack = [ri.name for ri in stack]
        self.msg = msg

    @property
    def pos(self) -> int:
        return self.cursor.pos

    @property
    def message(self):
        return self.msg

    def render(self, color: Color = MEMENTO_DEFAULT_COLOR) -> str:
        text = self.cursor.textstr
        msg = self.message
        info = self.info
        stack = self.stack

        return memento(msg, text, info, stack, color=color)

    def __str__(self):
        return self.render()


class FailedToken(FailedParse):
    def __init__(self, cursor: Cursor, stack: list[RuleInfo], token: str):
        super().__init__(cursor, stack, token)
        self.token = token

    @property
    def message(self):
        return 'expecting {}'.format(repr(self.token).lstrip('u'))


class FailedPattern(FailedParse):
    pass


class FailedMeta(FailedParse):
    pass


class FailedRef(FailedParse):
    def __init__(self, cursor: Cursor, stack: list[RuleInfo], name: str):
        super().__init__(cursor, stack, name)
        self.name = name

    @property
    def message(self):
        return f"Could not resolve reference to rule '{self.name}'"


class FailedChoice(FailedParse):
    @property
    def message(self):
        return 'No viable option'


class FailedLookahead(FailedParse):
    @property
    def message(self):
        return 'failed lookahead'


class FailedLeftRecursion(FailedParse):
    @property
    def message(self):
        return 'infinite left recursion'


class FailedExpectingEndOfText(FailedParse):
    pass


class FailedExpectingEndOfLine(FailedParse):
    pass


class KeywordError(FailedParse):
    pass


class FailedUnlinkedRule(FailedParse):
    pass


FailedKeywordSemantics = KeywordError

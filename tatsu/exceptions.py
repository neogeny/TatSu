# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .contexts.infos import RuleInfo
from .input import Cursor
from .util import typename


class TatSuException(Exception):
    pass


class ParseException(TatSuException):
    pass


class OptionSucceeded(ParseException):
    pass


class ParseError(ParseException):
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
        self.stack = stack.copy()
        self.msg = msg

    @property
    def pos(self) -> int:
        return self.cursor.pos

    @property
    def message(self):
        return self.msg

    def __str__(self):
        import re

        info = self.cursor.lineinfo()
        text = info.text.rstrip()
        leading = re.sub(r'[^\t]', ' ', text)[: info.col]

        text = text.expandtabs()
        leading = leading.expandtabs()
        rulestack = [r.name for r in reversed(self.stack)]
        return (
            f'{info.source}({info.line + 1}:{info.col + 1})'
            f' [{typename(self)}] {self.message.rstrip()} :'
            f'\n{text}\n{leading}^\n{'\n'.join(rulestack)}'
        )


class FailedToken(FailedParse):
    def __init__(self, cursor: Cursor, stack: list[RuleInfo], token: str):
        super().__init__(cursor, stack, token)
        self.token = token

    @property
    def message(self):
        return 'expecting {}'.format(repr(self.token).lstrip('u'))


class FailedPattern(FailedParse):
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


FailedKeywordSemantics = KeywordError

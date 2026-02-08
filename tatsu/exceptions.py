# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re

from .tokenizing import LineInfo


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


class FailedSemantics(ParseError):
    pass


class FailedParse(ParseError):
    def __init__(self, lineinfo: LineInfo, stack: list[str], msg: str):
        # NOTE:
        #   Pass all arguments to super() to avoid pickling problems
        #       https://stackoverflow.com/questions/27993567/
        super().__init__(lineinfo, stack, msg)

        self.lineinfo = lineinfo
        self.stack = stack
        self.msg = msg
        self.pos = lineinfo.end

    @property
    def message(self):
        return self.msg

    def __str__(self):
        info = self.lineinfo
        template = '{}({}:{}) {} :\n{}\n{}^\n{}'
        text = info.text.rstrip()
        leading = re.sub(r'[^\t]', ' ', text)[: info.col]

        text = text.expandtabs()
        leading = leading.expandtabs()
        return template.format(
            info.filename,
            info.line + 1,
            info.col + 1,
            self.message.rstrip(),
            text,
            leading,
            '\n'.join(self.stack),
        )


class FailedToken(FailedParse):
    def __init__(self, tokenizer, stack, token):
        super().__init__(tokenizer, stack, token)
        self.token = token

    @property
    def message(self):
        return 'expecting {}'.format(repr(self.token).lstrip('u'))


class FailedPattern(FailedParse):
    def __init__(self, tokenizer, stack, pattern):
        super().__init__(tokenizer, stack, pattern)
        self.pattern = pattern

    @property
    def message(self):
        return f'expecting /{self.pattern}/'


class FailedRef(FailedParse):
    def __init__(self, tokenizer, stack, name):
        super().__init__(tokenizer, stack, name)
        self.name = name

    @property
    def message(self):
        return f"could not resolve reference to rule '{self.name}'"


class FailedChoice(FailedParse):
    @property
    def message(self):
        return 'no viable option'


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


class FailedCut(FailedParse):
    def __init__(self, nested):
        super().__init__(nested.lineinfo, nested.stack, nested.msg)
        self.nested = nested

    @property
    def message(self):
        return self.nested.message

    def __reduce__(self):
        return type(self), (self.nested,)


class KeywordError(FailedParse):
    pass


FailedKeywordSemantics = KeywordError

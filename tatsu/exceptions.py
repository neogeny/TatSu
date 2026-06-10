# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .contexts.infos import RuleInfo
from .input import Cursor, LineInfo
from .util.colorize.style import Color, Style


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


_DEFAULT_COLOR = Color.stderr()


class _ColorSet:
    def __init__(self, color: Color = _DEFAULT_COLOR):
        self.err = Style(bold=True, fg=1, color=color).apply
        self.loc = Style(fg=4, color=color).apply
        self.gut = Style(dim=True, color=color).apply
        self.ar = Style(bold=True, fg=2, color=color).apply


class FailedParse(ParseException):
    def __init__(self, cursor: Cursor, stack: list[RuleInfo], msg: str):
        # NOTE:
        #  Pass all arguments to super() to avoid pickling problems
        #  https://stackoverflow.com/a/28335286/545637
        super().__init__(cursor, stack, msg)

        self.cursor = cursor.clone()
        self.info: LineInfo = cursor.lineinfo()
        self.stack = stack.copy()
        self.msg = msg

    @property
    def pos(self) -> int:
        return self.cursor.pos

    @property
    def message(self):
        return self.msg

    def render(self, color: Color = _DEFAULT_COLOR) -> str:
        from io import StringIO

        c = _ColorSet(color)

        text = self.cursor.textstr

        line, col = self.info.line, self.info.col

        source = self.info.source or '<unknown>'
        msg = self.message

        rulestack = [r.name for r in reversed(self.stack)]

        out = StringIO()

        lines = text.splitlines()
        print(f'{c.err("error:")} {msg}', file=out)
        print(
            f'{c.loc("  -->")} {source}@{self.info.end}[{line + 1}:{col + 1}]',
            file=out,
        )
        print(f'   {c.gut("|")}', file=out)

        max_line_digits = len(str(line + 1))
        start_line_idx = max(0, line - 4)

        for i in range(start_line_idx, min(line + 1, len(lines))):
            current_line_num = i + 1
            content = lines[i].expandtabs()
            print(
                f' {current_line_num:>{max_line_digits}} {c.gut("|")} {content}',
                file=out,
            )

        padding = ' ' * max(0, col)
        print(
            f'{" ":{max_line_digits + 1}}{c.gut("|")} {padding}{c.err("^")} {msg}',
            file=out,
        )

        print(file=out)
        for call in rulestack:
            print(f'{c.ar("→")} {call}', file=out)

        return out.getvalue()

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


FailedKeywordSemantics = KeywordError

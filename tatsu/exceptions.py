# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from tatsu.util.strtools import slicetowidth

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


class HeartDied(ParseError):
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
        self.err = Style(bold=True, fg=1, color=color)
        self.loc = Style(fg=4, color=color)
        self.gut = Style(color=color).basic_blue().bold()
        self.ar = Style(color=color).basic_red().dim()
        self.nam = Style(color=color).white().bold()
        self.msg = Style(color=color).white().bold()


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

        text = self.cursor.textstr
        msg = self.message
        info = self.info

        c = _ColorSet(color)
        line, col = info.line, info.col
        source = info.source or '<unknown>'
        rulestack = [r.name for r in reversed(self.stack)]

        out = StringIO()
        s = Style(color=color)

        lines = text.splitlines()
        errmsg = f'{c.err("error:")} {c.msg(msg)}'
        print(errmsg, file=out)
        loc = s(f'[{line + 1}:{col + 1}]').dim()
        print(
            f'{c.gut("  ─→")} {c.nam(source)}{loc}',
            file=out,
        )
        gut = c.gut("│")
        print(f'   {gut}', file=out)

        max_line_digits = len(str(line + 1))
        start_line_idx = max(0, line - 4)

        for i in range(start_line_idx, min(line + 1, len(lines))):
            current_line_num = i + 1
            content = lines[i].expandtabs()
            print(
                f' {current_line_num:>{max_line_digits}} {gut} {content}',
                file=out,
            )

        padding = ' ' * max(0, col)
        print(
            f' {" ":{max_line_digits + 1}}{gut}'
            f' {padding}{c.err("⌃ error:")} {c.msg(slicetowidth(msg, 40))}',
            file=out,
        )

        print(file=out)
        for call in rulestack:
            print(f'{c.ar("→")} {s(call).dim()}', file=out)

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


class FailedUnlinkedRule(FailedParse):
    pass


FailedKeywordSemantics = KeywordError

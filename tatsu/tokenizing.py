from __future__ import annotations

from itertools import starmap
from typing import Any, NamedTuple, Protocol, runtime_checkable


@runtime_checkable
class Tokenizer(Protocol):
    def __init__(self, *ags: Any, **kwargs: Any):
        ...

    @property
    def text(self) -> str:
        ...

    @property
    def filename(self) -> str:
        ...

    @property
    def ignorecase(self) -> bool:
        ...

    @property
    def pos(self) -> int:
        ...

    def goto(self, pos) -> None:
        ...

    def atend(self) -> bool:
        ...

    def ateol(self) -> bool:
        ...

    @property
    def current(self) -> str | None:
        ...

    @property
    def token(self):
        return self.current

    def next(self) -> str | None:
        ...

    def next_token(self) -> None:
        ...

    def match(self, token: str) -> str | None:
        ...

    def matchre(self, pattern: str) -> str | None:
        ...

    def posline(self, pos: int | None = None) -> int:
        ...

    def line_info(self, pos: int | None = None) -> LineInfo:
        ...

    def get_line(self, n: int | None = None) -> str:
        ...

    def get_lines(self, start: int | None = None, end: int | None = None) -> list[str]:
        ...

    def line_index(self, start: int = 0, end: int | None = None) -> list[LineIndexInfo]:
        ...

    def lookahead(self) -> str:
        ...

    def lookahead_pos(self) -> str:
        ...


class NullTokenizer(Tokenizer):
    def __init__(self, *ags: Any, **kwargs: Any):
        pass

    @property
    def text(self) -> str:
        return ''

    @property
    def filename(self) -> str:
        return ''

    @property
    def ignorecase(self) -> bool:
        return False

    @property
    def pos(self) -> int:
        return 0

    def goto(self, pos) -> None:
        return

    def atend(self) -> bool:
        return False

    def ateol(self) -> bool:
        return False

    @property
    def current(self) -> str | None:
        return None

    @property
    def token(self):
        return self.current

    def next(self) -> str | None:
        return None

    def next_token(self) -> None:
        return None

    def match(self, token: str) -> str | None:
        return None

    def matchre(self, pattern: str) -> str | None:
        return None

    def posline(self, pos: int | None = None) -> int:
        return 0

    def line_info(self, pos: int | None = None) -> LineInfo:
        return LineInfo('', 0, 0, 0, 0, '')

    def get_line(self, n: int | None = None) -> str:
        return ''

    def get_lines(self, start: int | None = None, end: int | None = None) -> list[str]:
        return []

    def line_index(self, start: int = 0, end: int | None = None) -> list[LineIndexInfo]:
        return []

    def lookahead(self) -> str:
        return ''

    def lookahead_pos(self) -> str:
        return ''


class LineIndexInfo(NamedTuple):
    filename: str
    line: int

    @staticmethod
    def block_index(name, n):
        return list(
            starmap(LineIndexInfo, zip(n * [name], range(n), strict=False)),
        )


class LineInfo(NamedTuple):
    filename: str
    line: int
    col: int
    start: int
    end: int
    text: str


class PosLine(NamedTuple):
    start: int
    line: int
    length: int

    @staticmethod
    def build_line_cache(lines):
        cache = []
        n = 0
        i = 0
        for n, line in enumerate(lines):
            pl = PosLine(i, n, len(line))
            for _ in line:
                cache.append(pl)  # noqa: PERF401
            i += len(line)
        n += 1
        if lines and lines[-1] and lines[-1][-1] in '\r\n':
            n += 1
        cache.append(PosLine(i, n, 0))
        return cache, n


class CommentInfo(NamedTuple):
    inline: list
    eol: list

    @staticmethod
    def new_comment():
        return CommentInfo([], [])

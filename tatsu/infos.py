from __future__ import generator_stop

import typing
import copy
from collections import namedtuple
from typing import (
    Any,
    Mapping,
    Optional,
    Type,
    Union,
)

from .ast import AST
from .util.unicode_characters import C_DERIVE


COMMENTS_RE = r'\(\*((?:.|\n)*?)\*\)'
EOL_COMMENTS_RE = r'#([^\n]*?)$'


class ParserConfig:
    __slots__ = ("owner", "name", "filename", "encoding", "start", "start_rule", "comments_re", "eol_comments_re", "tokenizercls", "semantics", "comment_recovery", "memoize_lookaheads", "colorize", "trace", "trace_filename", "trace_length", "trace_separator", "grammar", "left_recursion", "comments", "eol_comments", "keywords", "ignorecase", "namechars", "nameguard", "whitespace", "parseinfo")

    def __init__(self, 
        owner: object = None,
        name: Optional[str] = 'Test',
        filename: str = '',
        encoding: str = 'utf-8',

        start: Optional[str] = None,  # FIXME
        start_rule: Optional[str] = None,  # FIXME

        comments_re: Optional[str] = COMMENTS_RE,
        eol_comments_re: Optional[str] = EOL_COMMENTS_RE,

        tokenizercls: Optional[Type] = None,  # FIXME
        semantics: Optional[Type] = None,

        comment_recovery: bool = False,
        memoize_lookaheads: bool = True,

        colorize: bool = False,
        trace: bool = False,
        trace_filename: bool = False,
        trace_length: int = 72,
        trace_separator: str = C_DERIVE,

        # parser directives
        grammar: Optional[str] = None,
        left_recursion: bool = True,

        comments: Optional[str] = None,
        eol_comments: Optional[str] = None,
        keywords: Union[typing.List[str], typing.Set[str]] = None,

        ignorecase: Optional[bool] = False,
        namechars: str = '',
        nameguard: Optional[bool] = None,  # implied by namechars
        whitespace: Optional[str] = None,

        parseinfo: bool = False  # type
    ):
        if keywords is None:
            keywords = []

        self.owner = owner
        self.name = name
        self.filename = filename
        self.encoding = encoding

        self.start = start
        self.start_rule = start_rule

        self.comments_re = comments_re
        self.eol_comments_re = eol_comments_re

        self.tokenizercls = tokenizercls
        self.semantics = semantics

        self.comment_recovery = comment_recovery
        self.memoize_lookaheads = memoize_lookaheads

        self.colorize = colorize
        self.trace = trace
        self.trace_filename = trace_filename
        self.trace_length = trace_length
        self.trace_separator = trace_separator

        # parser directives
        self.grammar = grammar
        self.left_recursion = left_recursion

        self.comments = comments
        self.eol_comments = eol_comments
        self.keywords = keywords

        self.ignorecase = ignorecase
        self.namechars = namechars
        self.nameguard = nameguard
        self.whitespace = whitespace

        self.parseinfo = parseinfo

        self.__post_init__()

    def __post_init__(self):  # pylint: disable=W0235
        if self.ignorecase:
            self.keywords = [k.upper() for k in self.keywords]
        if self.comments:
            self.comments_re = self.comments
        if self.eol_comments:
            self.eol_comments_re = self.eol_comments

    @classmethod
    def new(cls, config: Optional["ParserConfig"], owner: Any = None, **settings: Any) -> "ParserConfig":
        result = cls(owner=owner)
        if config is not None:
            result = config.replace_config(config)
        return result.replace(**settings)

    def effective_rule_name(self):
        # note: there are legacy reasons for this mess
        return (
            self.start_rule or
            self.start
        )

    def _find_common(self, **settings: Any) -> Mapping[str, Any]:
        return {
            name: value
            for name, value in settings.items()
            if value is not None and hasattr(self, name)
        }

    def replace_config(self, other: Optional["ParserConfig"]) -> "ParserConfig":
        if other is None:
            return self
        elif not isinstance(other, ParserConfig):
            raise TypeError('Unexpected type ' + type(other).__name__)
        else:
            return self.replace(**{k: getattr(other, k) for k in other.__class__.__slots__})

    def replace(self, **settings: Any) -> "ParserConfig":
        overrides = self._find_common(**settings)
        d = {k: getattr(self, k) for k in self.__class__.__slots__}
        d.update(overrides)
        result = self.__class__(**d)
        if 'grammar' in overrides:
            result.name = result.grammar
        return result

    def merge(self, **settings: Any) -> "ParserConfig":
        overrides = self._find_common(**settings)
        overrides = {
            name: value for name, value in overrides.items()
            if getattr(self, name, None) is None
        }
        return self.replace(**overrides)

    def asdict(self):
        # warning: it seems dataclasses.asdict does a deepcopy
        # result = dataclasses.asdict(self)
        result = copy.copy(vars(self))
        result.pop('owner', None)
        return result


class PosLine(namedtuple('_PosLine', ['start', 'line', 'length'])):
    __slots__ = ()

    @staticmethod
    def build_line_cache(lines):
        cache = []
        n = 0
        i = 0
        for n, line in enumerate(lines):
            pl = PosLine(i, n, len(line))
            for c in line:
                cache.append(pl)
            i += len(line)
        n += 1
        if lines and lines[-1] and lines[-1][-1] in '\r\n':
            n += 1
        cache.append(PosLine(i, n, 0))
        return cache, n


class LineIndexInfo(namedtuple('_LineIndexInfoBase', ['filename', 'line'])):
    __slots__ = ()

    @staticmethod
    def block_index(name, n):
        return list(LineIndexInfo(line, i) for line, i in zip(n * [name], range(n)))


class LineInfo(namedtuple('_LineInfo', ['filename', 'line', 'col', 'start', 'end', 'text'])):
    __slots__ = ()


class CommentInfo(namedtuple('_CommentInfo', ['inline', 'eol'])):
    __slots__ = ()

    @staticmethod
    def new_comment():
        return CommentInfo([], [])


_ParseInfo = namedtuple(
    '_ParseInfo',
    [
        'tokenizer',
        'rule',
        'pos',
        'endpos',
        'line',
        'endline',
    ]
)


class ParseInfo(_ParseInfo):
    __slots__ = ()

    def text_lines(self):
        return self.tokenizer.get_lines(self.line, self.endline)

    def line_index(self):
        return self.tokenizer.line_index(self.line, self.endline)


MemoKey = namedtuple(
    'MemoKey',
    [
        'pos',
        'rule',
        'state'
    ]
)


_RuleInfo = namedtuple(
    '_RuleInfo',
    [
        'name',
        'impl',
        'is_leftrec',
        'is_memoizable',
        'is_name',
        'params',
        'kwparams',
    ]
)


class RuleInfo(_RuleInfo):
    __slots__ = ()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, RuleInfo):
            return self.name == other.name
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


RuleResult = namedtuple(
    'RuleResult',
    [
        'node',
        'newpos',
        'newstate',
    ]
)


class ParseState(object):
    __slots__ = ("pos", "ast", "cst")

    def __init__(self, pos: int= 0, ast = None, cst: Any = None):
        self.pos = pos
        if ast is None:
            ast = AST()
        self.ast = ast
        self.cst = cst

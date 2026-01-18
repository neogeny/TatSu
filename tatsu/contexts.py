from __future__ import annotations

import ast as stdlib_ast
import dataclasses
import functools
import re
import sys
from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager, suppress
from copy import copy
from typing import Any, NamedTuple, NoReturn, Protocol, cast

from . import buffering, color, tokenizing
from .ast import AST
from .buffering import Buffer
from .collections import BoundedDict
from .exceptions import (
    FailedExpectingEndOfText,
    FailedKeywordSemantics,
    FailedLeftRecursion,
    FailedLookahead,
    FailedParse,
    FailedPattern,
    FailedRef,
    FailedSemantics,
    FailedToken,
    OptionSucceeded,
    ParseError,
)
from .infos import (
    Alert,
    ParseInfo,
    ParserConfig,
    RuleInfo,
)
from .tokenizing import NullTokenizer, Tokenizer
from .util import (
    info,
    is_list,
    left_assoc,
    prune_dict,
    right_assoc,
    safe_name,
    trim,
)
from .util.unicode_characters import (
    C_CUT,
    C_DOT,
    C_ENTRY,
    C_FAILURE,
    C_RECURSION,
    C_SUCCESS,
)

__all__: list[str] = ['ParseContext', 'tatsumasu', 'leftrec', 'nomemo']


class MemoKey(NamedTuple):
    pos: int
    rule: RuleInfo
    state: Any


@dataclasses.dataclass(slots=True)
class ParseState:
    pos: int = 0
    ast: Any = dataclasses.field(default_factory=dict)
    cst: Any = None
    alerts: list[Alert] = dataclasses.field(default_factory=list)


class RuleResult(NamedTuple):
    node: Any
    newpos: int
    newstate: Any


class RuleLike(Protocol):
    is_leftrec: bool = False
    is_memoizable: bool = False
    is_name: bool = False

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass


# decorator for rule implementation methods
def tatsumasu(*params: Any, **kwparams: Any) -> Callable[[Callable[..., Any]], Callable[[ParseContext], Any]]:
    def decorator(impl: Callable[..., Any]) -> Callable[[ParseContext], Any]:
        @functools.wraps(impl)
        def wrapper(self: ParseContext) -> Any:
            name = impl.__name__  # type: ignore
            # remove the single leading and trailing underscore
            # that the parser generator added
            if name.startswith("_") and name.endswith("_"):
                name = name[1:-1]
            is_leftrec = getattr(impl, 'is_leftrec', False)
            is_memoizable = getattr(impl, 'is_memoizable', True)
            is_name = getattr(impl, 'is_name', False)
            ruleinfo = RuleInfo(
                name,
                impl,
                is_leftrec,
                is_memoizable,
                is_name,
                params,
                kwparams,
            )
            return self._call(ruleinfo)

        return wrapper

    return decorator


# This is used to mark left recursive rules
def leftrec(impl: Callable) -> Callable:
    over: RuleLike = cast(RuleLike, impl)
    over.is_leftrec = True
    over.is_memoizable = False
    return impl


# Marks rules for which memoization has to be turned off
# (has no effect when left recursion is turned off)
def nomemo(impl: Callable) -> Callable:
    over: RuleLike = cast(RuleLike, impl)
    over.is_memoizable = False
    return impl


# Marks rules marked as @name in the grammar
def isname(impl: Callable) -> Callable:
    over: RuleLike = cast(RuleLike, impl)
    over.is_name = True

    return impl


class closure(list[Any]):
    def __hash__(self) -> int:  # type: ignore
        return hash(tuple(self))


class ParseContext:
    def __init__(self, /, config: ParserConfig | None = None, **settings: Any) -> None:
        super().__init__()

        config = ParserConfig.new(config, **settings)
        if config.tokenizercls is None:
            config = config.replace(tokenizercls=Buffer)
        self.config: ParserConfig = config
        self._active_config: ParserConfig = self.config

        self._tokenizer: Tokenizer = NullTokenizer()
        self._semantics: type | None = config.semantics
        self._initialize_caches()

    def _initialize_caches(self) -> None:
        self._statestack: list[ParseState] = [ParseState()]
        self._rule_stack: list[RuleInfo] = []
        self._cut_stack: list[bool] = [False]

        self._last_node: Any = None
        self.substate: Any = None
        self._lookahead: int = 0
        self._furthest_exception: FailedParse | None = None

        self._clear_memoization_caches()

    @property
    def active_config(self) -> ParserConfig:
        return self._active_config

    @property
    def semantics(self) -> Any:
        return self._semantics

    @property
    def encoding(self) -> str | None:
        return self.active_config.encoding

    @property
    def parseinfo(self) -> bool:
        return self.active_config.parseinfo

    @property
    def trace(self) -> bool:
        return self.active_config.trace

    @property
    def trace_length(self) -> int:
        return self.active_config.trace_length

    @property
    def trace_separator(self) -> str:
        return self.active_config.trace_separator

    @property
    def trace_filename(self) -> str:
        return self.active_config.trace_filename

    @property
    def comments_re(self) -> re.Pattern | str | None:
        return self.active_config.comments_re

    @property
    def eol_comments_re(self) -> re.Pattern | str | None:
        return self.active_config.eol_comments_re

    @property
    def whitespace(self) -> str | None:
        return self.active_config.whitespace

    @property
    def ignorecase(self) -> bool:
        return self.active_config.ignorecase

    @property
    def nameguard(self) -> bool | None:
        return self.active_config.nameguard

    @property
    def memoize_lookaheads(self) -> bool:
        return self.active_config.memoize_lookaheads

    @property
    def left_recursion(self) -> bool:
        return self.active_config.left_recursion

    @property
    def colorize(self) -> bool:
        return self.active_config.colorize

    @property
    def keywords(self) -> set[str]:
        return self._keywords

    @property
    def namechars(self) -> str | None:
        return self.active_config.namechars

    def _reset(self, config: ParserConfig) -> ParserConfig:
        if self.active_config.colorize:
            color.init()
        self._initialize_caches()
        self._keywords: set[str] = set(config.keywords)
        self._semantics = config.semantics
        if hasattr(self.semantics, 'set_context'):
            self.semantics.set_context(self)
        return config

    def _set_furthest_exception(self, e: FailedParse) -> None:
        if (
                not self._furthest_exception
                or e.pos > self._furthest_exception.pos
        ):
            self._furthest_exception = e

    def parse(self, text: str | Tokenizer, /, *, config: ParserConfig | None = None, **settings: Any) -> Any:
        config = self.config.replace_config(config)
        config = config.replace(**settings)
        self._active_config = config
        try:
            self._reset(config)
            if isinstance(text, tokenizing.Tokenizer):
                tokenizer = text
            elif issubclass(config.tokenizercls, NullTokenizer):
                tokenizer = Buffer(text=text, config=config, **settings)
            elif text is not None:
                cls = self.tokenizercls
                tokenizer = cls(text, config=config, **settings)
            else:
                raise ParseError('No tokenizer or text')

            self._tokenizer = tokenizer
            start: str = self.active_config.effective_rule_name() or 'start'

            try:
                rule = self._find_rule(start)
                return rule()
            except FailedParse as e:
                self._set_furthest_exception(e)
                raise self._furthest_exception from e  # type: ignore
            finally:
                self._clear_memoization_caches()
        finally:
            self._active_config = self.config

    @property
    def tokenizer(self) -> Tokenizer:
        return self._tokenizer

    @property
    def tokenizercls(self) -> type[Tokenizer]:
        if self.config.tokenizercls is None:
            return buffering.Buffer
        else:
            return self.config.tokenizercls

    @property
    def last_node(self) -> Any:
        return self._last_node

    @last_node.setter
    def last_node(self, value: Any) -> None:
        self._last_node = value

    @property
    def _pos(self) -> int:
        return self._tokenizer.pos

    def _clear_memoization_caches(self) -> None:
        self._memos: BoundedDict[MemoKey, RuleResult | Exception] = BoundedDict(self.config.memo_cache_size)
        self._results: dict[MemoKey, RuleResult | Exception] = {}

    def _goto(self, pos: int) -> None:
        self._tokenizer.goto(pos)

    def _next(self) -> Any:
        return self._tokenizer.next()

    def _next_token(self, ruleinfo: RuleInfo | None = None) -> None:
        if ruleinfo is None or not ruleinfo.name.lstrip('_')[:1].isupper():
            self._tokenizer.next_token()

    def _define(self, keys: Iterable[str], list_keys: Iterable[str] | None = None) -> None:
        ast = AST()
        ast._define(keys, list_keys=list_keys)
        ast.update(self.ast)
        self.ast = ast

    @property
    def state(self) -> ParseState:
        return self._statestack[-1]

    @property
    def ast(self) -> AST:
        return self.state.ast

    @ast.setter
    def ast(self, value: AST) -> None:
        self.state.ast = value

    def name_last_node(self, name: str) -> None:
        self.ast[name] = self.last_node

    def add_last_node_to_name(self, name: str) -> None:
        self.ast._setlist(name, self.last_node)

    @staticmethod
    def _safe_name(name: str, ast: AST) -> str:
        while name in ast:
            name += '_'
        return name

    def ast_set(self, name: str, value: Any, as_list: bool = False) -> None:
        ast = self.ast
        name = self._safe_name(name, ast)

        previous = ast.get(name)
        if previous is None:
            new_value = [value] if as_list else value
        elif is_list(previous):
            new_value = [*previous, value]
        else:
            new_value = [previous, value]

        ast = AST(ast, name=new_value)
        self.ast = ast

    def ast_append(self, name: str, value: Any) -> None:
        self.ast_set(name, value, as_list=True)

    def _push_ast(self, copyast: bool = False) -> None:
        ast = copy(self.ast) if copyast else AST()
        self.state.pos = self._pos
        self._statestack.append(ParseState(ast=ast, pos=self._pos))

    def _pop_ast(self) -> None:
        self._statestack.pop()
        self.tokenizer.goto(self.state.pos)

    def _merge_ast(self) -> None:
        pos = self._pos
        ast = self.ast
        cst = self.cst
        self._statestack.pop()
        self.ast = ast
        self._extend_cst(cst)
        self.tokenizer.goto(pos)

    @property
    def cst(self) -> Any:
        return self.state.cst

    @cst.setter
    def cst(self, value: Any) -> None:
        self.state.cst = value

    def _push_cst(self) -> None:
        self._statestack.append(ParseState(ast=self.ast))

    def _pop_cst(self) -> None:
        ast = self.ast
        self._statestack.pop()
        self.ast = ast

    def _merge_cst(self, extend: bool = True) -> Any:
        cst = self.cst
        self._pop_cst()
        if extend:
            self._extend_cst(cst)
        else:
            self._append_cst(cst)
        return cst

    def _append_cst(self, node: Any) -> Any:
        self.last_node = node
        previous = self.cst
        if previous is None:
            self.cst = self._copy_node(node)
        elif is_list(previous):
            previous.append(node)
        else:
            self.cst = [previous, node]
        return node

    def _extend_cst(self, node: Any) -> Any:
        self.last_node = node
        if node is None:
            return None
        previous = self.cst
        if previous is None:
            self.cst = self._copy_node(node)
        elif is_list(node):
            if is_list(previous):
                previous.extend(node)
            else:
                self.cst = [previous, *node]
        elif is_list(previous):
            previous.append(node)
        else:
            self.cst = [previous, node]
        return node

    def _copy_node(self, node: Any) -> Any:
        if node is None:
            return None
        elif is_list(node):
            return node[:]
        else:
            return node

    def _is_cut_set(self) -> bool:
        return self._cut_stack[-1]

    def _cut(self) -> None:
        self._trace_cut()
        self._cut_stack[-1] = True

        def prune(cache: dict[Any, Any], cut_pos: int) -> None:
            prune_dict(
                cache,
                lambda k, v: k[0] < cut_pos and not isinstance(v, FailedLeftRecursion),
            )

        # prune(self._memos, self._pos)

    def _memoization(self) -> bool:
        return self.config.memoization and (
                self.memoize_lookaheads or
                self._lookahead == 0
        )

    def _rulestack(self) -> str:
        rulestack = [r.name for r in reversed(self._rule_stack)]
        stack = self.trace_separator.join(rulestack)
        if max((len(s) for s in stack.splitlines()), default=0) > self.trace_length:
            stack = stack[: self.trace_length]
            stack = stack.rsplit(self.trace_separator, 1)[0]
            stack += self.trace_separator
        return stack

    def _find_rule(self, name: str) -> Callable[[], Any]:
        self._error(name, exclass=FailedRef)
        return lambda: None  # makes static checkers happy

    def _find_semantic_action(self, name: str) -> tuple[Callable[..., Any] | None, Callable[..., Any] | None]:
        if self.semantics is None:
            return None, None

        postproc = getattr(self.semantics, '_postproc', None)

        action = getattr(self.semantics, safe_name(name), None)
        if not callable(action):
            action = getattr(self.semantics, '_default', None)

        if not callable(action):
            action = None
        if not callable(postproc):
            postproc = None

        return action, postproc

    def _trace(self, msg: str, *params: Any, **kwargs: Any) -> None:
        if not self.trace:
            return

        msg %= params
        indent = C_DOT * (len(self._rule_stack) - 3)
        info(indent, msg, file=sys.stderr)

    def _trace_event(self, event: str) -> None:
        if not self.trace:
            return

        fname = ''
        if self.trace_filename:
            fname = self._tokenizer.line_info().filename + '\n'

        lookahead = self._tokenizer.lookahead().rstrip()
        if lookahead:
            lookahead = '\n' + ' ' * (len(self._rule_stack) - 3) + lookahead

        self._trace(
            '%s %s%s%s',
            event + self._rulestack(),
            self._tokenizer.lookahead_pos(),
            color.Style.DIM + fname,
            color.Style.RESET_ALL + lookahead + color.Style.RESET_ALL,
            )

    def _trace_entry(self) -> None:
        self._trace_event(color.Fore.YELLOW + color.Style.BRIGHT + C_ENTRY)

    def _trace_success(self) -> None:
        self._trace_event(color.Fore.GREEN + color.Style.BRIGHT + C_SUCCESS)

    def _trace_failure(self, ex: Exception | None = None) -> None:
        if isinstance(ex, FailedLeftRecursion):
            self._trace_recursion()
        else:
            self._trace_event(color.Fore.RED + color.Style.BRIGHT + C_FAILURE)

    def _trace_recursion(self) -> None:
        self._trace_event(color.Fore.RED + color.Style.BRIGHT + C_RECURSION)

    def _trace_cut(self) -> None:
        self._trace_event(color.Fore.MAGENTA + color.Style.BRIGHT + C_CUT)

    def _trace_match(self, token: Any, name: str | None = None, failed: bool = False) -> None:
        if not self.trace:
            return

        fname = ''
        if self.trace_filename:
            fname = self._tokenizer.line_info().filename + '\n'
        name_str = f'/{name}/' if name else ''

        if not failed:
            fgcolor = color.Fore.GREEN + C_SUCCESS
        else:
            fgcolor = color.Fore.RED + C_FAILURE

        lookahead = self._tokenizer.lookahead().rstrip()
        if lookahead:
            lookahead = '\n' + ' ' * (len(self._rule_stack) - 3) + lookahead

        self._trace(
            color.Style.BRIGHT + fgcolor + "'%s' %s%s%s",
            token,
            name_str,
            color.Style.DIM + fname,
            color.Style.RESET_ALL + lookahead + color.Style.RESET_ALL,
            )

    def _make_exception(self, item: Any, exclass: type[FailedParse] = FailedParse) -> FailedParse:
        if issubclass(exclass, FailedLeftRecursion):
            rulestack: list[str] = []
        else:
            rulestack = [r.name for r in reversed(self._rule_stack)]
        return exclass(self.tokenizer, rulestack, item)

    def _error(self, item: Any, exclass: type[FailedParse] = FailedParse) -> NoReturn:
        raise self._make_exception(item, exclass=exclass)

    def _fail(self) -> NoReturn:
        self._error('fail')

    def _get_parseinfo(self, name: str, pos: int) -> ParseInfo:
        endpos = self._pos
        return ParseInfo(
            tokenizer=self.tokenizer,
            rule=name,
            pos=pos,
            endpos=endpos,
            line=self.tokenizer.posline(pos),
            endline=self.tokenizer.posline(endpos),
            alerts=self.state.alerts,
        )

    @property
    def rule(self) -> RuleInfo:
        return self._rule_stack[-1]

    def memokey(self) -> MemoKey:
        return MemoKey(self._pos, self.rule, self.substate)

    def _memoize(self, key: MemoKey, memo: RuleResult | Exception) -> RuleResult | Exception:
        if self._memoization() and key.rule.is_memoizable:
            self._memos[key] = memo
        return memo

    def _save_result(self, key: MemoKey, result: RuleResult) -> None:
        if is_list(result.node):
            result = result._replace(node=closure(result.node))
        self._results[key] = result

    def _set_left_recursion_guard(self, key: MemoKey) -> None:
        if not self.left_recursion:
            return
        ex = self._make_exception(key.rule.name, exclass=FailedLeftRecursion)
        self._memoize(key, ex)

    def _call(self, ruleinfo: RuleInfo) -> Any:
        self._rule_stack += [ruleinfo]
        pos = self._pos
        try:
            self._trace_entry()
            self._last_node = None

            result = self._recursive_call(ruleinfo)

            self._goto(result.newpos)
            self.substate = result.newstate
            self._append_cst(result.node)

            self._trace_success()

            return result.node
        except FailedPattern:
            self._error(f'Expecting <{ruleinfo.name}>')
        except FailedParse as e:
            self._goto(pos)
            self._set_furthest_exception(e)
            self._trace_failure(e)
            raise
        finally:
            self._rule_stack.pop()

    def _clear_recursion_errors(self) -> None:
        def filter_func(key: MemoKey, value: Any) -> bool:
            return isinstance(value, FailedLeftRecursion)

        prune_dict(self._memos, filter_func)

    def _found_left_recursion(self, ruleinfo: RuleInfo) -> bool:
        return any(ri.name == ruleinfo.name for ri in self._rule_stack)

    def _recursive_call(self, ruleinfo: RuleInfo) -> RuleResult:
        self._next_token(ruleinfo)
        key: MemoKey = self.memokey()

        if not ruleinfo.is_leftrec:
            return self._invoke_rule(ruleinfo, key)
        elif not self.left_recursion:
            self._error('Left recursion detected', exclass=FailedLeftRecursion)

        result: RuleResult | Exception | None = self._results.get(key)
        if isinstance(result, RuleResult):
            return result
        elif isinstance(result, Exception):
            raise result

        result = FailedLeftRecursion(self.tokenizer, stack=[], item=ruleinfo.name)
        self._results[key] = result

        initial = self._pos
        lastpos = -1
        while True:
            self._clear_recursion_errors()
            try:
                new_result = self._invoke_rule(ruleinfo, key)
                self._goto(initial)
            except FailedParse:
                break

            if new_result.newpos > lastpos:
                self._save_result(key, new_result)
                lastpos = new_result.newpos
                result = new_result
            else:
                break

        if isinstance(result, Exception):
            raise result

        return result

    def _actual_node_value(self, pos: int, ruleinfo: RuleInfo) -> Any:
        node: Any = self.ast
        if not node:
            node = tuple(self.cst) if is_list(self.cst) else self.cst
        elif '@' in node:
            node = node['@']  # override the AST
        elif self.parseinfo:
            node.set_parseinfo(self._get_parseinfo(ruleinfo.name, pos))
        return node

    def _invoke_rule(self, ruleinfo: RuleInfo, key: MemoKey) -> RuleResult:
        result = self._memos.get(key)
        if isinstance(result, Exception):
            raise result
        if isinstance(result, RuleResult):
            return result

        self._set_left_recursion_guard(key)

        self._push_ast()
        try:
            try:
                self._next_token(ruleinfo)
                ruleinfo.impl(self)
                node = self._actual_node_value(key.pos, ruleinfo)
                node = self._invoke_semantic_rule(ruleinfo, node)

                result = RuleResult(node, self._pos, self.substate)
                self._memoize(key, result)

                return result
            except FailedSemantics as e:
                self._error(str(e))
        except FailedParse as e:
            self._memoize(key, e)
            raise
        finally:
            self._pop_ast()

    def _invoke_semantic_rule(self, rule: RuleInfo, node: Any) -> Any:
        semantic_rule, postproc = self._find_semantic_action(rule.name)
        if semantic_rule:
            # try:
            node = semantic_rule(
                node,
                *(rule.params or ()),
                **(rule.kwparams or {}),
            )
            # except TypeError:
            #     node = semantic_rule(  # method call
            #         self.semantics,  # self
            #         node,
            #         *(rule.params or ()),
            #         **(rule.kwparams or {}),
            #     )

        if callable(postproc):
            postproc(self, node)
        if rule.is_name:
            self._check_name(node)
        return node

    def _token(self, token: str) -> str:
        self._next_token()
        if self.tokenizer.match(token) is None:
            self._trace_match(token, failed=True)
            self._error(token, exclass=FailedToken)
        self._trace_match(token)
        self._append_cst(token)
        return token

    def _constant(self, literal: Any) -> Any:
        self._next_token()
        self._trace_match(literal)
        if isinstance(literal, str):
            try:
                literal = stdlib_ast.literal_eval(literal.strip())
            except (ValueError, SyntaxError):
                if '\n' in literal:
                    literal = trim(literal)
                literal = eval(  # noqa: S307
                    f'{"f" + repr(literal)}', {}, self.ast,
                )
        self._append_cst(literal)
        return literal

    def _alert(self, message: str, level: int) -> None:
        self._next_token()
        self._trace_match(f'{"^" * level}`{message}`', failed=True)
        self.state.alerts.append(Alert(message=message, level=level))

    def _pattern(self, pattern: str) -> Any:
        token = self.tokenizer.matchre(pattern)
        if token is None:
            self._trace_match('', pattern, failed=True)
            self._error(pattern, exclass=FailedPattern)
        self._trace_match(token, pattern)
        self._append_cst(token)
        return token

    def _eof(self) -> bool:
        return self.tokenizer.atend()

    def _eol(self) -> bool:
        return self.tokenizer.ateol()

    def _check_eof(self) -> None:
        self._next_token()
        if not self.tokenizer.atend():
            self._error(
                'Expecting end of text', exclass=FailedExpectingEndOfText,
            )

    @contextmanager
    def _try(self) -> Generator[None, None, None]:
        s = self.substate
        self._push_ast(copyast=True)
        self.last_node = None
        try:
            yield
            self._merge_ast()
        except FailedParse:
            self._pop_ast()
            self.substate = s
            raise

    @contextmanager
    def _option(self) -> Generator[None, None, None]:
        self.last_node = None
        self._cut_stack += [False]
        try:
            with self._try():
                yield
            raise OptionSucceeded()
        except FailedParse:
            if self._is_cut_set():
                raise
            else:
                pass  # ignore, so next option is tried
        finally:
            self._cut_stack.pop()

    @contextmanager
    def _choice(self) -> Generator[None, None, None]:
        self.last_node = None
        with suppress(OptionSucceeded):
            yield

    @contextmanager
    def _optional(self) -> Generator[None, None, None]:
        self.last_node = None
        with self._choice(), self._option():
            yield

    @contextmanager
    def _group(self) -> Generator[None, None, None]:
        self._push_cst()
        try:
            yield
            self._merge_cst(extend=True)
        except Exception:
            self._pop_cst()
            raise

    @contextmanager
    def _if(self) -> Generator[None, None, None]:
        s = self.substate
        self._push_ast()
        self._lookahead += 1
        try:
            yield
        finally:
            self._pop_ast()  # simply discard
            self._lookahead -= 1
            self.substate = s

    @contextmanager
    def _ifnot(self) -> Generator[None, None, None]:
        try:
            with self._if():
                yield
        except FailedParse:
            pass
        else:
            self._error('', exclass=FailedLookahead)

    def _isolate(self, block: Callable[[], Any], drop: bool = False) -> Any:
        self._push_cst()
        try:
            block()
            cst = self.cst
        finally:
            self._pop_cst()

        if is_list(cst):
            cst = closure(cst)
        if not drop:
            self._append_cst(cst)
        return cst

    def _repeat(self, block: Callable[[], Any], prefix: Callable[[], Any] | None = None, dropprefix: bool = False) -> None:
        while True:
            with self._choice():
                with self._option():
                    p = self._pos

                    if prefix:
                        self._isolate(prefix, drop=dropprefix)
                        self._cut()

                    self._isolate(block)

                    if self._pos == p:
                        self._error('empty closure')
                return

    def _closure(self, block: Callable[[], Any], sep: Callable[[], Any] | None = None, omitsep: bool = False) -> Any:
        self._push_cst()
        try:
            self.cst = []
            with self._optional():
                block()
                self.cst = [self.cst]
            self._repeat(block, prefix=sep, dropprefix=omitsep)
            self.cst = closure(self.cst)
            return self._merge_cst()
        except Exception:
            self._pop_cst()
            raise

    def _positive_closure(self, block: Callable[[], Any], sep: Callable[[], Any] | None = None, omitsep: bool = False) -> Any:
        self._push_cst()
        try:
            block()
            self.cst = [self.cst]
            self._repeat(block, prefix=sep, dropprefix=omitsep)
            self.cst = closure(self.cst)
            return self._merge_cst()
        except Exception:
            self._pop_cst()
            raise

    def _empty_closure(self) -> closure:
        cst = closure([])
        self._append_cst(cst)
        return cst

    def _gather(self, block: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        return self._closure(block, sep=sep, omitsep=True)

    def _positive_gather(self, block: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        return self._positive_closure(block, sep=sep, omitsep=True)

    def _join(self, block: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        return self._closure(block, sep=sep)

    def _positive_join(self, block: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        return self._positive_closure(block, sep=sep)

    def _left_join(self, block: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        self.cst = left_assoc(self._positive_join(block, sep))
        self.last_node = self.cst
        return self.cst

    def _right_join(self, block: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        self.cst = right_assoc(self._positive_join(block, sep))
        self.last_node = self.cst
        return self.cst

    def _check_name(self, name: Any) -> None:
        name_str = str(name)
        if self.ignorecase or self.tokenizer.ignorecase:
            name_str = name_str.upper()
        if name_str in self.keywords:
            raise FailedKeywordSemantics(f'"{name_str}" is a reserved word')

    def _void(self) -> None:
        self.last_node = None

    def _any(self) -> Any:
        c = self._next()
        if c is None:
            self._trace_match(c, failed=True)
            self._error(c, exclass=FailedToken)
        self._trace_match(c)
        self._append_cst(c)
        return c

    def _skip_to(self, block: Callable[[], Any]) -> None:
        while not self._eof():
            try:
                with self._if():
                    block()
            except FailedParse:
                pass
            else:
                break
            pos = self._pos
            self._next_token()
            if self._pos == pos:
                self._next()
        block()

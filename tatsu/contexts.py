from __future__ import annotations

import ast as stdlib_ast
import functools
import sys
from contextlib import contextmanager, suppress
from copy import copy

from . import buffering, color, tokenizing
from .ast import AST
from .collections import OrderedSet as oset
from .exceptions import (
    FailedCut,
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
    MemoKey,
    ParseInfo,
    ParserConfig,
    ParseState,
    RuleInfo,
    RuleResult,
)
from .tokenizing import Tokenizer
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
    C_ENTRY,
    C_FAILURE,
    C_RECURSION,
    C_SUCCESS,
)

__all__ = ['ParseContext', 'tatsumasu', 'leftrec', 'nomemo']


# decorator for rule implementation methods
def tatsumasu(*params, **kwparams):
    def decorator(impl):
        @functools.wraps(impl)
        def wrapper(self):
            name = impl.__name__
            # remove the single leading and trailing underscore
            # that the parser generator added
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
def leftrec(impl):
    impl.is_leftrec = True
    impl.is_memoizable = False
    return impl


# Marks rules for which memoization has to be turned off
# (has no effect when left recursion is turned off)
def nomemo(impl):
    impl.is_memoizable = False
    return impl


# Marks rules marked as @name in the grammar
def isname(impl):
    impl.is_name = True
    return impl


class closure(list):
    def __hash__(self):
        return hash(tuple(self))


class ParseContext:
    def __init__(self, /, config: ParserConfig | None = None, **settings):
        super().__init__()
        config = ParserConfig.new(config, **settings)
        self.config = config
        self._active_config = self.config

        self._tokenizer: Tokenizer | None = None

        self._semantics = config.semantics

        self._initialize_caches()

    def _initialize_caches(self):
        self._statestack = [ParseState()]
        self._rule_stack = []
        self._cut_stack = [False]

        self._last_node = None
        self.substate = None
        self._lookahead = 0
        self._furthest_exception = None

        self._clear_memoization_caches()

    @property
    def active_config(self):
        return self._active_config

    @property
    def semantics(self):
        return self._semantics

    @property
    def encoding(self):
        return self.active_config.encoding

    @property
    def parseinfo(self):
        return self.active_config.parseinfo

    @property
    def trace(self):
        return self.active_config.trace

    @property
    def trace_length(self):
        return self.active_config.trace_length

    @property
    def trace_separator(self):
        return self.active_config.trace_separator

    @property
    def trace_filename(self):
        return self.active_config.trace_filename

    @property
    def comments_re(self):
        return self.active_config.comments_re

    @property
    def eol_comments_re(self):
        return self.active_config.eol_comments_re

    @property
    def whitespace(self):
        return self.active_config.whitespace

    @property
    def ignorecase(self):
        return self.active_config.ignorecase

    @property
    def nameguard(self):
        return self.active_config.nameguard

    @property
    def memoize_lookaheads(self):
        return self.active_config.memoize_lookaheads

    @property
    def left_recursion(self):
        return self.active_config.left_recursion

    @property
    def colorize(self):
        return self.active_config.colorize

    @property
    def keywords(self):
        return self._keywords

    @property
    def namechars(self):
        return self.active_config.namechars

    def _reset(self, config: ParserConfig):
        if self.active_config.colorize:
            color.init()
        self._initialize_caches()
        self._keywords = oset(config.keywords)
        self._semantics = config.semantics
        if hasattr(self.semantics, 'set_context'):
            self.semantics.set_context(self)
        return config

    def _set_furthest_exception(self, e):
        if (
            not self._furthest_exception
            or e.pos > self._furthest_exception.pos
        ):
            self._furthest_exception = e

    def parse(self, text, /, config: ParserConfig | None = None, **settings):
        config = self.config.replace_config(config)
        config = config.replace(**settings)
        self._active_config = config

        self._reset(config)
        if isinstance(text, tokenizing.Tokenizer):
            tokenizer = text
        elif text is not None:
            cls = self.tokenizercls
            tokenizer = cls(text, config=config)
        else:
            raise ParseError('No tokenizer or text')
        self._tokenizer = tokenizer
        start = self.active_config.effective_rule_name() or 'start'

        try:
            rule = self._find_rule(start)
            return rule()
        except FailedCut as e:
            self._set_furthest_exception(e.nested)
            raise self._furthest_exception from e
        except FailedParse as e:
            self._set_furthest_exception(e)
            raise self._furthest_exception from e
        finally:
            self._clear_memoization_caches()

    @property
    def tokenizer(self):
        return self._tokenizer

    @property
    def tokenizercls(self) -> type[Tokenizer]:
        if self.config.tokenizercls is None:
            return buffering.Buffer
        else:
            return self.config.tokenizercls

    @property
    def last_node(self):
        return self._last_node

    @last_node.setter
    def last_node(self, value):
        self._last_node = value

    @property
    def _pos(self):
        return self._tokenizer.pos

    def _clear_memoization_caches(self):
        self._memos = {}
        self._results = {}
        self._recursion_depth = 0

    def _goto(self, pos):
        self._tokenizer.goto(pos)

    def _next(self):
        return self._tokenizer.next()

    def _next_token(self, ruleinfo=None):
        if ruleinfo is None or not ruleinfo.name.lstrip('_')[:1].isupper():
            self._tokenizer.next_token()

    def _define(self, keys, list_keys=None):
        # if self.ast and isinstance(self.ast, AST):
        ast = AST()
        ast._define(keys, list_keys=list_keys)
        ast.update(self.ast)
        self.ast = ast

    @property
    def state(self):
        return self._statestack[-1]

    @property
    def ast(self):
        return self.state.ast

    @ast.setter
    def ast(self, value):
        self.state.ast = value

    def name_last_node(self, name):
        self.ast[name] = self.last_node

    def add_last_node_to_name(self, name):
        self.ast._setlist(name, self.last_node)

    @staticmethod
    def _safe_name(name, ast):
        while name in ast:
            name += '_'
        return name

    def ast_set(self, name, value, as_list=False):
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

    def ast_append(self, name, value):
        self.ast_set(name, value, as_list=True)

    def _push_ast(self, copyast=False):
        ast = copy(self.ast) if copyast else AST()
        self.state.pos = self._pos
        self._statestack.append(ParseState(ast=ast, pos=self._pos))

    def _pop_ast(self):
        self._statestack.pop()
        self.tokenizer.goto(self.state.pos)

    def _merge_ast(self):
        pos = self._pos
        ast = self.ast
        cst = self.cst
        self._statestack.pop()
        self.ast = ast
        self._extend_cst(cst)
        self.tokenizer.goto(pos)

    @property
    def cst(self):
        return self.state.cst

    @cst.setter
    def cst(self, value):
        self.state.cst = value

    def _push_cst(self):
        self._statestack.append(ParseState(ast=self.ast))

    def _pop_cst(self):
        ast = self.ast
        self._statestack.pop()
        self.ast = ast

    def _merge_cst(self, extend=True):
        cst = self.cst
        self._pop_cst()
        if extend:
            self._extend_cst(cst)
        else:
            self._append_cst(cst)
        return cst

    def _append_cst(self, node):
        self.last_node = node
        previous = self.cst
        if previous is None:
            self.cst = self._copy_node(node)
        elif is_list(previous):
            previous.append(node)
        else:
            self.cst = [previous, node]
        return node

    def _extend_cst(self, node):
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

    def _copy_node(self, node):
        if node is None:
            return None
        elif is_list(node):
            return node[:]
        else:
            return node

    def _is_cut_set(self):
        return self._cut_stack[-1]

    def _cut(self):
        self._trace_cut()
        self._cut_stack[-1] = True

        # Kota Mizushima et al say that we can throw away
        # memos for previous positions in the tokenizer under
        # certain circumstances, without affecting the linearity
        # of PEG parsing.
        #   https://kmizu.github.io/papers/paste513-mizushima.pdf
        #
        # We adopt the heuristic of always dropping the cache for
        # positions less than the current cut position. It remains to
        # be proven if doing it this way affects linearity. Empirically,
        # it hasn't.

        def prune(cache, cutpos):
            prune_dict(cache, lambda k, _: k[0] < cutpos)

        prune(self._memos, self._pos)

    def _memoization(self):
        return self.memoize_lookaheads or self._lookahead == 0

    def _rulestack(self):
        rulestack = [r.name for r in reversed(self._rule_stack)]
        stack = self.trace_separator.join(rulestack)
        if max(len(s) for s in stack.splitlines()) > self.trace_length:
            stack = stack[: self.trace_length]
            stack = stack.rsplit(self.trace_separator, 1)[0]
            stack += self.trace_separator
        return stack

    def _find_rule(self, name):
        self._error(name, exclass=FailedRef)
        return lambda: None  # makes static checkers happy

    def _find_semantic_action(self, name):
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

    def _trace(self, msg, *params, **kwargs):
        if self.trace:
            msg %= params
            info(str(msg), file=sys.stderr)

    def _trace_event(self, event):
        if self.trace:
            fname = ''
            if self.trace_filename:
                fname = self._tokenizer.line_info().filename + '\n'

            lookahead = self._tokenizer.lookahead().rstrip()
            if lookahead:
                lookahead = '\n' + lookahead
            self._trace(
                '%s %s%s%s',
                event + self._rulestack(),
                self._tokenizer.lookahead_pos(),
                color.Style.DIM + fname,
                color.Style.NORMAL + lookahead + color.Style.RESET_ALL,
                end='',
            )

    def _trace_entry(self):
        self._trace_event(color.Fore.YELLOW + color.Style.BRIGHT + C_ENTRY)

    def _trace_success(self):
        self._trace_event(color.Fore.GREEN + color.Style.BRIGHT + C_SUCCESS)

    def _trace_failure(self, ex=None):
        if isinstance(ex, FailedLeftRecursion):
            self._trace_recursion()
        else:
            self._trace_event(color.Fore.RED + color.Style.BRIGHT + C_FAILURE)

    def _trace_recursion(self):
        self._trace_event(color.Fore.RED + color.Style.BRIGHT + C_RECURSION)

    def _trace_cut(self):
        self._trace_event(color.Fore.MAGENTA + color.Style.BRIGHT + C_CUT)

    def _trace_match(self, token, name=None, failed=False):
        if self.trace:
            fname = ''
            if self.trace_filename:
                fname = self._tokenizer.line_info().filename + '\n'
            name = f'/{name}/' if name else ''

            if not failed:
                fgcolor = color.Fore.GREEN + C_SUCCESS
            else:
                fgcolor = color.Fore.RED + C_FAILURE

            lookahead = self._tokenizer.lookahead().rstrip()
            if lookahead:
                lookahead = '\n' + lookahead

            self._trace(
                color.Style.BRIGHT + fgcolor + "'%s' %s%s%s",
                token,
                name,
                color.Style.DIM + fname,
                color.Style.NORMAL + lookahead + color.Style.RESET_ALL,
                end='',
            )

    def _make_exception(self, item, exclass=FailedParse):
        rulestack = (r.name for r in self._rule_stack[::-1])
        return exclass(self.tokenizer, rulestack, item)

    def _error(self, item, exclass=FailedParse):
        raise self._make_exception(item, exclass=exclass)

    def _fail(self):
        self._error('fail')

    def _get_parseinfo(self, name, pos):
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
    def rule(self):
        return self._rule_stack[-1]

    @property
    def memokey(self):
        return MemoKey(self._pos, self.rule, self.substate)

    def _memoize(self, key, memo):
        if self._memoization() and key.rule.is_memoizable:
            self._memos[key] = memo
        return memo

    def _forget(self, key):
        self._memos.pop(key, None)

    def _memo_for(self, key):
        return self._memos.get(key)

        # if isinstance(memo, FailedLeftRecursion):
        #     memo = self._results.get(key, memo)

    def _mkresult(self, node):
        return RuleResult(node, self._pos, self.substate)

    def _save_result(self, key, result):
        if is_list(result.node):
            result = RuleResult(
                closure(result.node), result.newpos, result.newstate,
            )
        self._results[key] = result

    def _is_recursive(self, ruleinfo):
        return ruleinfo.is_leftrec

    def _set_left_recursion_guard(self, key):
        ex = self._make_exception(key.rule.name, exclass=FailedLeftRecursion)
        self._memoize(key, ex)

    def _call(self, ruleinfo):
        self._rule_stack += [ruleinfo]
        pos = self._pos
        try:
            self._trace_entry()

            self._last_node = None

            result = self._recursive_call(ruleinfo)
            node, newpos, newstate = result

            self._goto(newpos)
            self.substate = newstate
            self._append_cst(node)

            self._trace_success()

            return node
        except FailedPattern:
            self._error(f'Expecting <{ruleinfo.name}>')
        except FailedParse as e:
            self._goto(pos)
            self._set_furthest_exception(e)
            self._trace_failure(e)
            raise
        finally:
            self._rule_stack.pop()

    def _clear_recursion_errors(self):
        def filter(key, value):
            return isinstance(value, FailedLeftRecursion)

        prune_dict(self._memos, filter)

    def _recursive_call(self, ruleinfo):
        self._next_token(ruleinfo)
        key = self.memokey

        if not ruleinfo.is_leftrec:
            return self._invoke_rule(ruleinfo, key)
        elif not self.left_recursion:
            self._error('Left recursion detected', exclass=FailedLeftRecursion)

        self._recursion_depth += 1
        if key in self._results:
            result = self._results[key]
        else:
            result = self._make_exception(
                ruleinfo.name, exclass=FailedLeftRecursion,
            )
            self._results[key] = result

            initial = self._pos
            lastpos = initial - 1
            while True:
                try:
                    self._clear_recursion_errors()
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
        self._recursion_depth -= 1

        if isinstance(result, Exception):
            raise result  # pylint: disable=raising-non-exception

        return result

    def _invoke_rule(self, ruleinfo, key):
        memo = self._memo_for(key)
        if isinstance(memo, Exception):
            raise memo
        if memo:
            return memo
        self._set_left_recursion_guard(key)

        self._push_ast()
        try:
            try:
                self._next_token(ruleinfo)
                ruleinfo.impl(self)
                node = self._get_node(key.pos, ruleinfo)
                node = self._invoke_semantic_rule(ruleinfo, node)
                result = self._mkresult(node)
                self._memoize(key, result)
                return result
            except FailedSemantics as e:
                self._error(str(e))
        except FailedParse as e:
            self._memoize(key, e)
            raise
        finally:
            self._pop_ast()

    def _get_node(self, pos, ruleinfo):
        node = self.ast
        if not node:
            node = tuple(self.cst) if is_list(self.cst) else self.cst
        elif '@' in node:
            node = node['@']  # override the AST
        elif self.parseinfo:
            node.set_parseinfo(self._get_parseinfo(ruleinfo.name, pos))
        return node

    def _invoke_semantic_rule(self, rule, node):
        semantic_rule, postproc = self._find_semantic_action(rule.name)
        if semantic_rule:
            node = semantic_rule(
                node, *(rule.params or ()), **(rule.kwparams or {}),
            )
        if callable(postproc):
            postproc(self, node)  # pylint: disable=not-callable
        if rule.is_name:
            self._check_name(node)
        return node

    def _token(self, token):
        self._next_token()
        if self.tokenizer.match(token) is None:
            self._trace_match(token, failed=True)
            self._error(token, exclass=FailedToken)
        self._trace_match(token)
        self._append_cst(token)
        return token

    def _constant(self, literal):
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

    def _alert(self, message, level):
        self._next_token()
        self._trace_match(f'{"^" * level}`{message}`', failed=True)
        self.state.alerts.append(Alert(message=message, level=level))

    def _pattern(self, pattern):
        token = self.tokenizer.matchre(pattern)
        if token is None:
            self._trace_match('', pattern, failed=True)
            self._error(pattern, exclass=FailedPattern)
        self._trace_match(token, pattern)
        self._append_cst(token)
        return token

    def _eof(self):
        return self.tokenizer.atend()

    def _eol(self):
        return self.tokenizer.ateol()

    def _check_eof(self):
        self._next_token()
        if not self.tokenizer.atend():
            self._error(
                'Expecting end of text', exclass=FailedExpectingEndOfText,
            )

    @contextmanager
    def _try(self):
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
    def _option(self):
        self.last_node = None
        self._cut_stack += [False]
        try:
            with self._try():
                yield
            raise OptionSucceeded()
        except FailedCut:
            raise
        except FailedParse as e:
            if self._is_cut_set():
                raise FailedCut(e) from e
        finally:
            self._cut_stack.pop()

    @contextmanager
    def _choice(self):
        self.last_node = None
        with suppress(OptionSucceeded):
            yield

    @contextmanager
    def _optional(self):
        self.last_node = None
        with self._choice(), self._option():
            yield

    @contextmanager
    def _group(self):
        self._push_cst()
        try:
            yield
            self._merge_cst(extend=True)
        except Exception:
            self._pop_cst()
            raise

    @contextmanager
    def _if(self):
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
    def _ifnot(self):
        try:
            with self._if():
                yield
        except FailedParse:
            pass
        else:
            self._error('', exclass=FailedLookahead)

    def _isolate(self, block, drop=False):
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

    def _repeat(self, block, prefix=None, dropprefix=False):
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

    def _closure(self, block, sep=None, omitsep=False):
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

    def _positive_closure(self, block, sep=None, omitsep=False):
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

    def _empty_closure(self):
        cst = closure([])
        self._append_cst(cst)
        return cst

    def _gather(self, block, sep):
        return self._closure(block, sep=sep, omitsep=True)

    def _positive_gather(self, block, sep):
        return self._positive_closure(block, sep=sep, omitsep=True)

    def _join(self, block, sep):
        return self._closure(block, sep=sep)

    def _positive_join(self, block, sep):
        return self._positive_closure(block, sep=sep)

    def _left_join(self, block, sep):
        self.cst = left_assoc(self._positive_join(block, sep))
        self.last_node = self.cst
        return self.cst

    def _right_join(self, block, sep):
        self.cst = right_assoc(self._positive_join(block, sep))
        self.last_node = self.cst
        return self.cst

    def _check_name(self, name):
        name = str(name)
        if self.ignorecase or self.tokenizer.ignorecase:
            name = name.upper()
        if name in self.keywords:
            raise FailedKeywordSemantics(f'"{name}" is a reserved word')

    def _void(self):
        self.last_node = None

    def _any(self):
        c = self._next()
        if c is None:
            self._trace_match(c, failed=True)
            self._error(c, exclass=FailedToken)
        self._trace_match(c)
        self._append_cst(c)
        return c

    def _skip_to(self, block):
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

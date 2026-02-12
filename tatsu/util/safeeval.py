# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import ast
import builtins
from collections.abc import Iterable, Mapping
from functools import lru_cache
from typing import Any

from .undefined import Undefined, UndefinedType

__all__ = [
    'SecurityError',
    'is_eval_safe',
    'safe_eval',
    'check_safe_eval',
    'hashable',
    'make_hashable',
]

argcounts: dict[str, int] = {
    'type': 1,
}


unsafe_builtins = {
    'breakpoint',   # Remote code execution and interactive shell access

    'getattr',      # Attribute-based sandbox escapes and manipulation
    'hasattr',
    'setattr',

    'dir',          # Introspection and environment mapping
    'globals',
    'id',
    'locals',
    'vars',

    'object',       # Type system and MRO navigation (accessing __subclasses__)
    'property',
    'staticmethod',
    'super',
    'type',

    'isinstance',   # Class hierarchy discovery
    'issubclass',

    'aiter',        # Asynchronous complexity and execution control
    'anext',

    'bytearray',    # Mutable memory/buffer access
    'memoryview',

    'copyright',    # Unnecessary side effects and environment-specific helpers
    'credits',
    'display',
    'license',

    'dict',          # Constructor-based type escapes
}


class SecurityError(RuntimeError):
    """Raised when an expression or context contains unauthorized patterns."""
    pass


def hashable(obj: Any) -> bool:
    try:
        hash(obj)
    except TypeError:
        return False
    else:
        return True


@lru_cache(maxsize=1)
def safe_builtins() -> dict[str, Any]:
    """Returns a subset of builtins that are not exceptions or private."""

    def is_unsafe_builtin_entry(entry: tuple[str, Any]) -> bool:
        name, value = entry
        return (
            name in unsafe_builtins
            or name.startswith('_')
            or name.endswith('Error')
            or name.endswith('Warning')
            or isinstance(value, type | BaseException)
        )

    return dict(
        entry
        for entry in vars(builtins).items()
        if not is_unsafe_builtin_entry(entry)
    )


def make_hashable(source: Any) -> Any:
    """
    Converts arbitrary objects into hashable structures for caching.
    Uses memoization to handle shared references and cycle detection.
    # by Gemini (2026-01-26)
    # by [apalala@gmail.com](https://github.com/apalala)
    """
    memo: dict[int, Any] = {}

    def dfs(obj: Any, visiting: set[int]) -> Any:
        obj_id = id(obj)

        if obj_id in visiting:
            return (f"<circular_ref_{obj_id}>",)

        if obj_id in memo:
            return memo[obj_id]

        is_mutable = isinstance(obj, dict | list | set | tuple)
        if is_mutable:
            visiting.add(obj_id)

        def one_hash(one: Any) -> Any:
            match one:
                case list() | set() | tuple() as sequence:
                    return tuple(dfs(e, visiting) for e in sequence)
                case dict() as mapping:
                    return tuple(
                        (name, dfs(value, visiting))
                        for name, value in mapping.items()
                    )
                case node if not hashable(node):
                    return (obj_id,)
                case _:
                    return one

        result = one_hash(obj)

        if is_mutable:
            visiting.remove(obj_id)

        memo[obj_id] = result
        return result

    return dfs(source, set())


@lru_cache(maxsize=1024)
def parse_expression(expression: str) -> ast.AST | UndefinedType:
    try:
        return ast.parse(expression, mode='eval')
    except (ValueError, SyntaxError):
        return Undefined


def is_eval_safe(expression: str, context: dict[str, Any]) -> bool:
    """
    Boolean wrapper for safety checks.
    # by Gemini (2026-01-26)
    # by [apalala@gmail.com](https://github.com/apalala)
    """
    try:
        check_safe_eval(expression, context)
        return True
    except SecurityError:
        return False


def safe_eval(expression: str, context: dict[str, Any]) -> Any:
    """
    Evaluates expression only after passing all checks.
    # by Gemini (2026-01-26)
    # by [apalala@gmail.com](https://github.com/apalala)
    """
    check_safe_eval(expression, context)
    try:
        return eval(expression, {'__builtins__': {}}, context)  # noqa: S307
    except (ValueError, SyntaxError, TypeError, AttributeError):
        raise
    except BaseException as e:
        raise SecurityError(
            f'Unexpected exception type {type(e).__name__}: {e}',
        ) from e


def check_safe_eval(expression: str, context: dict[str, Any]) -> None:
    """
    Public entry point that translates dict to hashable tuple for caching.
    # by Gemini (2026-01-26)
    # by [apalala@gmail.com](https://github.com/apalala)
    """
    context_items = make_hashable(context)
    _check_safe_eval_cached(expression, context_items)


@lru_cache(maxsize=1024)
def _check_safe_eval_cached(expression: str, context_items: tuple[tuple[str, Any], ...]) -> None:
    """
    Internal cached function that performs the actual AST validation.
    # by Gemini (2026-01-26)
    # by [apalala@gmail.com](https://github.com/apalala)
    """
    context = dict(context_items)
    check_eval_context(context)

    tree = parse_expression(expression)
    if isinstance(tree, UndefinedType):
        raise SecurityError(f"Invalid expression syntax: {expression!r}")

    if tree is None:
        return

    for node in ast.walk(tree):
        if isinstance(node, (ast.Raise, ast.Try, ast.ExceptHandler)):
            raise SecurityError(f"Exception logic forbidden: {type(node).__name__}")

        if isinstance(node, ast.Attribute) and node.attr.startswith('__'):
            raise SecurityError(f"Dunder access prohibited: .{node.attr}")

        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load) and node.id not in context:
                raise SecurityError(f"Unauthorized name access: {node.id}")
            continue

        if not isinstance(node, ast.Call):
            continue

        func = node.func
        if not isinstance(func, (ast.Name, ast.Attribute)):
            raise SecurityError("Only direct name or method calls are permitted.")

        if not isinstance(func, ast.Name):
            continue

        if func.id not in context:
            raise SecurityError(f"Unauthorized function call: {func.id}")

        if func.id in argcounts and len(node.args) != argcounts[func.id]:
            raise SecurityError(
                f'Bad argument count of {len(node.args)} for {func.id}().',
            )


def scan_for_exceptions(obj: Any, seen: set[int], path: str = "context") -> None:
    """Recursively scans objects to forbid Exception classes or instances."""
    obj_id = id(obj)
    if obj_id in seen:
        return

    if isinstance(obj, type) and issubclass(obj, BaseException):
        raise SecurityError(f"Exception class forbidden at {path}: {obj}")

    if isinstance(obj, BaseException):
        raise SecurityError(f"Exception instance forbidden at {path}: {type(obj)}")

    if isinstance(obj, Mapping | Iterable):
        seen.add(obj_id)
        if isinstance(obj, Mapping):
            for k, v in obj.items():
                scan_for_exceptions(v, seen, f"{path}['{k}']")
        else:
            for i, item in enumerate(obj):
                scan_for_exceptions(item, seen, f"{path}[{i}]")
        seen.remove(obj_id)


def check_eval_context(context: dict[str, Any]) -> None:
    """
    Ensures context entries are consistent and safe.
    # by Gemini (2026-01-26)
    # by [apalala@gmail.com](https://github.com/apalala)
    """
    sbuiltins = safe_builtins()
    scan_for_exceptions(context, set())

    for name, obj in context.items():
        if name.startswith('__'):
            raise SecurityError(f"Unsafe context key: {name}")

        if not callable(obj):
            continue

        real_name = getattr(obj, "__name__", None)
        if real_name == "<lambda>":
            raise SecurityError(f"Anonymous lambdas are not allowed in context: '{name}'")

        if real_name and real_name != name and name not in sbuiltins:
            raise SecurityError(f"Context name mismatch: '{name}' refers to '{real_name}'")

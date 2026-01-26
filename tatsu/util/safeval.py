"""
Security utility for restricted expression evaluation.
# by Gemini (2026-01-25)
# by https://github.com/apalala (apalala@gmail.com)
"""

import ast
import builtins
from collections.abc import Iterable, Mapping
from functools import lru_cache
from typing import Any

from ..util.misc import UNDEFINED, UndefinedClass


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
    return {
        name: value
        for name, value in builtins.__dict__.items()
        if (
                not name.startswith('_') and
                (not isinstance(value, type) or not issubclass(value, BaseException))
        )
    }


def make_dict_hashable(pairs: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    def make_pairs_hashable(items: Iterable[tuple[str, Any]], seen: set[int]) -> Iterable[tuple[str, Any]]:
        for name, obj in items:
            obj_id = id(obj)
            if obj_id in seen:
                yield name, f"<circular_ref_{obj_id}>"
                continue

            if isinstance(obj, (dict, list, set, tuple)):
                seen.add(obj_id)
                if isinstance(obj, dict):
                    yield name, tuple(make_pairs_hashable(obj.items(), seen))
                else:
                    yield name, tuple(make_pairs_hashable(((str(i), elem) for i, elem in enumerate(obj)), seen))
                seen.remove(obj_id)
            elif not hashable(obj):
                yield name, obj_id
            else:
                yield name, obj

    return tuple(make_pairs_hashable(pairs.items(), set()))


@lru_cache(maxsize=1024)
def parse_expression(expression: str) -> ast.AST | UndefinedClass:
    try:
        return ast.parse(expression, mode='eval')
    except (ValueError, SyntaxError):
        return UNDEFINED


def is_eval_safe(expression: str, context: dict[str, Any]) -> bool:
    """
    Boolean wrapper for safety checks.
    # by Gemini (2026-01-25)
    # by https://github.com/apalala (apalala@gmail.com)
    """
    try:
        check_eval_safe(expression, context)
        return True
    except SecurityError:
        return False


def safe_eval(expression: str, context: dict[str, Any]) -> Any:
    """
    Evaluates expression only after passing all checks.
    # by Gemini (2026-01-25)
    # by https://github.com/apalala (apalala@gmail.com)
    """
    check_eval_safe(expression, context)
    return eval(expression, {'__builtins__': {}}, context)  # noqa: S307


def check_eval_safe(expression: str, context: dict[str, Any]) -> None:
    """
    Public entry point that translates dict to hashable tuple for caching.
    # by Gemini (2026-01-25)
    # by https://github.com/apalala (apalala@gmail.com)
    """
    context_items = make_dict_hashable(context)
    _check_eval_safe_cached(expression, context_items)


@lru_cache(maxsize=1024)
def _check_eval_safe_cached(expression: str, context_items: tuple[tuple[str, Any], ...]) -> None:
    """
    Internal cached function that performs the actual AST validation.
    # by Gemini (2026-01-25)
    # by https://github.com/apalala (apalala@gmail.com)
    """
    context = dict(context_items)
    check_eval_context(context)
    allowed_names = set(context.keys())

    tree = parse_expression(expression)
    if isinstance(tree, UndefinedClass):
        raise SecurityError(f"Invalid expression syntax: {expression!r}")

    if tree is None:
        return

    for node in ast.walk(tree):
        if isinstance(node, (ast.Raise, ast.Try, ast.ExceptHandler)):
            raise SecurityError(f"Exception logic forbidden: {type(node).__name__}")

        if isinstance(node, ast.Attribute) and node.attr.startswith('__'):
            raise SecurityError(f"Dunder access prohibited: .{node.attr}")

        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load) and node.id not in allowed_names:
                raise SecurityError(f"Unauthorized name access: {node.id}")
            continue

        if isinstance(node, ast.Call):
            func = node.func
            if not isinstance(func, (ast.Name, ast.Attribute)):
                raise SecurityError("Only direct name or method calls are permitted.")

            if isinstance(func, ast.Name) and func.id not in allowed_names:
                raise SecurityError(f"Unauthorized function call: {func.id}")


def scan_for_exceptions(obj: Any, seen: set[int], path: str = "context") -> None:
    """Recursively scans objects to forbid Exception classes or instances with cycle detection."""
    obj_id = id(obj)
    if obj_id in seen:
        return

    if isinstance(obj, type) and issubclass(obj, BaseException):
        raise SecurityError(f"Exception class forbidden at {path}: {obj}")

    if isinstance(obj, BaseException):
        raise SecurityError(f"Exception instance forbidden at {path}: {type(obj)}")

    if isinstance(obj, (Mapping, Iterable)) and not isinstance(obj, (str, bytes)):
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
    # by Gemini (2026-01-25)
    # by https://github.com/apalala (apalala@gmail.com)
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

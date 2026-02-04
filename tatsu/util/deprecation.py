# by [apalala@gmail.com](https://github.com/apalala)
# by Gemini (2026-01-29)

from __future__ import annotations

import functools
import inspect
import warnings
from collections.abc import Callable
from typing import Any

from .misc import fqn

type Decorator = Callable[[Callable[..., Any]], Callable[..., Any]]
type AnyCallable = Callable[..., Any]


def deprecated(replacement: AnyCallable | None = None) -> Callable[[AnyCallable], AnyCallable]:
    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-01-30)

    def decorator(func: AnyCallable) -> AnyCallable:
        # Get FQN for the deprecated function and its replacement
        func_name = fqn(func)

        if replacement is not None:
            repl_name = fqn(replacement)
            msg = f"\nDEP `{func_name}()` is deprecated! \nUSE `{repl_name}()` instead."
        else:
            msg = f"\n`DEP {func_name}()` is deprecated and will be removed in a future version."

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                msg,
                category=DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def deprecated_params(**params_map: str | None) -> Decorator:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not params_map:
                return func(*args, **kwargs)

            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)
            actual_args = bound_args.arguments

            # Access __name__ safely to satisfy the linter
            func_name = getattr(func, "__name__", str(func))

            for old_p, new_p in params_map.items():
                if old_p not in actual_args:
                    continue

                msg = f"Parameter '{old_p}' is deprecated."
                if new_p:
                    msg += f" Use '{new_p}' instead."
                warnings.warn(
                    f"{msg} (in {func_name})",
                    category=DeprecationWarning,
                    stacklevel=2,
                )

                if not new_p:
                    continue

                if new_p not in actual_args:
                    kwargs[new_p] = actual_args.pop(old_p)
                    continue

                actual_args.pop(old_p)
                warnings.warn(
                    f"Both '{old_p}' and '{new_p}' provided. Using '{new_p}'.",
                    category=RuntimeWarning,
                    stacklevel=2,
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator

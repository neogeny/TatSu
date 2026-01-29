from __future__ import annotations

import dataclasses
import importlib
import types
from typing import Any, Self

from ..util import asjson
from . import Undefined


@dataclasses.dataclass
class Config:
    def __post_init__(self):  # pylint: disable=W0235
        pass

    @classmethod
    def new(cls, config: Self | None = None, **settings: Any) -> Self:
        result = cls()
        result = result.replace_config(config)
        result = result.replace(**settings)
        assert isinstance(result, cls) and dataclasses.is_dataclass(result)
        return result

    def _find_common(self, **settings: Any) -> dict[str, Any]:
        hard = settings.pop('hard', False)
        return {
            name: value
            for name, value in settings.items()
            if (
                hasattr(self, name)
                and (hard or (value is not None and value is not Undefined))
            )
        }

    def replace_config(self, other: Config | None = None) -> Self:
        if other is None:
            return self
        elif not isinstance(other, type(self)):
            raise TypeError(f'Unexpected type {type(other).__name__}')
        else:
            return self.replace(**other.asdict())

    def merge_config(self, other: Config | None = None) -> Self:
        if other is None:
            return self
        elif not isinstance(other, type(self)):
            raise TypeError(f'Unexpected type {type(other).__name__}')
        else:
            return self.merge(**other.asdict())

    # non-init fields cannot be used as arguments in `replace`, however
    # they are values returned by `vars` and `dataclass.asdict` so they
    # must be filtered out.
    # If the `ParserConfig` dataclass drops these fields, then this filter can be removed
    def _filter_non_init_fields(self, settings: dict[str, Any]) -> dict[str, Any]:
        noninit = [f.name for f in dataclasses.fields(self) if not f.init]
        return {
            name: value for name, value in settings.items()
            if name not in noninit
        }

    def replace(self, **settings: Any) -> Self:
        settings = self._filter_non_init_fields(settings)
        overrides = self._find_common(**settings)
        assert dataclasses.is_dataclass(self)
        return dataclasses.replace(self, **overrides)

    def hard_replace(self, **settings: Any) -> Self:
        return self.replace(**settings)

    def merge(self, **settings: Any) -> Self:
        overrides = self._find_common(**settings)
        overrides = {
            name: value
            for name, value in overrides.items()
            if getattr(self, name, None) is None
        }
        return self.replace(**overrides)

    def asdict(self):
        return {
            f.name: getattr(self, f.name)
            for f in dataclasses.fields(self) if f.name != 'temp_cache'
        }

    def diff(self, other: Self | None) -> list[tuple[str, Any, Any]]:
        if other is None:
            return []

        result: list[tuple[str, Any, Any]] = []
        for name, value in self.asdict().items():
            ovalue = getattr(other, name, Undefined)
            if value != ovalue:
                result.append((name, value, ovalue))
        return result

    def diffs(self, other: Self | None) -> str:
        return '\n'.join(
            f'{name} {value!r} {ovalue!r}'
            for name, value, ovalue in self.diff(other)
        )

    def __json__(self, seen=None):
        return asjson(self.asdict(), seen=seen)

    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-01-29)
    def __getstate__(self) -> dict[str, Any]:
        state = self.asdict()
        for name, value in tuple(state.items()):
            if isinstance(value, types.ModuleType) or type(value).__name__ == 'module':
                state[f'{name}__mod__'] = value.__name__
                del state[name]
                continue

            if isinstance(value, type):
                state[f'{name}__cls__'] = f"{value.__module__}.{value.__name__}"
                del state[name]
                continue

            # NOTE
            #   If we get here, it's something else (like a lambda or socket)
            #   The vars(value) idea could go here as a last resort,
            #   but be wary of the recursive PicklingError.
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        for key, value in state.items():
            if key.endswith('__mod__'):
                real_name = key.replace('__mod__', '')
                object.__setattr__(self, real_name, importlib.import_module(value))
                continue

            if key.endswith('__cls__'):
                real_name = key.replace('__cls__', '')
                mod_name, cls_name = value.rsplit('.', 1)
                mod = importlib.import_module(mod_name)
                object.__setattr__(self, real_name, getattr(mod, cls_name))
                continue

            object.__setattr__(self, key, value)

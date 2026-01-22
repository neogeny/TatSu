from collections.abc import Callable, MutableMapping
from typing import Any

from .objectmodel import BaseNode

# NOTE:
#   __REGISTRY is an alias for the modules vars()/ __dict__.
#   That allows for synthesized types to reside within this module.
__REGISTRY: MutableMapping[str, Callable] = vars()


class _Synthetic(BaseNode):
    pass


def synthesize(name: str, bases: tuple[type, ...], *args: Any, **kwargs: Any) -> Callable:
    typename = f'{__name__}.{name}'

    if not isinstance(bases, tuple):
        bases = (bases,)

    if _Synthetic not in bases:
        bases = (*bases, _Synthetic)

    constructor = __REGISTRY.get(typename)
    if not constructor:
        constructor = type(name, bases, kwargs)
        typename = constructor.__name__
        __REGISTRY[typename] = constructor

    return constructor


def registered_synthetics() -> dict[str, Callable]:
    return dict(__REGISTRY)

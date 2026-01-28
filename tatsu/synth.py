from collections.abc import Callable, MutableMapping
from typing import Any

from .objectmodel import BaseNode

# NOTE:
#   __REGISTRY is an alias for the modules vars()/ __dict__.
#   That allows for synthesized types to reside within this module.
__REGISTRY: MutableMapping[str, Callable] = vars()

__all__ = ['SynthNode', 'registered_synthetics', 'synthesize']


class SynthNode(BaseNode):
    pass


def synthesize(name: str, bases: tuple[type, ...], **kwargs: Any) -> Callable:
    typename = f'{__name__}.{name}'

    if not isinstance(bases, tuple):
        raise TypeError(f'bases must be a tuple, not {type(bases)}')

    if SynthNode not in bases:
        bases = (*bases, SynthNode)

    constructor = __REGISTRY.get(typename)
    if not constructor:
        constructor = type(name, bases, kwargs)
        typename = constructor.__name__
        __REGISTRY[typename] = constructor

    return constructor


def registered_synthetics() -> dict[str, Callable]:
    return dict(__REGISTRY)

from collections.abc import Callable, MutableMapping
from typing import Any

from .objectmodel import BaseNode

# NOTE:
#   __REGISTRY is an alias for the modules vars()/ __dict__.
#   That allows for synthesized types to reside within this module.
__registry: MutableMapping[str, Callable] = vars()

__all__ = ['SynthNode', 'registered_synthetics', 'synthesize']


class SynthNode(BaseNode):
    pass


def synthesize(name: str, bases: tuple[type, ...], **kwargs: Any) -> Callable:
    if not isinstance(bases, tuple):
        raise TypeError(f'bases must be a tuple, not {type(bases)}')

    if SynthNode not in bases:
        bases = (*bases, SynthNode)

    constructor = __registry.get(name)
    if not constructor:
        constructor = type(name, bases, kwargs)
        __registry[name] = constructor

    return constructor


def registered_synthetics() -> dict[str, Callable]:
    return dict(__registry)

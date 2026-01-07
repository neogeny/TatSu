from collections.abc import Callable, MutableMapping
from typing import Any

# NOTE:
#   __REGISTRY is an alias for the modules vars()/ __dict__.
#   That allows for synthesized types to reside within this module.
__REGISTRY: MutableMapping[str, Callable] = vars()


class _Synthetic:
    def __reduce__(self) -> tuple[Any, ...]:
        return (
            synthesize(type(self).__name__, type(self).__bases__),
            (),
            vars(self),
        )


def synthesize(name: str, bases: tuple[type, ...]) -> Callable:
    typename = f'{__name__}.{name}'

    if not isinstance(bases, tuple):
        bases = (bases,)

    if _Synthetic not in bases:
        bases += (_Synthetic,)

    constructor = __REGISTRY.get(typename)
    if not constructor:
        constructor = type(name, bases, {})
        typename = constructor.__name__
        __REGISTRY[typename] = constructor

    return constructor


def registered_symthetics() -> dict[str, Callable]:
    return dict(__REGISTRY)

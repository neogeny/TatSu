from collections.abc import MutableMapping
from typing import Any

__REGISTRY: MutableMapping[str, Any] = vars()


class _Synthetic:
    def __reduce__(self) -> tuple[Any, ...]:
        return (
            synthesize(type(self).__name__, type(self).__bases__),
            (),
            vars(self),
        )


def synthesize(name: str, bases: tuple[type, ...]) -> type:
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

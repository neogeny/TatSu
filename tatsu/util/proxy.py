# idea: off
# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations
from typing import Any


class FastProxy[T]:
    def __init__(self, obj: T):
        object.__setattr__(self, '_obj', obj)

    def __getattr__(self, name: str) -> Any:
        value = getattr(self._obj, name)
        if callable(value):
            unbound = getattr(type(self._obj), name)
            if hasattr(unbound, "__get__"):
                # This handles both methods and properties correctly
                bound = unbound.__get__(self._obj)
                object.__setattr__(self, name, bound)
                return bound

        return value

    def __setattr__(self, name: str, value: Any) -> None:
        if name == '_obj' or name not in vars(self._obj):
            super().__setattr__(name, value)
        else:
            setattr(self._obj, name, value)

    def __dir__(self) -> list[str]:
        return sorted(set(super().__dir__()) | set(dir(self._obj)))

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._obj!r}))'


if __name__ == '__main__':
    class C:
        def __init__(self):
            self._x = 0

        @property
        def x(self):
            return self._x

        @x.setter
        def x(self, value):
            self._x = value

        @property
        def dx(self) -> int:
            return 2 * self._x

        def incr(self) -> int:
            self.x += 1
            return self.x

        def whoami(self) -> str:
            return f'I am {type(self).__name__} {self!r}'

    c = C()
    p = FastProxy(c)

    print(p.incr())
    assert c.x == 1, c.x
    assert p.x == 1, p.x

    print(c.incr())
    assert c.x == 2, c.x
    assert p.x == 2, p.x

    class Over[C](FastProxy[C]):
        def __init__(self, obj: C):
            super().__init__(obj)
            object.__setattr__(self, 'x', None)
            self.y = 66

        @property
        def x(self):
            return 42

        @x.setter
        def x(self, value):
            return

        def incr(self) -> int:
            return self._obj.incr()

    o = Over(c)
    print(o.incr())
    print(o.dx)

    print(c.whoami())
    print(o.whoami())

    print(type(c))
    print(type(o))

    print(c.incr)
    print(p.incr)
    print(o.incr)

    print(C.x)
    print(p.x)
    print(Over.x)

    print(c.incr())
    assert o.x == 42, o.x
    assert p.x == 4, p.x
    assert c.x == 4, c.x

    o.y = 22

    assert not hasattr(c, 'y')
    assert not hasattr(p, 'y')
    assert hasattr(o, 'y')
    assert o._obj is c

    print(vars(o))

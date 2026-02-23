# idea: off
# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations
from typing import Any
import copy
from tatsu.util.typetools import isproperty


class Proxy[T]:
    def __init__(self, obj: T):
        # We store 'obj' as T to help with type inference
        object.__setattr__(self, '_obj', obj)

    def __getattr__(self, name: str) -> Any:
        value = getattr(self._obj, name)

        if callable(value) or isproperty(self._obj, name):
            unbound = getattr(type(self._obj), name)
            setattr(type(self), name, copy.copy(unbound))

        return value

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self._obj, name):
            setattr(self._obj, name, value)
        else:
            super().__setattr__(name, value)

    def __dir__(self) -> list[str]:
        return dir(self._obj)


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

        def incr(self) -> int:
            self.x += 1
            return self.x

    c = C()
    p = Proxy(c)
    print(p.incr())
    assert c.x == 1, c.x
    assert p.x == 1, p.x

    class Over[C](Proxy[C]):
        def __init__(self, c: C):
            super().__init__(c)
            object.__setattr__(self, 'x', None)
            self.y = 66

        @property
        def x(self):
            # return self._x
            print(f'Overriden {self._x}')
            return 25

        @x.setter
        def x(self, value):
            return
            self._x = value

        # def incr(self) -> int:
        #     self.x += 7
        #     return self.x

    o = Over(c)
    print(o.incr())

    print(c.incr)
    print(p.incr)
    print(o.incr)

    print(C.x)
    print(Proxy.x)
    print(Over.x)

    assert o.x == 25, o.x
    assert p.x == 26, p.x
    assert c.x == 26, c.x

    o.y = 22

    assert not hasattr(c, 'y')
    assert not hasattr(p, 'y')
    assert hasattr(o, 'y')

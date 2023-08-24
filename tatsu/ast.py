from __future__ import annotations

import operator
from functools import reduce

from tatsu.util import asjson, is_list


class AST(dict):
    _frozen = False

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.update(*args, **kwargs)
        self._frozen = True

    @property
    def frozen(self):
        return self._frozen

    @property
    def parseinfo(self):
        try:
            return super().__getitem__('parseinfo')
        except KeyError:
            pass

    def set_parseinfo(self, value):
        super().__setitem__('parseinfo', value)

    def copy(self):
        return self.__copy__()  # pylint: disable=unnecessary-dunder-call

    def asjson(self):
        return asjson(self)

    def _set(self, key, value, force_list=False):
        key = self._safekey(key)
        previous = self.get(key)

        if previous is None and force_list:
            value = [value]
        elif previous is None:
            pass
        elif is_list(previous):
            value = previous + [value]
        else:
            value = [previous, value]

        super().__setitem__(key, value)

    def _setlist(self, key, value):
        return self._set(key, value, force_list=True)

    def __copy__(self):
        return AST(self)

    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
        key = self._safekey(key)
        if key in self:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        self._set(key, value)

    def __delitem__(self, key):
        key = self._safekey(key)
        super().__delitem__(key)

    def __setattr__(self, name, value):
        if self._frozen and name not in vars(self):
            raise AttributeError(
                f'{type(self).__name__} attributes are fixed. '
                f' Cannot set attribute "{name}".'
            )
        super().__setattr__(name, value)

    def __getattr__(self, name):
        key = self._safekey(name)
        if key in self:
            return self[key]
        elif name in self:
            return self[name]

        try:
            return super().__getattribute__(name)
        except AttributeError:
            return None

    def __hasattribute__(self, name):
        try:
            super().__getattribute__(name)
        except (TypeError, AttributeError):
            return False
        else:
            return True

    def __reduce__(self):
        return (AST, (list(self.items()),))

    def _safekey(self, key):
        while self.__hasattribute__(key):
            key += '_'
        return key

    def _define(self, keys, list_keys=None):
        for key in keys:
            key = self._safekey(key)
            if key not in self:
                super().__setitem__(key, None)

        for key in list_keys or []:
            key = self._safekey(key)
            if key not in self:
                super().__setitem__(key, [])

    def __json__(self):
        return {
            name: asjson(value)
            for name, value in self.items()
        }

    def __repr__(self):
        return repr(self.asjson())

    def __str__(self):
        return str(self.asjson())

    def __hash__(self):
        # NOTE: objects are actually mutable during creation
        return reduce(
            operator.xor,
            (hash((name, id(value))) for name, value in self.items()),
            0
        )

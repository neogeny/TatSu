# -*- coding: utf-8 -*-
"""
Define the AST class, a direct descendant of dict that's used during parsing
to store the values of named elements of grammar rules.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from tatsu.util import strtype, asjson, is_list, PY3, Mapping


class AST(dict):
    _closed = False

    def __init__(self, *args, **kwargs):
        super(AST, self).__init__()
        self._order = []

        self.update(*args, **kwargs)
        self._closed = True

    def set_parseinfo(self, value):
        self.set('parseinfo', value)

    def asjson(self):
        return asjson(self)

    def iterkeys(self):
        return iter(self)

    def keys(self):
        keys = self.iterkeys()
        return keys if PY3 else list(keys)

    def itervalues(self):
        return (self[k] for k in self)

    def values(self):
        values = self.itervalues()
        return values if PY3 else list(values)

    def iteritems(self):
        return ((k, self[k]) for k in self)

    def items(self):
        items = self.iteritems()
        return items if PY3 else list(items)

    def update(self, *args, **kwargs):
        def upairs(d):
            for k, v in d:
                self[k] = v

        for d in args:
            if isinstance(d, Mapping):
                upairs(d.items())
            else:
                upairs(d)
        upairs(kwargs.items())

    def set(self, key, value, force_list=False):
        key = self._safekey(key)

        previous = self.get(key)
        if previous is None:
            if force_list:
                super(AST, self).__setitem__(key, [value])
            else:
                super(AST, self).__setitem__(key, value)
            self._order.append(key)
        elif is_list(previous):
            previous.append(value)
        else:
            super(AST, self).__setitem__(key, [previous, value])
        return self

    def setlist(self, key, value):
        return self.set(key, value, force_list=True)

    def copy(self):
        return AST(
            (k, v[:] if is_list(v) else v)
            for k, v in self.items()
        )

    def __iter__(self):
        return iter(self._order)

    def __getitem__(self, key):
        if key in self:
            return super(AST, self).__getitem__(key)
        key = self._safekey(key)
        if key in self:
            return super(AST, self).__getitem__(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        key = self._safekey(key)
        super(AST, self).__delitem__(key)
        self._order.remove(key)

    def __setattr__(self, name, value):
        if self._closed and name not in vars(self):
            raise AttributeError(
                '%s attributes are fixed. Cannot set attribute %s.'
                %
                (self.__class__.__name__, name)
            )
        super(AST, self).__setattr__(name, value)

    def __getattr__(self, name):
        return self[name]

    def __hasattribute__(self, name):
        if not isinstance(name, strtype):
            return False
        try:
            super(AST, self).__getattribute__(name)
            return True
        except AttributeError:
            return False

    def __reduce__(self):
        return (AST, (), None, None, iter(self.items()))

    def _safekey(self, key):
        while self.__hasattribute__(key):
            key += '_'
        return key

    def _define(self, keys, list_keys=None):
        # WARNING: This is the *only* implementation that does what's intended
        for key in list_keys or []:
            key = self._safekey(key)
            if key not in self:
                self[key] = []

        for key in keys:
            key = self._safekey(key)
            if key not in self:
                super(AST, self).__setitem__(key, None)
                self._order.append(key)

    def __json__(self):
        return {
            asjson(k): asjson(v)
            for k, v in self.items() if not k.startswith('_')
        }

    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            super(AST, self).__repr__()
        )

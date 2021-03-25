from __future__ import annotations

from collections.abc import Mapping

from tatsu.util import asjson, is_list


class AST(Mapping):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.__dict__ = dict(*args, **kwargs)

    # def copy(self):
    #     return self.__copy__()

    def asjson(self):
        return asjson(self)

    def __copy__(self):
        return AST(self)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __reduce__(self):
        return (AST, (), None, None, iter(self.items()))

    def __json__(self):
        return asjson(self.__dict__)

    def __repr__(self):
        return repr(self.asjson())

    def __str__(self):
        return str(self.asjson())

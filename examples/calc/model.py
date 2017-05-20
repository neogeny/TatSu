# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics


class CalcModelBuilderSemantics(ModelBuilderSemantics):
    def __init__(self):
        types = [
            t for t in globals().values()
            if type(t) is type and issubclass(t, ModelBase)
        ]
        super(CalcModelBuilderSemantics, self).__init__(types=types)


class ModelBase(Node):
    pass


class Add(ModelBase):
    def __init__(self,
                    left=None,
                    op=None,
                    right=None,
                    **_kwargs_):
        super(Add, self).__init__(
            left=left,
            op=op,
            right=right,
            **_kwargs_
        )


class Subtract(ModelBase):
    def __init__(self,
                    left=None,
                    op=None,
                    right=None,
                    **_kwargs_):
        super(Subtract, self).__init__(
            left=left,
            op=op,
            right=right,
            **_kwargs_
        )


class Multiply(ModelBase):
    def __init__(self,
                    left=None,
                    op=None,
                    right=None,
                    **_kwargs_):
        super(Multiply, self).__init__(
            left=left,
            op=op,
            right=right,
            **_kwargs_
        )


class Divide(ModelBase):
    def __init__(self,
                    left=None,
                    right=None,
                    **_kwargs_):
        super(Divide, self).__init__(
            left=left,
            right=right,
            **_kwargs_
        )

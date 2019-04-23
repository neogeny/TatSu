# -*- coding: utf-8 -*-
from __future__ import generator_stop

import sys

from tatsu.codegen import ModelRenderer
from tatsu.codegen import CodeGenerator

THIS_MODULE = sys.modules[__name__]


class PostfixCodeGenerator(CodeGenerator):
    def __init__(self):
        super().__init__(modules=[THIS_MODULE])


class Number(ModelRenderer):
    template = '''\
    PUSH {value}'''


class Add(ModelRenderer):
    template = '''\
    {left}
    {right}
    ADD'''


class Subtract(ModelRenderer):
    template = '''\
    {left}
    {right}
    SUB'''


class Multiply(ModelRenderer):
    template = '''\
    {left}
    {right}
    MUL'''


class Divide(ModelRenderer):
    template = '''\
    {left}
    {right}
    DIV'''

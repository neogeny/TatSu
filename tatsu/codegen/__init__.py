# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from tatsu.exceptions import CodegenError
from tatsu.codegen.cgbase import (  # noqa
    DelegatingRenderingFormatter,
    ModelRenderer,
    NullModelRenderer,
    CodeGenerator,
)


def codegen(model, target='python'):
    if target.lower() == 'python':
        from tatsu.codegen import python
        return python.codegen(model)
    else:
        raise CodegenError('Unknown target language: %s' % target)

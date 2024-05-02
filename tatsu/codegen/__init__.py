from __future__ import annotations

from ..exceptions import CodegenError
from .cgbase import (  # noqa: F401
    CodeGenerator,
    DelegatingRenderingFormatter,
    ModelRenderer,
    NullModelRenderer,
)


def codegen(model, target='python'):
    if target.lower() == 'python':
        from tatsu.codegen import python

        return python.codegen(model)
    else:
        raise CodegenError(f'Unknown target language: {target}')

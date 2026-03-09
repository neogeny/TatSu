# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
from importlib import resources

from ._config import __toolname__, __version__
from ._version import version, version_info
from .contexts import AST, ast
from .contexts.decorator import name, nomemo, tatsumasu
from .grammars import builder
from .objectmodel import (
    NodeDataclassParams,
    NodeDataclassParams as TatSuDataclassParams,
    nodedataclass,
    nodedataclass as dataclass,
    nodedataclass as tatsudataclass,
)
from .tokenizing import buffer
from .tool import (  # pylint: disable=W0622
    compile,
    gencode,
    genmodel,
    parse,
    tatsu_main,
    tatsu_main as main,
    to_python_model,
    to_python_sourcecode,
)

# HACK!
# NOTE: this is for backwrds compatibility with legacy generated parsers
sys.modules.update(  # noqa: RUF067
    {
        'tatsu.ast': ast,
        'tatsu.builder': builder,
        'tatsu.buffering': buffer,
    }
)


grammar_path = resources.files().joinpath("_tatsu.tatsu")  # noqa: RUF067
grammar = grammar_path.read_text()  # noqa: RUF067

__all__ = [
    '__toolname__',
    '__version__',
    'AST',
    'builder',
    'compile',
    'gencode',
    'genmodel',
    'main',  # some unit tests want this
    'parse',
    'tatsu_main',
    'to_python_model',
    'to_python_sourcecode',
    'version',
    'version_info',
    'NodeDataclassParams',
    'TatSuDataclassParams',
    'dataclass',
    'nodedataclass',
    'tatsudataclass',
    'name',
    'nomemo',
    'tatsumasu',
    'grammar_path',
    'grammar',
]

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
from importlib import resources

from ._config import __toolname__, __version__
from ._grammar import grammar, grammar_path
from ._version import version, version_info
from .contexts import ast as ast
from .contexts.decorator import isname, leftrec, name, nomemo, rule, tatsumasu
from .grammars import builder as builder
from .objectmodel import (
    NodeDataclassParams,
    NodeDataclassParams as TatSuDataclassParams,
    nodedataclass,
    nodedataclass as dataclass,
    nodedataclass as tatsudataclass,
)
from .tokenizing import buffer as buffering
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
        'tatsu.buffering': buffering,
    }
)


__all__ = [
    '__toolname__',
    '__version__',
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
    'isname',
    'NodeDataclassParams',
    'TatSuDataclassParams',
    'dataclass',
    'nodedataclass',
    'tatsudataclass',
    'name',
    'leftrec',
    'nomemo',
    'rule',
    'tatsumasu',
    'grammar_path',
    'grammar',
]

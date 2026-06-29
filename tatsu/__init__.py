# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys

from . import config as parserconfig, input as tokenizing
from ._grammar import grammar, grammar_path
from ._version import __toolname__, __version__, version, version_info
from .api import (
    compile,
    compile_to_parser,
    gencode,
    genmodel,
    parse,
    to_grammar_json,
    to_python_model,
    to_python_sourcecode,
)  # pylint: disable=W0622
from .contexts import ast as ast
from .contexts.decorator import isname, leftrec, name, nomemo, rule, tatsumasu
from .input import buffer as buffer, buffer as buffering, textlines as textlines
from .objectmodel import (
    NodeDataclassParams,
    NodeDataclassParams as TatSuDataclassParams,
    builder as builder,
    nodedataclass,
    nodedataclass as dataclass,
    nodedataclass as tatsudataclass,
)
from .tool.cli import tatsu_main


# HACK!
# NOTE: this is for backwrds compatibility with legacy generated parsers
sys.modules.update(  # noqa: RUF067
    {
        'tatsu.ast': ast,
        'tatsu.builder': builder,
        'tatsu.buffering': buffering,
        'tatsu.parserconfig': parserconfig,
        'tatsu.tokenizing': tokenizing,
        'tatsu.tokenizing.buffer': buffer,
        'tatsu.tokenizing.textlines': textlines,
    }
)


__all__ = [
    '__toolname__',
    '__version__',
    'compile_to_parser',
    'builder',
    'compile',
    'gencode',
    'genmodel',
    'parse',
    'tatsu_main',
    'to_grammar_json',
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

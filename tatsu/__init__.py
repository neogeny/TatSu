# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from ._config import __toolname__, __version__
from ._version import version, version_info
from .tool import (  # pylint: disable=W0622
    compile,
    gencode,
    genmodel,
    parse,
    tatsu_main,
    to_python_model,
    to_python_sourcecode,
)
from .tool import tatsu_main as main
from .contexts.decorator import isname, name, leftrec, nomemo, rule, tatsumasu
from .objectmodel import TatSuDataclassParams, tatsudataclass as dataclass
from importlib import resources

grammar_path = resources.files().joinpath("_tatsu.tatsu")  # noqa: RUF067
grammar = grammar_path.read_text()  # noqa: RUF067

__all__ = [
    '__toolname__',
    '__version__',
    "compile",
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
    'TatSuDataclassParams',
    'dataclass',
    'name',
    'leftrec',
    'nomemo',
    'rule',
    'tatsumasu',
    'grammar_path',
    'grammar',
]

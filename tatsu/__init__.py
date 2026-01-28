from __future__ import annotations

from ._config import __toolname__, __version__
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
]

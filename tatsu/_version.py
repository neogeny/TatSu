# Copyright © 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause

from __future__ import annotations

import importlib.metadata

from .util import Version


__toolname__ = 'TatSu'
__version__ = 'v5.22.1-beta.1'
try:
    __toolname__ = importlib.metadata.metadata("TatSu")["name"]
    __version__ = importlib.metadata.version("TatSu")
except importlib.metadata.PackageNotFoundError:
    pass

version = __version__
version_info = Version.parse(version).astuple()

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause

from __future__ import annotations

from .util import Version


__toolname__ = 'TatSu'
__version__ = '5.19.0rc1'
version = __version__
version_info = Version.parse(version).astuple()

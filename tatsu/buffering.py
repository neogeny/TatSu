#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import warnings

# NOTE: re-exports for bw compatibility
from .tokenizing import buffer
from .tokenizing.buffer import *  # noqa: F403
from .util import fqn

warnings.warn(
    f'Module {__name__!r} is deprecated. Use module {fqn(buffer)!r} instead.',
    DeprecationWarning,
    stacklevel=2,
)

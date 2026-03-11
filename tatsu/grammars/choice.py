# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import field
from typing import Any

from ..contexts import Ctx
from ..objectmodel import nodedataclass
from ..util import cast, indent
from ._core import PEP8_LLEN, Box, Model
from .math import ffset

from __future__ import annotations

from typing import Any

from ..contexts import Ctx
from .closure import PositiveJoin


class LeftJoin(PositiveJoin):
    JOINOP = '<'

    def _parse(self, ctx: Ctx) -> Any:
        return ctx.left_join(self.exp._parse, self.sep._parse)


class RightJoin(PositiveJoin):
    JOINOP = '>'

    def _parse(self, ctx: Ctx) -> Any:
        return ctx.right_join(self.exp._parse, self.sep._parse)

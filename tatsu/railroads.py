# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from tatsu import grammars
from tatsu.walkers import NodeWalker


def draw(model: grammars.Grammar):
    pass


class RailroadNodeWalker(NodeWalker):
    def __init__(self):
        super().__init__()

    def walk_decorator(self, d):
        ...

    def walk_default(self, node):
        ...

    def walk_grammar(self, g):
        ...

    def walk_rule(self, r):
        ...

    def walk_optional(self, o):
        ...

    def walk_closure(self, r):
        ...

    def walk_choice(self, c):
        ...

    def walk_sequence(self, s):
        ...

    def walk_call(self, rr):
        ...

    def walk_pattern(self, p):
        ...

    def walk_token(self, t):
        token = t
        width = 8
        print(f'-|{token:^{width}}|-')
        ...

    def walk_eof(self, v):
        ...

    def walk_lookahead(self, v):
        ...

    def walk_negative_lookahead(self, v):
        ...

    def walk_void(self, v):
        ...

    def walk_fail(self, v):
        ...

    def walk_endrule(self, ast):
        ...

    def walk_emptyline(self, ast, *args):
        ...

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import importlib
import itertools
from pathlib import Path

from .util import misc
from .walkers import NodeWalker

__all__ = ['draw']

# SHAPE           DESCRIPTION
# box             Standard rectangle
# circle          Basic circle
# ellipse         Default shape; an oval
# point           Microscopic filled circle (junctions)
# egg             Asymmetric oval
# triangle        Upward pointing triangle
# plaintext       Text with no border
# diamond         Rhombus (decision points)
# trapezium       Trapezoid
# parallelogram   Slanted rectangle (I/O or rules)
# house           Polygon shaped like a house
# pentagon        Five-sided polygon
# hexagon         Six-sided polygon
# septagon        Seven-sided polygon
# octagon         Eight-sided polygon
# doublecircle    Circle with an inner ring
# doubleoctagon   Octagon with an inner border
# tripleoctagon   Octagon with two inner borders
# invtriangle     Upside-down triangle
# invtrapezium    Upside-down trapezoid
# invhouse        Upside-down house shape
# rect            Alias for box
# rectangle       Alias for box
# square          Box with equal sides
# star            Multi-pointed star
# cylinder        3D-style tube (databases)
# note            Paper with a folded corner
# tab             Folder-style tab
# folder          Classic file folder shape
# box3d           Rectangle with 3D depth
# component       Box with "plug protrusions"
# larrow          Arrow pointing left
# rarrow          Arrow pointing right
# record          Box for structured data fields
# Mrecord         Record with rounded corners
# none            No shape and no label space


def available() -> bool:
    return misc.module_available('graphviz') and misc.platform_has_command('dot')


def draw(filename, grammar):
    traverser = DiagramNodeWalker()
    traverser.walk(grammar)
    traverser.render(filename)


class DiagramNodeWalker(NodeWalker):
    def __init__(self):
        super().__init__()

        # splines=
        # true     ?
        # line     Strictly straight lines between nodes.
        # polyline Straight segments that can change direction at internal points.
        # ortho    All lines are strictly horizontal or vertical (manhattan routing).
        # curved   Smooth Bezier curves (default behavior for splines=true).
        self.graphviz = importlib.import_module('graphviz')

        self.top_graph = self.graphviz.Digraph(
            engine='dot',
            graph_attr={
                'rankdir': 'LR',
                'packMode': 'clust',
                'splines': 'true',
            },
        )
        self.stack = [self.top_graph]
        self.node_count = 0

    @property
    def graph(self):
        return self.stack[-1]

    def render(self, filename):
        filepath = Path(filename)
        fmt = filepath.suffix.lstrip('.') or 'dot'
        fmt = 'jpeg' if fmt == 'jpg' else fmt
        self.graph.render(
            # filename=filename,
            outfile=filename,
            format=fmt,
            cleanup=True,
        )

    def push_graph(self, name=None, **attr):
        if name is None:
            self.node_count += 1
            name = f'cluster_g{self.node_count}'
        elif not name.startswith('cluster'):
            # graphviz needs "cluster" prefix to draw a bounding box
            name = f'cluster_{name}'

        # In graphviz, subgraphs are created as new objects
        attr['style'] = 'invis'
        new_subgraph = self.graphviz.Digraph(name=name, graph_attr=attr)
        self.stack.append(new_subgraph)
        return new_subgraph

    def pop_graph(self):
        last_graph = self.stack.pop()
        # In graphviz, you must explicitly add the child back to the parent
        self.graph.subgraph(last_graph)

    def node(self, label, id=None, **attr):
        if id is None:
            self.node_count += 1
            id = f'n{self.node_count}'

        # graphviz .node() takes the ID and then attributes
        self.graph.node(id, label=label, **attr)
        return id  # We return the ID string to be used for edges

    def tnode(self, name, **attr):
        return self.node(name, shape='hexagon', **attr)

    def dot(self):
        return self.node('', shape='point', width='0.01')

    def start_node(self):
        return self.dot()

    def ref_node(self, name):
        return self.node(name, shape='box', style='rounded')

    def rule_node(self, name, **attr):
        # Using the name as the ID for rules as per original logic
        return self.node(
            name, id=name, shape='box', style='bold', **attr,
        )

    def end_node(self):
        return self.node('', shape='point', width='0.1')

    def edge(self, s, e, **attr):
        # style       Changes the line pattern solid, dashed, dotted, bold, tapered
        # color       Changes the line color red, blue, #FFA500, transparent
        # arrowhead   Changes the shape of the tip normal, dot, none, vee, diamond
        # penwidth    Changes line thickness Numeric value (e.g., 2.0, 0.5)
        # label       Adds text to the edge Any string
        if not (s and e):
            return
        self.graph.edge(s, e, **attr)

    def redge(self, s, e):
        return self.edge(s, e, dir='back')

    def zedge(self, s, e):
        # 'len' is for neato, but kept for parity
        return self.edge(s, e, len='0.000001')

    def nedge(self, s, e):
        return self.edge(s, e, style='invisible', dir='none')

    # --- Walker Logic (Mostly identical, utilizing new wrapper methods) ---

    def walk_decorator(self, d):
        return self.walk(d.exp)

    def walk_default(self, node):
        pass

    def walk_grammar(self, g):
        # Creating clusters for organization
        self.push_graph(name=f"{g.name}_0")
        try:
            vrules = [self.walk(r) for r in reversed(g.rules)]
        finally:
            self.pop_graph()

        if not vrules:
            return None, None

        s, t = vrules[0][0], vrules[-1][1]
        return s, t

    def walk_rule(self, r):
        self.push_graph(name=r.name)
        try:
            i, e = self.walk(r.exp)
            s = self.rule_node(r.name)
            self.edge(s, i)
            t = self.end_node()
            self.edge(e, t)
            return s, t
        finally:
            self.pop_graph()

    def walk_optional(self, o):
        i, e = self.walk_decorator(o)
        ni = self.dot()
        ne = self.dot()
        self.zedge(ni, i)
        self.edge(ni, ne)
        self.zedge(e, ne)
        return ni, ne

    def walk_closure(self, r):
        self.push_graph(rankdir='TB')
        try:
            i, e = self.walk_decorator(r)
            ni = self.dot()
            self.zedge(ni, i)
            self.zedge(e, ni)
            return ni, ni
        finally:
            self.pop_graph()

    def walk_choice(self, c):
        vopt = [self.walk(o) for o in c.options]
        vopt = [o for o in vopt if o is not None]
        ni = self.dot()
        ne = self.dot()
        for i, e in vopt:
            self.edge(ni, i)
            self.edge(e, ne)
        return ni, ne

    def walk_sequence(self, s):
        vseq = [self.walk(x) for x in s.sequence if x is not None]
        vseq = [x for x in vseq if x is not None]

        if not vseq:
            return None, None

        first, _ = vseq[0]
        _, last = vseq[-1]

        for (_, e), (i, _) in itertools.pairwise(vseq):
            self.edge(e, i)

        return first, last

    # Simplified remaining walkers for brevity
    def walk_call(self, rr):
        n = self.ref_node(rr.name)
        return n, n

    def walk_pattern(self, p):
        n = self.tnode(p.pattern)
        return n, n

    def walk_token(self, t):
        n = self.tnode(t.token)
        return n, n

    def walk_eof(self, v):
        n = self.node('$EOF')
        return n, n

    def walk_lookahead(self, v):
        i, e = self.walk(v.exp)
        s = self.node('&', shape='diamond')
        self.zedge(s, i)
        return s, e

    def walk_negative_lookahead(self, v):
        try:
            i, e = self.walk(v.exp)
        except TypeError as e:
            raise TypeError(f'{e} {v.exp}') from e
        s = self.node('&', shape='diamond')
        s = self.node('!', shape='diamond')
        self.zedge(s, i)
        return s, e

    def walk_void(self, v):
        return None, None

    def walk_fail(self, v):
        return None, None

    def ENDRULE(self, ast):
        return None, None

    def EMPTYLINE(self, ast, *args):
        return None, None

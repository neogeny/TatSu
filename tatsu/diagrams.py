from __future__ import annotations

import itertools

import pygraphviz as pgv  # pylint: disable=E0401

from .walkers import NodeWalker

__all__ = ['draw']


def draw(filename, grammar):
    traverser = GraphvizWalker()
    traverser.walk(grammar)
    traverser.draw(filename)


class GraphvizWalker(NodeWalker):
    def __init__(self):
        super().__init__()
        self.top_graph = pgv.AGraph(
            directed=True, rankdir='LR', packMode='clust', splines='true',
        )
        self.stack = [self.top_graph]
        self.node_count = 0

    @property
    def graph(self):
        return self.stack[-1]

    def draw(self, filename):
        self.graph.layout(prog='dot')
        # WARNING: neato generated graphics hang my GPU
        # self.graph.layout(prog='neato')
        self.graph.draw(filename)

    def push_graph(self, name=None, **attr):
        if name is None:
            self.node_count += 1
            name = 'g%d' % self.node_count
        self.stack.append(self.graph.add_subgraph(name, **attr))
        return self.graph

    def pop_graph(self):
        self.stack.pop()

    def node(self, name, id=None, **attr):
        if id is None:
            self.node_count += 1
            id = 'n%d' % self.node_count
        else:
            try:
                return self.graph.get_node(id)
            except KeyError:
                pass
        self.graph.add_node(id, **attr)
        n = self.graph.get_node(id)
        n.attr['label'] = name
        #        n.attr['shape'] = 'circle'
        return n

    def tnode(self, name, **attr):
        return self.node(name, **attr)

    def dot(self):
        n = self.node('')
        n.attr['shape'] = 'point'
        n.attr['size'] = 0.0000000001
        n.attr['label'] = ''
        return n

    def start_node(self):
        return self.dot()

    def ref_node(self, name):
        n = self.node(name)
        n.attr['shape'] = 'box'
        return n

    def rule_node(self, name, **attr):
        n = self.node(name, **attr)
        n.attr['shape'] = 'parallelogram'
        return n

    def end_node(self):
        n = self.node('')
        n.attr['shape'] = 'point'
        n.attr['width'] = 0.1
        return n

    def edge(self, s, e, **attr):
        self.graph.add_edge(s, e, **attr)
        edge = self.graph.get_edge(s, e)
        # edge.attr['arrowhead'] = 'normal'
        edge.attr['arrowhead'] = 'none'
        return edge

    def redge(self, s, e):
        edge = self.edge(s, e)
        edge.attr['dir'] = 'back'
        return edge

    def zedge(self, s, e):
        return self.edge(s, e, len=0.000001)

    def nedge(self, s, e):
        return self.edge(s, e, style='invisible', dir='none')

    def path(self, p):
        self.graph.add_path(p)

    def subgraph(self, name, bunch):
        self.top_graph.add_subgraph(name)

    def concat(self, *args):
        return list(itertools.chain(*args))

    def _walk_decorator(self, d):
        return self.walk(d.exp)

    def walk_default(self, node):
        raise NotImplementedError('No walking for ', type(node).__name__)

    def walk__decorator(self, d):
        return self.walk(d.exp)

    def walk__grammar(self, g):
        self.push_graph(g.name + '0')
        try:
            vrules = [self.walk(r) for r in reversed(g.rules)]
        finally:
            self.pop_graph()
        self.push_graph(g.name + '1')
        try:
            pass
            # link all rule starting nodes with invisible edges
            # starts = [self.node(r.name, id=r.name) for r in g.rules]
            # for n1, n2 in zip(starts, starts[1:]):
            #     self.nedge(n1, n2)
        finally:
            self.pop_graph()
        s, t = vrules[0][0], vrules[-1][1]
        return (s, t)

    def walk__rule(self, r):
        self.push_graph(r.name)
        try:
            i, e = self.walk(r.exp)
            s = self.rule_node(r.name, id=r.name)
            self.edge(s, i)
            t = self.end_node()
            self.edge(e, t)
            return (s, t)
        finally:
            self.pop_graph()

    def walk__based_rule(self, r):
        return self.walk__rule(r)

    def walk__rule_ref(self, rr):
        n = self.ref_node(rr.name)
        return (n, n)

    def walk__special(self, s):
        n = self.node(s.special)
        return (n, n)

    def walk__override(self, o):
        return self._walk_decorator(o)

    def walk__named(self, n):
        return self._walk_decorator(n)

    def walk__named_list(self, n):
        return self._walk_decorator(n)

    def walk__cut(self, c):
        # c = self.node('>>')
        # return (c, c)
        return None

    def walk__optional(self, o):
        i, e = self._walk_decorator(o)
        ni = self.dot()
        ne = self.dot()
        self.zedge(ni, i)
        self.edge(ni, ne)
        self.zedge(e, ne)
        return (ni, ne)

    def walk__closure(self, r):
        self.push_graph(rankdir='TB')
        try:
            i, e = self._walk_decorator(r)
            ni = self.dot()
            self.edge(ni, i)
            self.edge(e, ni)
            return (ni, ni)
        finally:
            self.pop_graph()

    def walk__positive_closure(self, r):
        i, e = self._walk_decorator(r)
        if i == e:
            self.redge(e, i)
        else:
            self.edge(e, i)
        return (i, e)

    def walk__join(self, r):
        i, e = self._walk_decorator(r)
        n = self.tnode(r.sep)
        self.edge(i, n)
        self.edge(n, e)
        return (i, e)

    def walk__group(self, g):
        return self._walk_decorator(g)

    def walk__choice(self, c):
        vopt = [self.walk(o) for o in c.options]
        vopt = [o for o in vopt if o is not None]
        ni = self.dot()
        ne = self.dot()
        for i, e in vopt:
            self.edge(ni, i)
            self.edge(e, ne)
        return (ni, ne)

    def walk__sequence(self, s):
        vseq = [self.walk(x) for x in s.sequence]
        vseq = [x for x in vseq if x is not None]
        i, _ = vseq[0]
        _, e = vseq[-1]
        if i != e:
            bunch = zip(
                [a for _x, a in vseq[:-1]],
                [b for b, _y in vseq[1:]],
                strict=False,
            )
            for n, n1 in bunch:
                self.edge(n, n1)
        return (i, e)

    def walk__lookahead(self, la):
        _, e = self._walk_decorator(la)
        n = self.node('&')
        self.edge(n, e)
        return (n, e)

    def walk__negative_lookahead(self, la):
        _, e = self._walk_decorator(la)
        n = self.node('!')
        self.edge(n, e)
        return (n, e)

    def walk__rule_include(self, la):
        _, e = self._walk_decorator(la)
        n = self.node('>')
        self.edge(n, e)
        return (n, e)

    def walk__pattern(self, p):
        n = self.tnode(p.pattern)
        return (n, n)

    def walk__token(self, t):
        n = self.tnode(t.token)
        return (n, n)

    def walk__void(self, v):
        n = self.dot()
        return (n, n)

    def walk__constant(self, t):
        n = self.tnode(f'`{t.ast}`')
        return (n, n)

    def walk__eof(self, v):
        # n = self.node('$')
        # return (n, n)
        return None

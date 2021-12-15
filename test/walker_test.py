from __future__ import generator_stop

import json
from collections import defaultdict

import tatsu
from tatsu.walkers import DepthFirstWalker
from tatsu.util import asjson


def test_walk_node_ast():
    GRAMMAR = r'''
        @@grammar::TLA

        #
        # comment
        #
        start = expression $;

        expression = temporal_expression | nontemporal_top_expression ;
        nontemporal_top_expression(SampleExpression) =  expr:nontemporal_expression ;
        temporal_expression =    temporal_atom;
        temporal_atom(TemporalSeq) = ['Seq'] '(' @:temporal_arg_list ')';
        temporal_arg_list = "," .{@+:expression}+;
        nontemporal_expression =  number ;

        # tokens
        number::int = /\d+/;
    '''

    parser = tatsu.compile(GRAMMAR, asmodel=True)
    model = parser.parse('Seq(1,1)')
    assert model.ast is not None

    seen = defaultdict(int)

    class PW(DepthFirstWalker):
        def walk_Node(self, node, *args, **kwargs):
            t = type(node).__name__
            print(f'node {t}')
            seen[t] += 1

    print(json.dumps(asjson(model), indent=2))
    PW().walk(model)
    assert seen == {'SampleExpression': 2, 'TemporalSeq': 1}

import json
from collections import defaultdict

import tatsu
from tatsu.util import asjson
from tatsu.walkers import DepthFirstWalker, NodeWalker


def test_walk_node_ast():
    GRAMMAR = r"""
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
    """

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


def test_cache_per_class():
    class PW(DepthFirstWalker):
        pass

    assert isinstance(
        NodeWalker._walker_cache, dict,
    )
    assert isinstance(
        DepthFirstWalker._walker_cache, dict,
    )
    assert isinstance(PW._walker_cache, dict)

    assert id(NodeWalker._walker_cache) != id(
        DepthFirstWalker._walker_cache,
    )
    assert id(PW._walker_cache) != id(
        DepthFirstWalker._walker_cache,
    )

    walker = PW()
    assert id(walker._walker_cache) == id(
        PW._walker_cache,
    )

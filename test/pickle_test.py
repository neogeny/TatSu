import pickle

from tatsu.semantics import ModelBuilderSemantics
from tatsu.tool import compile
from tatsu.util import asjson


def test_synth_model():
    grammar = '''
        start::ASeq
            =
            aseq
            $
            ;

        aseq
            =
            {'a'}+
            ;
    '''

    m = compile(grammar, 'ASeq')
    model = m.parse('a a a', semantics=ModelBuilderSemantics())
    assert 'ASeq' == type(model).__name__

    p = pickle.dumps(model)
    new_model = pickle.loads(p)
    assert 'ASeq' == type(new_model).__name__

    assert model.ast == new_model.ast


def test_nested_class_synth_model():
    grammar = '''
        start::ASeq
            =
            seqs:aseq
            $
            ;

        aseq::Seq
            =
            values:{'a'}+
            ;
    '''

    m = compile(grammar, 'ASeq')
    model = m.parse('a a a', semantics=ModelBuilderSemantics())
    assert 'ASeq' == type(model).__name__

    p = pickle.dumps(model)
    new_model = pickle.loads(p)
    assert 'ASeq' == type(new_model).__name__

    # NOTE: Since we are unpickling an object which contains nested objects, we can't do
    # self.assertEqual(model.ast, new_model.ast) as the memory locations will be different.
    # So either (1) we recursively walk the objects and compare fields or (2) we convert it into a
    # str()/repr()/JSON and compare that. The latter as it is easier.
    assert asjson(model.ast) == asjson(new_model.ast)

from __future__ import annotations

import difflib
import importlib
import json
import pickle
import pprint
import py_compile
import shutil
import sys
from pathlib import Path

import pytest

from tatsu import diagrams
from tatsu.ngcodegen import codegen
from tatsu.parser import EBNFParser, GrammarGenerator
from tatsu.parser_semantics import EBNFGrammarSemantics
from tatsu.semantics import ASTSemantics
from tatsu.tool import to_python_sourcecode
from tatsu.util import asjson
from tatsu.walkers import DepthFirstWalker

tmp = Path('./tmp').resolve()
sys.path.insert(0, str(tmp))


@pytest.mark.dependency()
def test_00_with_boostrap_grammar():
    print('-' * 20, 'phase 00 - parse using the bootstrap grammar')

    tmp = Path('./tmp')
    if (tmp / '00.ast').is_file():
        shutil.rmtree('./tmp')
    tmp.mkdir(exist_ok=True)
    text = Path('grammar/tatsu.ebnf').read_text()
    g = EBNFParser('EBNFBootstrap')
    grammar0 = g.parse(text, semantics=ASTSemantics(), parseinfo=False)
    ast0 = json.dumps(asjson(grammar0), indent=2)
    Path('./tmp/00.ast').write_text(ast0)


@pytest.mark.dependency('test_00_with_boostrap_grammar')
def test_01_with_parser_generator():
    print('-' * 20, 'phase 01 - parse with parser generator')
    text = Path('grammar/tatsu.ebnf').read_text()
    g = GrammarGenerator('EBNFBootstrap')
    result = g.parse(text)
    generated_grammar1 = str(result)
    Path('./tmp/01.ebnf').write_text(generated_grammar1)


@pytest.mark.dependency('test_01_with_parser_generator')
def test_02_previous_output_generator():
    print(
        '-' * 20,
        'phase 02 - parse previous output with the parser generator',
    )
    text = Path('grammar/tatsu.ebnf').read_text()
    g = GrammarGenerator('EBNFBootstrap')
    result = g.parse(text)
    generated_grammar1 = str(result)

    text = Path('./tmp/01.ebnf').read_text()
    g = GrammarGenerator('EBNFBootstrap')
    result = g.parse(text)
    generated_grammar2 = str(result)
    Path('./tmp/02.ebnf').write_text(generated_grammar2)
    assert generated_grammar2 == generated_grammar1


@pytest.mark.dependency('test_02_previous_output_generator')
def test_03_repeat_02():
    print('-' * 20, 'phase 03 - repeat')
    text = Path('./tmp/02.ebnf').read_text()
    g = EBNFParser('EBNFBootstrap')
    ast3 = g.parse(text)
    Path('./tmp/03.ast').write_text(json.dumps(asjson(ast3), indent=2))


@pytest.mark.dependency('test_03_repeat_02')
def test_04_repeat_03():
    print('-' * 20, 'phase 04 - repeat')
    text = Path('./tmp/01.ebnf').read_text()
    g = GrammarGenerator('EBNFBootstrap')
    result = g.parse(text)
    generated_grammar2 = str(result)

    text = Path('./tmp/02.ebnf').read_text()
    g = GrammarGenerator('EBNFBootstrap')
    parser = g.parse(text)
    generated_grammar4 = str(parser)
    Path('./tmp/04.ebnf').write_text(generated_grammar4)
    assert generated_grammar4 == generated_grammar2


@pytest.mark.dependency('test_04_repeat_03')
def test_05_parse_with_model():
    print('-' * 20, 'phase 05 - parse using the grammar model')
    text = Path('./tmp/02.ebnf').read_text()
    g = GrammarGenerator('EBNFBootstrap')
    parser = g.parse(text)

    text = Path('./tmp/04.ebnf').read_text()
    ast5 = parser.parse(text)
    Path('./tmp/05.ast').write_text(json.dumps(asjson(ast5), indent=2))


@pytest.mark.dependency('test_05_parse_with_model')
def test_06_generate_code():
    print('-' * 20, 'phase 06 - generate parser code')
    text = Path('./tmp/02.ebnf').read_text()
    g = GrammarGenerator('EBNFBootstrap')
    parser = g.parse(text)
    gencode6 = codegen(parser)
    Path('./tmp/g06.py').write_text(gencode6)


@pytest.mark.dependency('test_06_generate_code')
def test_07_import_generated_code():
    print('-' * 20, 'phase 07 - import generated code')

    text = Path('grammar/tatsu.ebnf').read_text()
    gencode7 = to_python_sourcecode(text)
    Path('./tmp/g07.py').write_text(gencode7)
    assert Path('./tmp/g07.py').is_file()

    compiled_path = py_compile.compile('./tmp/g07.py', doraise=True)
    if compiled_path is None:
        pytest.fail('Could not compile module')
    assert compiled_path is not None
    compiled_path = Path(compiled_path)
    print('COMPILED', compiled_path)

    tmpdir = Path('./tmp')
    tmpdir.mkdir(parents=True, exist_ok=True)
    assert tmpdir.is_dir()
    Path('./tmp/__init__.py').touch()
    Path('./tmp/__init__.pyc').touch()
    print('CURRENT', Path.cwd())
    importlib.invalidate_caches()
    g07 = importlib.import_module('g07', package='tmp')

    # g07 = __import__('g07')
    assert g07
    generated_parser = g07.TatSuParser
    assert generated_parser


@pytest.mark.dependency('test_07_import_generated_code')
def test_08_compile_with_generated():
    print('-' * 20, 'phase 08 - compile using generated code')
    Path('./tmp').mkdir(parents=True, exist_ok=True)
    Path('./tmp/__init__.py').touch()
    importlib.invalidate_caches()
    g07 = importlib.import_module('g07', package='tmp')
    generated_parser = g07.TatSuParser
    assert generated_parser

    ast0 = Path('./tmp/00.ast').read_text()

    parser = generated_parser(trace=False)
    text = Path('grammar/tatsu.ebnf').read_text()
    result = parser.parse(text, semantics=ASTSemantics(), parseinfo=False)
    ast8 = json.dumps(asjson(result), indent=2)
    Path('./tmp/08.ast').write_text(ast8)
    print('DIFF')
    pprint.pprint(
        list(
            difflib.unified_diff(ast0.splitlines(), ast8.splitlines()),
        ),
    )
    assert ast0 == ast8


@pytest.mark.dependency('test_08_compile_with_generated')
def test_09_parser_with_semantics():
    print('-' * 20, 'phase 09 - Generate parser with semantics')
    text = Path('grammar/tatsu.ebnf').read_text()
    parser = GrammarGenerator('EBNFBootstrap')
    g9 = parser.parse(text)
    generated_grammar9 = str(g9)
    Path('./tmp/09.ebnf').write_text(generated_grammar9)
    text = Path('grammar/tatsu.ebnf').read_text()
    g = GrammarGenerator('EBNFBootstrap')
    result = g.parse(text)
    generated_grammar1 = str(result)
    assert generated_grammar9 == generated_grammar1


@pytest.mark.dependency('test_09_parser_with_semantics')
def test_10_with_model_and_semantics():
    print('-' * 20, 'phase 10 - Parse with a model using a semantics')
    text = Path('grammar/tatsu.ebnf').read_text()
    parser = GrammarGenerator('EBNFBootstrap')
    g9 = parser.parse(text)
    g10 = g9.parse(
        text,
        start_rule='start',
        semantics=EBNFGrammarSemantics('EBNFBootstrap'),
    )
    generated_grammar10 = str(g10)
    Path('./tmp/10.ebnf').write_text(generated_grammar10)
    gencode10 = codegen(g10)
    Path('./tmp/g10.py').write_text(gencode10)


@pytest.mark.dependency('test_10_with_model_and_semantics')
def test_11_with_pickle_and_retry():
    print('-' * 20, 'phase 11 - Pickle the model and try again.')
    text = Path('grammar/tatsu.ebnf').read_text()
    parser = GrammarGenerator('EBNFBootstrap')
    g9 = parser.parse(text)
    g10 = g9.parse(
        text,
        start_rule='start',
        semantics=EBNFGrammarSemantics('EBNFBootstrap'),
    )
    with Path('./tmp/11.tatsu').open('wb') as f:
        pickle.dump(g10, f)
    with Path('./tmp/11.tatsu').open('rb') as f:
        g11 = pickle.load(f)
    r11 = g11.parse(
        text,
        start_rule='start',
        semantics=EBNFGrammarSemantics('EBNFBootstrap'),
    )
    Path('./tmp/11.ebnf').write_text(str(g11))
    gencode11 = codegen(r11)
    Path('./tmp/bootstrap_g11.py').write_text(gencode11)


@pytest.mark.dependency('test_11_with_pickle_and_retry')
def test_12_walker():
    print('-' * 20, 'phase 12 - Walker')

    class PrintNameWalker(DepthFirstWalker):
        def __init__(self):
            super().__init__()
            self.walked = []

        def walk_default(self, o):
            self.walked.append(o.__class__.__name__)

    with Path('./tmp/11.tatsu').open('rb') as f:
        g11 = pickle.load(f)
    v = PrintNameWalker()
    v.walk(g11)
    Path('./tmp/12.txt').write_text('\n'.join(v.walked))


@pytest.mark.dependency('test_12_walker')
@pytest.mark.skipif(not diagrams.available(), reason='graphviz is not available')
def test_13_graphics():
    print('-' * 20, 'phase 13 - Graphics')
    with Path('./tmp/11.tatsu').open('rb') as f:
        g11 = pickle.load(f)
    diagrams.draw('./tmp/13.png', g11)

from __future__ import annotations

import json
import pickle
import py_compile
import shutil
import sys
import unittest
from pathlib import Path

from tatsu import util
from tatsu.codegen import codegen
from tatsu.parser import EBNFParser, GrammarGenerator
from tatsu.parser_semantics import EBNFGrammarSemantics
from tatsu.util import asjson
from tatsu.walkers import DepthFirstWalker

tmp = Path('./tmp').resolve()
sys.path.insert(0, str(tmp))


class BootstrapTests(unittest.TestCase):

    def test_bootstrap(self):
        print()

        tmp = Path('./tmp')
        if (tmp / '00.ast').is_file():
            shutil.rmtree('./tmp')
        tmp.mkdir(exist_ok=True)
        print('-' * 20, 'phase 00 - parse using the bootstrap grammar')
        with Path('grammar/tatsu.ebnf').open() as f:
            text = str(f.read())
        g = EBNFParser('EBNFBootstrap')
        grammar0 = g.parse(text, parseinfo=False)
        ast0 = json.dumps(asjson(grammar0), indent=2)
        with open('./tmp/00.ast', 'w') as f:
            f.write(ast0)

        print('-' * 20, 'phase 01 - parse with parser generator')
        with Path('grammar/tatsu.ebnf').open() as f:
            text = str(f.read())
        g = GrammarGenerator('EBNFBootstrap')
        result = g.parse(text)

        generated_grammar1 = str(result)
        with Path('./tmp/01.ebnf').open('w') as f:
            f.write(generated_grammar1)

        print('-' * 20, 'phase 02 - parse previous output with the parser generator')
        with Path('./tmp/01.ebnf').open() as f:
            text = str(f.read())
        g = GrammarGenerator('EBNFBootstrap')
        result = g.parse(text)
        generated_grammar2 = str(result)
        with Path('./tmp/02.ebnf').open('w') as f:
            f.write(generated_grammar2)
        self.assertEqual(generated_grammar2, generated_grammar1)

        print('-' * 20, 'phase 03 - repeat')
        with Path('./tmp/02.ebnf').open() as f:
            text = f.read()
        g = EBNFParser('EBNFBootstrap')
        ast3 = g.parse(text)
        with Path('./tmp/03.ast').open('w') as f:
            f.write(json.dumps(asjson(ast3), indent=2))

        print('-' * 20, 'phase 04 - repeat')
        with Path('./tmp/02.ebnf').open() as f:
            text = f.read()
        g = GrammarGenerator('EBNFBootstrap')
        parser = g.parse(text)
    #    pprint(parser.first_sets, indent=2, depth=3)
        generated_grammar4 = str(parser)
        with Path('./tmp/04.ebnf').open('w') as f:
            f.write(generated_grammar4)
        self.assertEqual(generated_grammar4, generated_grammar2)

        print('-' * 20, 'phase 05 - parse using the grammar model')
        with Path('./tmp/04.ebnf').open() as f:
            text = f.read()
        ast5 = parser.parse(text)
        with Path('./tmp/05.ast').open('w') as f:
            f.write(json.dumps(asjson(ast5), indent=2))

        print('-' * 20, 'phase 06 - generate parser code')
        gencode6 = codegen(parser)
        with open('./tmp/g06.py', 'w') as f:
            f.write(gencode6)

        print('-' * 20, 'phase 07 - import generated code')
        py_compile.compile('./tmp/g06.py', doraise=True)
        # g06 = __import__('g06')
        # GenParser = g06.EBNFBootstrapParser
        # assert GenParser

        # print('-' * 20, 'phase 08 - compile using generated code')
        # parser = GenParser(trace=False)
        # result = parser.parse(original_grammar, semantics=ASTSemantics, parseinfo=False)
        # ast8 = json.dumps(asjson(result), indent=2)
        # open('./tmp/08.ast', 'w').write(ast8)
        # self.assertEqual(ast0, ast8)

        print('-' * 20, 'phase 09 - Generate parser with semantics')
        with Path('grammar/tatsu.ebnf').open() as f:
            text = f.read()
        parser = GrammarGenerator('EBNFBootstrap')
        g9 = parser.parse(text)
        generated_grammar9 = str(g9)
        with open('./tmp/09.ebnf', 'w') as f:
            f.write(generated_grammar9)
        self.assertEqual(generated_grammar9, generated_grammar1)

        print('-' * 20, 'phase 10 - Parse with a model using a semantics')
        g10 = g9.parse(
            text,
            start_rule='start',
            semantics=EBNFGrammarSemantics('EBNFBootstrap'),
        )
        generated_grammar10 = str(g10)
        with open('./tmp/10.ebnf', 'w') as f:
            f.write(generated_grammar10)
        gencode10 = codegen(g10)
        with open('./tmp/g10.py', 'w') as f:
            f.write(gencode10)

        print('-' * 20, 'phase 11 - Pickle the model and try again.')
        with open('./tmp/11.tatsu', 'wb') as f:
            pickle.dump(g10, f)
        with open('./tmp/11.tatsu', 'rb') as f:
            g11 = pickle.load(f)
        r11 = g11.parse(
            text,
            start_rule='start',
            semantics=EBNFGrammarSemantics('EBNFBootstrap'),
        )
        with open('./tmp/11.ebnf', 'w') as f:
            f.write(str(g11))
        gencode11 = codegen(r11)
        with open('./tmp/bootstrap_g11.py', 'w') as f:
            f.write(gencode11)

        print('-' * 20, 'phase 12 - Walker')

        class PrintNameWalker(DepthFirstWalker):
            def __init__(self):
                super().__init__()
                self.walked = []

            def walk_default(self, o, children):
                self.walked.append(o.__class__.__name__)

        v = PrintNameWalker()
        v.walk(g11)
        with open('./tmp/12.txt', 'w') as f:
            f.write('\n'.join(v.walked))

        print('-' * 20, 'phase 13 - Graphics')
        try:
            from tatsu.diagrams import draw
        except ImportError:
            print('PyGraphViz not found!')
        else:
            if not util.PY37:
                draw('./tmp/13.png', g11)


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(BootstrapTests)


def main():
    unittest.TextTestRunner(verbosity=2).run(suite())


if __name__ == '__main__':
    main()

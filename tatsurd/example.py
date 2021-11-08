import io
import tatsu
from tatsurd import TatSuRDG

path_to_grammar = "../examples/calc/grammars/calc.ebnf"  # path to your tatsu ebnf grammar
with io.open(path_to_grammar, 'r', encoding="utf-8") as file:
    grammar = file.read()

parser = tatsu.compile(grammar)
rg = TatSuRDG(parser)
# you may also override the default behavior of single rules by providing a dictionary of default values for them
# rg = TatSuRDG(parser, max_length_regex=5, override_placeholders={"number": "42"})

for i in range(1, 50):
    rg.init_rules()
    print(rg.random_derivation("expression"))

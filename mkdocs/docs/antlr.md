# ANTLR Grammars

[ANTLR](http://www.antlr.org/) is one of the best known parser genrators, and it has an important collection of [grammars](https://github.com/antlr/grammars-v4). The `tatsu.g2e` module can translate an [ANTLR](http://www.antlr.org/) grammar to the syntax used by {{TatSu}}.

The resulting grammar won't be immediately usable. It will have to be edited to make it abide to [PEG](http://en.wikipedia.org/wiki/Parsing_expression_grammar) semantics, and in general be adapted to the way things are done with {{TatSu}}.

To use `g2e` as a module, invoke one of its translation functions.

``` python
def translate(text=None, filename=None, name=None, encoding='utf-8', trace=False):
```

For example:

``` python
from tatsu import g2e

tatsu_grammar = translate(filename='mygrammar.g', name='My')
with open('my.tatsu') as f:
    f.write(tatsu_grammar)
```

`g2e` can also be used from the command line:

``` bash
$ python -m tatsu.g2e mygrammar.g > my.tatsu
```

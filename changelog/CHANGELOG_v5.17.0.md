
## The Big and Beautiful Refactoring

Maintenance and contributions to **[TatSu][]** have been more difficult than necessary because of the way the code evolved through the years while adding features.

- Very long modules and classes that try to do too much
- Algorithms difficult to understand or incorrect semantics
- Basic features missing because the above made them hard to implement

This release is a major refactoring of the code in **[TatSu][]**.

- Complex modules were partitioned into sub-modules and classes with well defined purpose
- Algorithms were rewritten to make their semantics clear and evident
- Many unit tests were added to assert the semantics of complex algorithms
- Some user-facing features were added as they became easy to implement

For the details about the many changes please take a look at the [commit log][].

## User-Facing Changes

- `walkers.NodeWalker` now handles all known types of input. Also: 
	- `DepthFirstWalker` was reimplemented to ensure DFS semantics
	- `PreOrderWalker` was broken and crazy. It was rewritten as a `BreadthFirstWalker` with the correct semantics
- Constant expressions in a grammar are now evaluated deeply with  multiple passes of `eval()` to produce results more as expected
```python
def test_constant_math():
    grammar = r"""
        start = a:`7` b:`2` @:```{a} / {b}``` $ ;
    """
    result = parse(grammar, '', trace=True)
    assert result == 3.5

```
- Evaluation of Python expressions by the parsing engine now use `safe_eval()`, a hardened firewall around most security attacks targeting `eval()` (see the [safeeval][] module for details)
- Because `None` is a valid initial value for attributes and a frequent return value for callables, the required logic for undefined values was moved to the `notnone` module, which declares `Undefined` as an alias for `notnone.NotNone`
```python
In [1]: from tatsu.util.notnone import Undefined
In [2]: u = Undefined
In [3]: u is None
Out[3]: False
In [4]: u is Undefined
Out[4]: True
In [5]: Undefined is None
Out[5]: False
In [6]: d = u or 'ok'
In [7]: d
Out[7]: 'ok'
```
- `objectmodel.Node` was rewritten to give it clear semantics and efficiency
	- No Python attributes are created with `setattr()`, .  No new attributes may be defined on a `Node` after initialization
	- `Node.children()` has the expected semantics now, it was made much more efficient, and is now recalculated on each call in consistency with the mutability of `Node`
- `Node.parseinfo` is honored by the parsing engine, when previously only results of type `AST` had a `parseinfo`
```python
      def test_node_parseinfo(self):
        grammar = """
            @@grammar :: Test
            start::Test = true | false ;
            true = "test" @:`True` $;
            false = "test" @:`False` $;
        """

        text = 'test'
        node = tatsu.parse(grammar, text, asmodel=True, parseinfo=True, )
        assert type(node).__name__ == 'Test'
        assert node.ast is True
        assert node.parseinfo is not None
        assert node.parseinfo.pos == 0
        assert node.parseinfo.endpos == len(text)

```
- Synthetic classes created by `synth.synthetize()` during parsing with `semantics.ModeleBuilderSemantics` behave more consistently, and now have a base class of `class SynthNode(BaseNode):` 

[TatSu]: https://github.com/neogeny/TatSu
[commit log]: https://github.com/neogeny/TatSu/commits/
[safeeval]: https://github.com/neogeny/TatSu/blob/master/tatsu/util/safeeval.py

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

Every effort has been made to preserve backwards compatibility by keeping mosts unit tests intact and running projects with large grammars and complex processing. If something escaped, there will be a minor release with the fixes.

### User-Facing Changes

- Now `tatsu.parse(...., asmodel=True)` produces the same model result as `tatsu.to_python_model()` 	
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
- `Node.parseinfo` is honored by the parsing engine, when previously only results of type `AST` could have a `parseinfo`. Generation of `parseinfo` is disabled by defaulti, so pass `pareseinfo=True` to the API entry points to enable it.
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
<<<<<<< HEAD
- Synthetic classes created by `synth.synthetize()` during parsing with `semantics.ModeleBuilderSemantics` behave more consistently, and now have a base class of `class SynthNode(BaseNode)`
- The API and other entry now check that the value provided for `semantics=` is an object instance and not a `type/class`
=======
- Synthetic classes created by `synth.synthetize()` during parsing with `ModeleBuilderSemantics` behave more consistently, and now have a base class of `class SynthNode(BaseNode)`
- `ast.AST` now has consistent semantics of a `dict` that allows access to contents using an attributes interface
- `asjson()` and friends now cover all cases with improved consistency and efficiency, and less demands over users of the API
- Documentation has a better look and improved navigation thanks to using `MyST-Parser` with `Sphinx`
- [TatSu][] still has no library dependencies for its core functionality, but several libraries are used during its development and testing. [TatSu][] configuration uses `uv` and `hatch`, but several `requirements-xyz.txt` files are generated in favor of those using `pip` with `pyenv`, `virtualenvwrapper`, or `virtualenv`
- Many of the functions that [TatSu][] defines for its own use are useful in other contexts. Examples are:
```python
	from tatsu.notnone import Undefined
	from tatsu.safeeval import is_eval_safe()
	from tatsu.safeeval import hasshable()
	from tatsu.safeeval import make_hashable()
	from tatsu.util import safe_name()
	from tatsu.util.misc import find_from_rematch()
	from tatsu.util.misc import topsort()
	# ... and many more
```
>>>>>>> master

[TatSu]: https://github.com/neogeny/TatSu
[commit log]: https://github.com/neogeny/TatSu/commits/
[safeeval]: https://github.com/neogeny/TatSu/blob/master/tatsu/util/safeeval.py
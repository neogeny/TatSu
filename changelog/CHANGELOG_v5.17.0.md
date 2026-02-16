## The Overdue Major Refactoring

Maintenance and contributions to **TatSu** have been more difficult than necessary because of the way the code evolved through its lifetime.

- Very long modules and classes that try to do too much
- Algorithms difficult to understand or with incorrect semantics
- Basic features missing, because the above made them hard to implement

This release is a major refactoring of the code in **TatSu**.

- Complex modules were partitioned into sub-modules and classes with well-defined purpose
- Several algorithms were rewritten to make their semantics clear and evident, and their implementation more efficient
- Many unit tests were added to assert the semantics of complex algorithms
- Several user-facing features were added as they became easier to implement

For the details about the many changes please take a look at the [commit log][].

* **pypi:** https://pypi.org/project/TatSu/
* **docs:** https://tatsu.readthedocs.io/
* **repo:** https://github.com/neogeny/TatSu

Every effort has been made to preserve backwards compatibility by keeping most unit tests intact and testing with projects with large grammars and complex processing. If something escaped those tests, there will be a bugfix release with the fixes soon enough.

### User-Facing Changes

- The [**TatSu** documentation](https://tatsu.readthedocs.io) has been improved and expanded, and it has a better look&feel with improved navigation.
- **TatSu** doesn't care about file names, but the default extension used in unit tests, examples, and documentation for grammars is now `.tatsu`
- EBNF, both ISO and the classic variations, is fully supported as grammar input format
- Now `tatsu.parse(...., asmodel=True)` produces a model that matches the `::Type` declarations in their grammar (see the [models][] documentation for a thorough review of the features).
- `walkers.NodeWalker` now handles all known types of input.
   Also:
    - `DepthFirstWalker` was reimplemented to ensure DFS semantics
    - `PostOrderDepthFirstWalker` walks children before parents
    - `PreOrderWalker` was broken and crazy. It was rewritten as a `BreadthFirstWalker` with the correct semantics
- Constant expressions in a grammar are now evaluated deeply with  multiple passes of `eval()` as to produce results that are intuitively correct:

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
    In [1]: from tatsu.util.undefined import Undefined
    In [2]: u = Undefined
    In [3]: u is None
    Out[3]: False
    In [4]: u is Undefined
    Out[4]: True
    In [5]: Undefined is None
    Out[5]: False
    In [6]: d = u or 'OK'
    In [7]: d
    Out[7]: 'OK'
  ```
- `objectmodel.Node` was rewritten to give it clear semantics and efficiency
    - New attributes to `Node` after initialization generate a warning if the name of a method is being shadowed. This change avoids confusing `@dataclass`, which is used in generated object models.
    - `Node` equality is explicitly defined as object identity. No attempts are made at comparing `Node` structurally.
    - `Node.children()` has the expected semantics, and is much more efficient.
- `Node.parseinfo` is now honored by the parsing engine (previously, only results of type `AST` could have a `parseinfo`). Generation of `parseinfo` is disabled by default, and is enabled by passing `pareseinfo=True` to the API entry points.

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
- Synthetic classes created by `synth.synthetize()` during parsing with `ModelBuilderSemantics` behave more consistently, and now have a base class of `class SynthNode(BaseNode)`
- Now `ast.AST` has consistent semantics of a `dict` that allows access to contents using the attribute interface
- `asjson()` and friends now cover all known cases with improved consistency and efficiency, so there are less demands over clients of the API
- Entry points no longer list a large subset of the configuration options defined in `ParserConfig`, but still accept them through `**settings` keyword arguments. Now `ParserConfig` verifies that the settings passed to are valid, eliminating the frustration of passing an incorrect setting name (a typo) and hoping it has the intended effect.
- **TatSu** still has no library dependencies for its core functionality, but several libraries
  are used during its development and testing. The **TatSu** development configuration uses `uv` and `hatch`. Several `requirements-xyz.txt` files are generated in favor of those using `pip` with `pyenv`, `virtualenvwrapper`, or `virtualenv`
- All attempts at recovering comments from parsed input were removed. It never worked, so it had no use. Comment recovery may be attempted in the future.
- All pre-existing grammars are compatible with this version of **TatSu**.
- Previously generated Python parsers and models, work with this version of **TatSu**, yet *you should* consider generating them anew to take advantage of the improved speed, layout, and features.
- *CAVEAT:* Several functions, methods, and argument names were deprecated. They can still be used, but *warnings* will be issued at runtime.
- *CAVEAT:* If there are invalid strings or regex patterns in your grammars *YOU MUST* fix them because now the grammar parser validates strings and patterns.
- Many of the functions that **TatSu** defines for its own use are useful in other contexts. Some examples are:

    ```python
        from tatsu.safeeval import is_eval_safe
        from tatsu.safeeval import hasshable
        from tatsu.safeeval import make_hashable
        from tatsu.util import safe_name
        from tatsu.util.misc import find_from_rematch
        from tatsu.util.misc import topsort
        from tatsu.util.undefined import Undefined
        # ...
    ```

[TatSu]: https://github.com/neogeny/TatSu
[commit log]: https://github.com/neogeny/TatSu/commits/
[safeeval]: https://github.com/neogeny/TatSu/blob/master/tatsu/util/safeeval.py
[models]: https://tatsu.readthedocs.io/en/stable/models.html

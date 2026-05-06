[//]: Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
[//]: SPDX-License-Identifier: BSD-4-Clause

# v5.19.0

- The `$->` (EOL) expression was introduced in the grammar language to match and
  consume the whitespace up to and including the next line break, using the
  Python semantics of `os.linesep`. The match interprets whitespace using the
  Python definition as implemented by `str.isspace()`, so beware when
  a particular definition of _whitespace_ is part of the language to parse.

- The `@nostak` decorator for rules was added to the grammar. The setting hints
  the tracer and error handler that the rule should not be part of the call stack.
  The setting is useful to avoid noise in traces when low-level rules (like those
  for qualified or attributed identifiers) form their own small hierarchy.

- The file extension for **TatSu** grammars is now `.ebnf`. The grammar language
  is, after all, an _extension_ of the most known forms of EBNF syntax. Syntax
  highlighters may recognize the extension

- The benchmark in `tatsu.tool.bench` was used over several large grammars and
  large input sets to evaluate parser strategies. The result is that there is a
  1.3x performance advantage in generating a Python program versus using the
  in-memory model of the parsed **TatSu** grammar for parsing. In tests with
  complex projects (Java) the performance difference is not perceivable. The
  [codspeed][] benchmark that runs with unit tests on GitHub doesn't see the
  performance difference either.

  [codspeed]: https://codspeed.io

  Now **TatSu** uses for bootstrap a module that loads its own grammar model
  as the main parser (the one used by `tatsu.compile()`). The previous kind of
  parser can still be generated with `tatsu.to_python_sourcecode()`, which
  remains well tested in several unit tests. The new model-based kind of parser
  can be generated with `tatsu.to_parsermodel_sourcecode()`.

  Note that you don't need to generate any source code for a parser in your own
  projects. **TatSu** does generate a module to make it faster to bootstrap
  a parser from its own grammar. In your projects you can run the usual steps
  to have a performant parser:

    ```python
    import tatsu

    grammartext = ...

    model = tatsu.compile(grammartext, asmodel=True)
    output = model.parse(input)
    ```
  Generating a module with classes for the type definitions in the grammar is
  still useful.

    ```python
    from pathlib import Path
    import tatsu

    grammartext = ...

    sourcecode = tatsu.to_python_model(grammartext)
    Path('./modelclases.py').write_text(sourcecode)
    ```
- Optimizations in the parser logic produce parsing speeds comparable to those
  of **TatSu** v5.16 with any parsing strategy (model or generated code).

- The old parser and model generator modules in `tatsu.codegen` have been deleted.
  Using [pyrefly][] revealed that they are both incorrect and non-working. Their
  defunctness was caused by the lack of unit tests and their lack of use since
  `tatsu.ngcodegen` was introduced several years ago. The helper modules
  `codegen.cgbase` and `codegen.rendering` remain in case any old projects use
  them for their own code generation.

  [pyrefly]: https://pypi.org/project/pyrefly/

- The `g2e` example in `./examples/g2e` was removed. The example had become
  irrelevant now that the new PEG parser in Python uses a [pegen][]-style grammar
  for the language that is less than a 1000 lines long. The **TatSu** grammar
  for ANTLR in `./examples/g2e/antlr.tatsu` can still parse ANTLR grammars, but
  there's no test case for it. The semantics in `g2e.semanrics.ANTLRSemantics`
  try to do everything on a single pass (like substituting simple TOKEN rules by
  their value), when transformation of the parsed input grammar model should be
  more stable and easier to understand with a simplerr approach.

  [pegen]: https://we-like-parsers.github.io/pegen/grammar.html

- There's no longer a separate stack for the state of `cut`. The state of `cut`
  is kept in the general state stack.

- A new `@statescope` context manager takes care of handling the state stack in most cases.

- Lookaheads are always memoized. Configuration settings for disabling it
  have been deprecated and disabled.

- A new `PaserConfig.perlinememos: float` configuration sets a `(perlinememos * linecount) `
  bound on the total number of memoization entries that are allowed on each parse.

- Incorporated [zuban][] to the set of type linters.

  [zuban]: https://github.com/zubanls/zuban

- Introduced `objectmodel.ctx.CanParse(Protocol)` defining the `parse()` method
  for entry point to parsing.

- An important refactoring was done to get rid of the legacy names *"tokenizing"*
  and *"tokenizer"* which didn't abide to theory and practice of parsing. Now the
  names are `tatsu.input`, `tatsu.input.text`, and `tatsu.input.text.Text`. The
  old names are still available as legacy for backwards compatibility.

- Rule invludes (`RuleInclude`) kept an atcutal copy of the included rule in the
  model. To preserve consistent semantics, the only mentions of `Rule` in a model
  are at the top-level, in `Grammar.rules` and `Grammar.rulemap`.

- Grammar models that haven't been compiled from a grammar but instead loaded from
  the JSON or Python representations don't need to be analyzed for left recursion,
  because the markers of the analysis are already in the loaded models. A new
  `Grammar.analyzed: bool` attribute was added to quickly check if a grammar model
  from any source has already been analyzed.
- Support for `#include` in grammars has been dropped. It was always a bad idea.
  Text-to-text preprocessing doesn't belong in the grammar in part because it
  doesn't apply to input sources that are not text, like that of tokenizers or
  streams. The class `tatsu.input.buffer.Buffer` still has all the infrastrucure for
  supporting C-style or COBOL-style textual includes, and its definition of
  `BufferCursor` honors it. `Buffer` keeps track of which file was the source of
  each line of input, something essential for good error reporting. During
  compilation of grammar text to a `Grammar` object, the grammar text is the
  parser's input, so the `Cursor` semantics regarding the parsing still apply.
- The CLI tool now has a `--json` option to produce the JSON version of the model
  for a grammar. Re-importing of a JSON model is not yet implemented in **TatSu**, but **[TieXiu](https://github.com/neogeny/tiexiu)** uses them successfully as the fast way to import a **TatSu** grammar model.

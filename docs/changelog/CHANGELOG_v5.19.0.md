[//]: Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
[//]: SPDX-License-Identifier: BSD-4-Clause

# v5.19.0

- The benchmark in `tatsu.tool.bench` was used over several large grammars and
  large input sets. The result as that there is no performance advantage in
  renerating a procedural Python program for a parser because the in-memory
  model of the parsed **TatSu** grammar performs equally well. 

  Now **TatSu** uses for bootstrap a module that loads its own grammar model to 
  ase main parser (the one used by `tatsu.compile()`). The previous kind of parser 
  can still be generated with `to_python_sourcecode()`. The new kind of parser  
  can be generated with `to_parse_with_model_sourcecode()`.

  Note that you don't need to generate any source code for a parser in your own 
  projects. **TatSu** does generate a module to make it faster to bootstrap 
  a parser from it's own grammar. In your projects you can run the usual steps
  to have a performant parser:

    ```python
    model = tatsu.compile(grammartext, asmodel=True)
    output = model.parse(input)
    ```
  Generating a module with classes for the type definitions in the grammar is
  still useful.

    ```python
    sourcecode = to_python_model(grammartext)
    Path('./modelclases.py').write_text(sourcecode)
    ```
  still be useful:

- There's no longer a separate stack for the state of `cut`. The state of `cut`
  is kept in the general state stack.

- A new `@statescope` context manager takes care of handling the state stack in most cases.

- Lookaheads are always memoized. Configuration settings for disabling it 
  have been deprecated and disabled. 

- A new `PaserConfig.perlinememos: float` configuration sets a `(perlinememos * linecount) ` 
  bound on the total number of memoization entries that are allowed on each parse.

- Incorporated [zuban][] to the set of type linters.

- Introduced `objectmodel.ctx.CanParse(Protocol)` defining the `parse()` method
  for entry point to parsing.

- An important refactoring was done to get rid of the legacy names *"tokenizing"*
  and *"tokenizer"* which didn't abide to theory and practice of parsing. Now the
  names are `tatsu.input`, `tatsu.input.text`, and `tatsu.input.text.Text`. The
  olde names are still available as legacy for backwards compatibility.

[zuban]: https://github.com/zubanls/zuban 

[//]: Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
[//]: SPDX-License-Identifier: BSD-4-Clause

# v5.18.1

- The benchmark in `tatsu.tool.bench` was used over several large grammars and
  large input sets. The result is that there is no performance advantage in
  renerating a procedural Python program for the parser, because the in-memory
  model of the parsed **TatSu** grammar performs equally well. Now **TatSu**
  uses for bootstrap a module that loads its grammar model to perform the parse.
  The old kind of parser can still be generated with `to_python_sourcecode(()`
  but **TatSu** uses the new type of parser wich is generated with the new
  `to_modelparser_sourcecode()`.

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

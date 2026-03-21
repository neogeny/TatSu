[//]: Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
[//]: SPDX-License-Identifier: BSD-4-Clause

# v5.18.1


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

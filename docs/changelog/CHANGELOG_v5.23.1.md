<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# [v5.23.1] new features + bugfixes + (- dependencies)

[v5.23.1]: https://github.com/neogeny/tatsu/compare/v5.23.0...HEAD

## Changed

- Every optimization to core parsing for trying to make model-based parsing faster, also optimizes generated procedural parsers. As a result, `bootstrap.py` (the generated parser) is now about 25% faster than before, and 2.5x faster than `bootparser.py` (the model-based parser). The structural difference between the two types of parser is that all calls happen on two objects (`ParserMethods` and `Context`) in the generated parser, and across many in the model. In the lack of a better explanation or an optimization strategy, the default parser is again `bootstrap.py`.

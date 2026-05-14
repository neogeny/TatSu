<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# v5.19.1 Maintenance Release

* The algorithm for left-recursion analysis went over another round of simplification and optimization. Although the analysis is performed once per `Grammar`, before any parsing, a simpler implementation makes this core part of **TatSu** easier to maintain.

* Added better rendering to `FailedParse.__str__()`. Now a code fragment and line numbers are shown, as in many modern tools.

    ```console
    error: expecting 'world'
      --> example:1:7
       |
     1 | hello missing
       |       ^ expecting 'world'
    
      -> start
    ```

### JSON

* Now a `Grammar` can be imported from the JSON produced by `model.asjson()`. Roundtrip has been tested and it works. New methods `Grammar.load(value: Any) -> Grammar` and `Grammar.loads(json: str) -> Grammar` make the functionality available.

### Grammar Syntax

* The definition of the `DEDENT` rule in the **TatSu** grammar is used to support
  EBNF notations with no rule-terminatiors and grammars without blank lines
  between rules. The pattern used in the rule was incorrectly consuming the first
  non-space character starting the new rule.

  This is a valid EBNF definition:

    ```python
    grammar = r"""
        @@grammar :: MiniJSON
        @@nameguard :: False
        @@whitespace :: /\s+/
        start: value $

        value: object | array | string | number | 'true' | 'false' | 'null'

        object: '{' members? '}'
        array: '[' elements? ']'
        members: pair (',' pair)*
        elements: value (',' value)*
        pair: string ':' value
        string: '"' CONTENT '"'
        CONTENT: /[^"]*/
        number: /-?\d+(\.\d+)?/
    """
    ```

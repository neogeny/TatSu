<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# v5.19.1 Maintenance Release


## Internals

* The algorithm for left-recursion analysis went over another round of simplification and optimization. Then the analysis done in [pegen][], a more efficient and theoretically-sound approach, was evaluated. All tests pass with the [pegen][]'s `SCC` (_Strongly Connected Componets_) algorithm, so the old-and-tried algorithm in **TatSu** was replaced.

  Although left-recursion analysis is performed once per `Grammar`, before any parsing, a simpler implementation makes this core part of **TatSu** easier to maintain.

[pegen]: https://we-like-parsers.github.io/pegen/grammar.html

## g2e (ANTLR to TatSu)

* The `g2e` (ANTLR grammar to TatSu) translator has been revived and
  significantly simplified. A working example (`python3.tatsu`, 551 lines)
  is generated from Python 3's full ANTLR grammar and passes
  `tatsu.compile()`.

* Removed the regex conversion approach for ANTLR token rules. ANTLR
  lexer patterns (notably `\uXXXX` escapes) are not viable as Python
  regex patterns. Non-trivial token rules now emit `Fail()` instead of
  `Pattern`. The classes and methods `TokenPattern`,
  `_token_expr_to_regex`, `_token_expr_to_regex_verbose`,
  `_decode_antlr_string`, and `_char_to_regex` have been removed.

* Streamlined generated grammar output — removed unnecessary
  parenthesization:
  - Single token references in alternatives no longer wrapped in extra
    parens: `(NEWLINE)` → `NEWLINE`.
  - Groups inside `[...]`, `{...}`, `{...}+` unwrapped:
    `[('as' NAME)]` → `['as' NAME]`,
    `{('.' NAME)}` → `{'.' NAME}`.
  - Rule deduplication by name handles `tokens {}` declarations that
    collide with defined rules (e.g. `INDENT`/`DEDENT`).

* Token name resolution now uses uppercase names consistently.

## Tools

* A new `--recursion-limit` (`-R1`) option was added to the `tatsu` CLI tool
  so it can handle large and deeply recursive input grammars. When used as a
  library, the host program should call `sys.setrecursionlimit()` when
  required by the grammar complexity.

* Added better rendering to `FailedParse.__str__()`. Now a code fragment and line numbers are shown, as in many modern tools.

    ```console
    error: expecting 'world'
      --> example:1:7
       |
     1 | hello missing
       |       ^ expecting 'world'

      -> start
    ```

## JSON

* `tatsu.ebnf` define rules for JSON literals, so `true`, `false`, and `null`,
  may be used where previously only `True`, `False`, and `None` were recognized.
  The Python literals are still honored as before, as well as the `boolean` rule
  resolving to `True` for non-falsy values. These literals are only used in 
  grammar directives, as parsing is only interested in the strings that match
  a `Token` or `Pattern`.

* Now a `Grammar` can be imported from the JSON produced by `model.asjson()`. 
  Roundtrip has been tested and it works. New methods 
  `Grammar.load(value: Any) -> Grammar` 
  and `Grammar.loads(json: str) -> Grammar` 
  make the functionality available.

    ```python
    class Grammar:
        @staticmethod
        def load(value: Any) -> Grammar:
            from .json import load_grammar
            return load_grammar(value)
    
        @staticmethod
        def loads(value: str) -> Grammar:
            from .json import loads_grammar
    
            return loads_grammar(value)
    ```

## Grammar Syntax

* The definition of the `DEDENT` rule in the **TatSu** grammar is used to
  support EBNF notations with no rule-terminatiors and grammars with no blank
  lines * rules. The pattern used in the rule was incorrectly consuming the
  first non-space character starting the next rule. Fixed.

  Now this is a valid EBNF definition:

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

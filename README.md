[![fury](https://badge.fury.io/py/tatsu.svg)](https://badge.fury.io/py/tatsu)
[![license](https://img.shields.io/badge/license-BSD-blue.svg)](https://raw.githubusercontent.com/apalala/tatsu/master/LICENSE.txt)
[![pyversions](https://img.shields.io/pypi/pyversions/tatsu.svg)](https://pypi.python.org/pypi/tatsu)
[![travis](https://secure.travis-ci.org/apalala/tatsu.svg)](http://travis-ci.org/apalala/tatsu)

[//]: # [![landscape](https://landscape.io/github/apalala/tatsu/release/landscape.png)](https://landscape.io/github/apalala/tatsu/release)

> _At least for the people who send me mail about a new language that they're designing, the general advice is: do it to learn about how to write a compiler. Don't have any expectations that anyone will use it, unless you hook up with some sort of organization in a position to push it hard. It's a lottery, and some can buy a lot of the tickets. There are plenty of beautiful languages (more beautiful than C) that didn't catch on. But someone does win the lottery, and doing a language at least teaches you something._
>
>[Dennis Ritchie] (1941-2011)
>    _Creator of the [C][] programming language and of [Unix][]_


Tatsu
=====

    Copyright (C) 2017 Juancarlo Añez

----

> [![donate][btn_donate]][donate]
>
> _If you'd like to contribute to the future development of **Tatsu**, please_
> **[make a donation][donate]** to the project.
>
> _Some of the planned new features are: grammar expressions for left and right
> associativity, new algorithms for left-recursion, a unified intermediate
> model for parsing and translating programming languages, and more..._

----

[donate]: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=P9PV7ZACB669J
[btn_donate]: https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif


**Tatsu** (for *grammar compiler*) is a tool that takes grammars in a
variation of [EBNF][] as input, and outputs [memoizing][] ([Packrat][]) [PEG][]
parsers in [Python][].

**Tatsu** can also compile a grammar stored in a string into a `tatsu.grammars.Grammar` object that can be used to parse any given input, much like the [re][] module does with regular expressions.


**Tatsu** is *different* from other [PEG] parser generators:

-   Generated parsers use [Python]'s very efficient exception-handling
    system to backtrack. **Tatsu** generated parsers simply assert what
    must be parsed. There are no complicated *if-then-else* sequences
    for decision making or backtracking. Memoization allows going over
    the same input sequence several times in linear time.
-   *Positive and negative lookaheads*, and the *cut* element (with its
    cleaning of the memoization cache) allow for additional,
    hand-crafted optimizations at the grammar level.
-   Delegation to [Python]'s [re] module for *lexemes* allows for
    ([Perl]-like) powerful and efficient lexical analysis.
-   The use of [Python]'s [context managers] considerably reduces the
    size of the generated parsers for code clarity, and enhanced
    CPU-cache hits.
-   Include files, rule inheritance, and rule inclusion give **Tatsu**
    grammars considerable expressive power.
-   Automatic generation of Abstract Syntax Trees\_ and Object Models,
    along with *Model Walkers* and *Code Generators* make analysis and
    translation approachable

The parser generator, the run-time support, and the generated parsers
have measurably low [Cyclomatic complexity]. At around 5 [KLOC] of
[Python], it is possible to study all its source code in a single
session.

The only dependencies are on the [Python] standard library, yet the
[regex] library will be used if installed, and [colorama] will be used
on trace output if available. [pygraphviz] is required for generating
diagrams.

**Tatsu** is feature-complete and currently being used with complex
grammars to parse, analyze, and translate hundreds of thousands of lines
of input text, including source code in several programming languages.

Table of Contents
-----------------

[TOC]

Rationale
---------

**Tatsu** was created to address some recurring problems encountered
over decades of working with parser generation tools:

-   Some programming languages allow the use of *keywords* as
    identifiers, or have different meanings for symbols depending on
    context ([Ruby]). A parser needs control of lexical analysis to be
    able to handle those languages.
-   LL and LR grammars become contaminated with myriads of lookahead
    statements to deal with ambiguous constructs in the source language.
    [PEG] parsers address ambiguity from the onset.
-   Separating the grammar from the code that implements the semantics,
    and using a variation of a well-known grammar syntax ([EBNF]) allows
    for full declarative power in language descriptions. General-purpose
    programming languages are not up to the task.
-   Semantic actions *do not* belong in a grammar. They create yet
    another programming language to deal with when doing parsing and
    translation: the source language, the grammar language, the
    semantics language, the generated parser's language, and the
    translation's target language. Most grammar parsers do not check the
    syntax of embedded semantic actions, so errors get reported at
    awkward moments, and against the generated code, not against
    the grammar.
-   Preprocessing (like dealing with includes, fixed column formats,
    or structure-through-indentation) belongs in well-designed program
    code; not in the grammar.
-   It is easy to recruit help with knowledge about a mainstream
    programming language like [Python], but help is hard to find for
    working with complex grammar-description languages. **Tatsu**
    grammars are in the spirit of a *Translators and Interpreters 101*
    course (if something is hard to explain to a college student, it's
    probably too complicated, or not well understood).
-   Generated parsers should be easy to read and debug by humans.
    Looking at the generated source code is sometimes the only way to
    find problems in a grammar, the semantic actions, or in the parser
    generator itself. It's inconvenient to trust generated code that one
    cannot understand.
-   [Python] is a great language for working with language parsing
    and translation.

The Generated Parsers
---------------------

A **Tatsu** generated parser consists of the following classes:

-   A `MyLanguageBuffer` class derived from `tatsu.buffering.Buffer`
    that handles the grammar definitions for *whitespace*, *comments*,
    and *case significance*.
-   A `MyLanguageParser` class derived from `tatsu.parsing.Parser` which
    uses a `MyLanguageBuffer` for traversing input text, and implements
    the parser using one method for each grammar rule:

```python
        def _somerulename_(self):
            ...
```

-   A `MyLanguageSemantics` class with one semantic method per
    grammar rule. Each method receives as its single parameter the
    [Abstract Syntax Tree] ([AST][Abstract Syntax Tree]) built from the
    rule invocation:

```python
        def somerulename(self, ast):
            return ast
```

-   A `if __name__ == '__main__':` definition, so the generated parser
    can be executed as a [Python] script.

The methods in the delegate class return the same [AST][Abstract Syntax
Tree] received as parameter, but custom semantic classes can override
the methods to have them return anything (for example, a [Semantic
Graph]). The semantics class can be used as a template for the final
semantics implementation, which can omit methods for the rules that do
not need semantic treatment.

If present, a `_default()` method will be called in the semantics class
when no method matched the rule name:

```python
def _default(self, ast):
    ...
    return ast
```

If present, a `_postproc()` method will be called in the semantics class
after each rule (including the semantics) is processed. This method will
receive the current parsing context as parameter:

```python
def _postproc(self, context, ast):
    ...
```

Using the Tool
--------------


### As a Library

**Tatsu** can be uses as a library, much like [Python][]'s `re`, by embedding grammars as strings and generating grammar models instead of generating code.

*   `tatsu.compile(grammar, name=None, **kwargs)`
>    Compiles the grammar and generates a _model_ that can subsequently be used for parsing input with.

*   `tatsu.parse(grammar, input, **kwargs)`
>    Compiles the grammar and parses the given input producing an [AST][] as result. The result is equivalent to calling `model = compile(grammar); model.parse(input)`. Compiled grammars are cached for efficiency.

*   `tatsu.to_python_sourcecode(grammar, name=None, filename=None, **kwargs)`
>   Compiles the grammar to the [Python][] sourcecode that implements the parser.

This is an example of how to use **Tatsu** as a library:

```python
GRAMMAR = '''
    @@grammar::Calc

    start = expression $ ;

    expression
        =
        | term '+' ~ expression
        | term '-' ~ expression
        | term
        ;

    term
        =
        | factor '*' ~ term
        | factor '/' ~ term
        | factor
        ;

    factor
        =
        | '(' ~ @:expression ')'
        | number
        ;

    number = /\d+/ ;
'''


def main():
    import pprint
    import json
    from tatsu import parse
    from tatsu.util import asjson

    ast = parse(GRAMMAR, '3 + 5 * ( 10 - 20 )')
    print('PPRINT')
    pprint.pprint(ast, indent=2, width=20)
    print()

    json_ast = asjson(ast)
    print('JSON')
    print(json.dumps(json_ast, indent=2))
    print()


if __name__ == '__main__':
    main()
```

And this is the output:

```bash
PPRINT
[ '3',
  '+',
  [ '5',
    '*',
    [ '10',
      '-',
      '20']]]

JSON
[
  "3",
  "+",
  [
    "5",
    "*",
    [
      "10",
      "-",
      "20"
    ]
  ]
]
```


### Compiling grammars to Python

**Tatsu** can be run from the command line:

```bash
$ python -m tatsu
```

Or:

```bash
$ scripts/tatsu
```

Or just:

```bash
$ tatsu
```

if **Tatsu** was installed using *easy\_install* or *pip*.

The *-h* and *--help* parameters provide full usage information:

```bash
$ python -m tatsu -h
usage: tatsu [--generate-parser | --draw | --object-model | --pretty]
            [--color] [--trace] [--no-left-recursion] [--name NAME]
            [--no-nameguard] [--outfile FILE] [--object-model-outfile FILE]
            [--whitespace CHARACTERS] [--help] [--version]
            GRAMMAR

Tatsu (for "grammar compiler") takes a grammar in a variation of EBNF as
input, and outputs a memoizing PEG/Packrat parser in Python.

positional arguments:
GRAMMAR               the filename of the Tatsu grammar to parse

optional arguments:
--generate-parser     generate parser code from the grammar (default)
--draw, -d            generate a diagram of the grammar (requires --outfile)
--object-model, -g    generate object model from the class names given as
                        rule arguments
--pretty, -p          generate a prettified version of the input grammar

parse-time options:
--color, -c           use color in traces (requires the colorama library)
--trace, -t           produce verbose parsing output

generation options:
--no-left-recursion, -l
                        turns left-recusion support off
--name NAME, -m NAME  Name for the grammar (defaults to GRAMMAR base name)
--no-nameguard, -n    allow tokens that are prefixes of others
--outfile FILE, --output FILE, -o FILE
                        output file (default is stdout)
--object-model-outfile FILE, -G FILE
                        generate object model and save to FILE
--whitespace CHARACTERS, -w CHARACTERS
                        characters to skip during parsing (use "" to disable)

common options:
--help, -h            show this help message and exit
--version, -v         provide version information and exit
$
```

Using the Generated Parser
--------------------------

To use the generated parser, just subclass the base or the abstract
parser, create an instance of it, and invoke its `parse()` method
passing the grammar to parse and the starting rule's name as parameter:

```python
from myparser import MyParser

parser = MyParser()
ast = parser.parse('text to parse', rule_name='start')
print(ast)
print(json.dumps(ast, indent=2)) # ASTs are JSON-friendy
```

The generated parsers' constructors accept named arguments to specify
whitespace characters, the regular expression for comments, case
sensitivity, verbosity, and more (see below).

To add semantic actions, just pass a semantic delegate to the parse
method:

```python
model = parser.parse(text, rule_name='start', semantics=MySemantics())
```

If special lexical treatment is required (as in *80 column* languages),
then a descendant of `tatsu.buffering.Buffer` can be passed instead of
the text:

```python
class MySpecialBuffer(MyLanguageBuffer):
    ...

buf = MySpecialBuffer(text)
model = parser.parse(buf, rule_name='start', semantics=MySemantics())
```

The generated parser's module can also be invoked as a script:

```bash
$ python myparser.py inputfile startrule
```

As a script, the generated parser's module accepts several options:

```bash
$ python myparser.py -h
usage: myparser.py [-h] [-c] [-l] [-n] [-t] [-w WHITESPACE] FILE [STARTRULE]

Simple parser for DBD.

positional arguments:
    FILE                  the input file to parse
    STARTRULE             the start rule for parsing

optional arguments:
    -h, --help            show this help message and exit
    -c, --color           use color in traces (requires the colorama library)
    -l, --list            list all rules and exit
    -n, --no-nameguard    disable the 'nameguard' feature
    -t, --trace           output trace information
    -w WHITESPACE, --whitespace WHITESPACE
                        whitespace specification
```

Grammar Syntax
--------------

**Tatsu** uses a variant of the standard [EBNF] syntax. Syntax
definitions for [VIM] and for [Sublime Text] can be found under the
`etc/vim` and `etc/sublime` directories in the source code distribution.

### Rules

A grammar consists of a sequence of one or more rules of the form:

```ocaml
name = <expre> ;
```

If a *name* collides with a [Python] keyword, an underscore (`_`) will
be appended to it on the generated parser.

Rule names that start with an uppercase character:

```ocaml
FRAGMENT = /[a-z]+/ ;
```

*do not* advance over whitespace before beginning to parse. This feature
becomes handy when defining complex lexical elements, as it allows
breaking them into several rules.

The parser returns an [AST][Abstract Syntax Tree] value for each rule
depending on what was parsed:

-   A single value
-   A list of [AST][Abstract Syntax Tree]
-   A dict-like object for rules with named elements
-   An object, when ModelBuilderSemantics is used
-   None

See the *Abstract Syntax Trees* and *Building Models* sections for more
details.

### Expressions

The expressions, in reverse order of operator precedence, can be:

#### `e1 | e2`

:   Choice. Match either `e1` or `e2`.

    A `|` be be used before the first option if desired:

        choices
            =
            | e1
            | e2
            | e3
            ;

#### `e1 e2`

:   Sequence. Match `e1` and then match `e2`.

#### `( e )`

:   Grouping. Match `e`. For example: `('a' | 'b')`.

#### `[ e ]`

:   Optionally match `e`.

#### `{ e }` or `{ e }*`

:   Closure. Match `e` zero or more times. Note that the
    [AST][Abstract Syntax Tree] returned for a closure is always
    a list.

#### `{ e }+`

:   Positive closure. Match `e` one or more times. The [AST][Abstract
    Syntax Tree] is always a list.

#### `{}`

:   Empty closure. Match nothing and produce an empty list as
    [AST][Abstract Syntax Tree].


#### `~`

:   The *cut* expression. Commit to the current option and prevent
    other options from being considered even if what follows fails
    to parse.

    In this example, other options won't be considered if a
    parenthesis is parsed:

        atom
            =
              '(' ~ @:expre ')'
            | int
            | bool
            ;


#### `s%{ e }+`

:   Positive join. Inspired by [Python]'s `str.join()`, it parses the same as
    this   expression:

        e {s ~ e}

    yet the result is a single list of the form:

        [e, s, e, s, e....]

    Use grouping if `s` is more complex than a *token* or a *pattern*:

        (s t)%{ e }+

#### `s%{ e }` or `s%{ e }*`

:   Join. Parses the list of `s`-separated expressions, or the empty closure.

    It is equivalent to:

        s%{e}+|{}


#### `op<{ e }+`

:   Left join. Like the _join expression_, but the result is a left-associative tree built with `tuple()`, in wich the first elelemnt is the separator (`op`), and the other two elements are the operands.

    The expression:

        '+'<{/\d+/}+

    Will parse this input:

        1 + 2 + 3 + 4

    To this tree:

        (
            '+',
            (
                '+',
                (
                    '+',
                    '1',
                    '2'
                ),
                '3'
            ),
            '4'
        )


#### `op>{ e }+`

:   Right join. Like the _join expression_, but the result is a right-associative tree built with `tuple()`, in wich the first elelemnt is the separator (`op`), and the other two elements are the operands.

    The expression:

        '+'>{/\d+/}+

    Will parse this input:

        1 + 2 + 3 + 4

    To this tree:

        (
            '+',
            '1',
            (
                '+',
                '2',
                (
                    '+',
                    '3',
                    '4'
                )
            )
        )


#### `s.{ e }+`

:   Positive _gather_. Like _positive join_, but the separator is not included in the resulting [AST][].


#### `s.{ e }` or `s.{ e }*`

:   _Gather_. Like the _join_, but the separator is not included in the resulting [AST][].

    It is equivalent to:

        s.{e}+|{}

#### `&e`

:   Positive lookahead. Succeed if `e` can be parsed, but do not
    consume any input.

#### `!e`

:   Negative lookahead. Fail if `e` can be parsed, and do not consume
    any input.

#### `'text'` or `"text"`

:   Match the token *text* within the quotation marks.

    Note that if *text* is alphanumeric, then **Tatsu** will check
    that the character following the token is not alphanumeric. This
    is done to prevent tokens like *IN* matching when the text ahead
    is *INITIALIZE*. This feature can be turned off by passing
    `nameguard=False` to the `Parser` or the `Buffer`, or by using a
    pattern expression (see below) instead of a token expression.
    Alternatively, the `@@nameguard` or `@@namechars` directives may
    be specified in the grammar:

        @@nameguard :: False

    or to specify additional characters that should also be considered
    part of names:

        @@namechars :: '$-.'

#### `r'text'` or `r"text"`

:   Match the token *text* within the quotation marks, interpreting _text_ like [Python]'s [raw string literal]s.

[string literal]: https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals
[raw string literal]: https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals


#### `?"regexp"` or `?'regexp'`

:   The _pattern_ expression. Match the [Python] regular expression
    `regexp` at the current text position. Unlike other expressions,
    this one does not advance over whitespace or comments. For that,
    place the `regexp` as the only term in its own rule.

    The *regex* is interpreted as a [Python]'s [raw string literal] and
    passed *as-is* to the [Python][] [re] module (or to
    [regex], if available), using `match()` at the current position in
    the text. The matched text is the [AST][Abstract Syntax Tree] for
    the expression.

    Consecutive patterns are concatenated to form a single one.


* `/regexp/`

:   Another form of the _pattern_ expression.


* `+/regexp/`

:   Concatenate the given pattern with the preceding one.



#### `` `constant` ``

:   Match nothing, but behave as if `constant` had been parsed.

    Constants can be used to inject elements into the concrete and
    abstract syntax trees, perhaps avoiding having to write a
    semantic action. For example:

        boolean_option = name ['=' (boolean|`true`) ] ;

#### `rulename`

:   Invoke the rule named `rulename`. To help with lexical aspects of
    grammars, rules with names that begin with an uppercase letter
    will not advance the input over whitespace or comments.

#### `>rulename`

:   The include operator. Include the *right hand side* of rule
    `rulename` at this point.

    The following set of declarations:

        includable = exp1 ;

        expanded = exp0 >includable exp2 ;

    Has the same effect as defining *expanded* as:

        expanded = exp0 exp1 exp2 ;

    Note that the included rule must be defined before the rule that
    includes it.

#### `()`

:   The empty expression. Succeed without advancing over input. Its
    value is `None`.

#### `!()`

:   The *fail* expression. This is actually `!` applied to `()`, which
    always fails.

#### `name:e`

:   Add the result of `e` to the [AST][Abstract Syntax Tree] using
    `name` as key. If `name` collides with any attribute or method of
    `dict`, or is a [Python] keyword, an underscore (`_`) will be
    appended to the name.

#### `name+:e`

:   Add the result of `e` to the [AST][Abstract Syntax Tree] using
    `name` as key. Force the entry to be a list even if only one
    element is added. Collisions with `dict` attributes or [Python]
    keywords are resolved by appending an underscore to `name`.

#### `@:e`

:   The override operator. Make the [AST][Abstract Syntax Tree] for
    the complete rule be the [AST][Abstract Syntax Tree] for `e`.

    The override operator is useful to recover only part of the right
    hand side of a rule without the need to name it, or add a
    semantic action.

    This is a typical use of the override operator:

        subexp = '(' @:expre ')' ;

    The [AST][Abstract Syntax Tree] returned for the `subexp` rule
    will be the [AST][Abstract Syntax Tree] recovered from invoking
    `expre`.

#### `@+:e`

:   Like `@:e`, but make the [AST][Abstract Syntax Tree] always be
    a list.

    This operator is convenient in cases such as:

        arglist = '(' @+:arg {',' @+:arg}* ')' ;

    In which the delimiting tokens are of no interest.

#### `$`

:   The *end of text* symbol. Verify that the end of the input text
    has been reached.

#### `#` *comment*

:   [Python]-style comments are also allowed.

When there are no named items in a rule, the [AST][Abstract Syntax Tree]
consists of the elements parsed by the rule, either a single item or a
list. This default behavior makes it easier to write simple rules:

```ocaml
number = /[0-9]+/ ;
```

Without having to write:

```ocaml
number = number:/[0-9]+/ ;
```

When a rule has named elements, the unnamed ones are excluded from the
[AST][Abstract Syntax Tree] (they are ignored).

### Deprecated Expressions

The following expressions are still recognized in grammars, but they are considered deprecated, and will be removed in a future version of **Tatsu**.

* `?/regexp/?`

:   Another form of the pattern expression that can be used when there
    are slashes (`/`) in the pattern. Use the `?"regexp"` or `?'regexp'` forms instead.

* `(*` *comment* `*)`

:   Comments may appear anywhere in the text. Use the [Python]-style comments instead.



### Rules with Arguments

**Tatsu** allows rules to specify [Python]-style arguments:

```ocaml
addition(Add, op='+')
    =
    addend '+' addend
    ;
```

The arguments values are fixed at grammar-compilation time.

An alternative syntax is available if no *keyword parameters* are
required:

```ocaml
addition::Add, '+'
    =
    addend '+' addend
    ;
```

Semantic methods must be ready to receive any arguments declared in the
corresponding rule:

```python
def addition(self, ast, name, op=None):
    ...
```

When working with rule arguments, it is good to define a `_default()`
method that is ready to take any combination of standard and keyword
arguments:

```python
def _default(self, ast, *args, **kwargs):
    ...
```

### Based Rules

Rules may extend previously defined rules using the `<` operator. The
*base rule* must be defined previously in the grammar.

The following set of declarations:

```ocaml
base::Param = exp1 ;

extended < base = exp2 ;
```

Has the same effect as defining *extended* as:

```ocaml
extended::Param = exp1 exp2 ;
```

Parameters from the *base rule* are copied to the new rule if the new
rule doesn't define its own. Repeated inheritance should be possible,
but it *hasn't been tested*.

### Rule Overrides

A grammar rule may be redefined by using the `@override` decorator:

```ocaml
start = ab $;

ab = 'xyz' ;

@override
ab = @:'a' {@:'b'} ;
```

When combined with the `#include` directive, rule overrides can be used
to create a modified grammar without altering the original.

Abstract Syntax Trees (ASTs)
----------------------------

By default, and [AST][Abstract Syntax Tree] is either a *list* (for
*closures* and rules without named elements), or *dict*-derived object
that contains one item for every named element in the grammar rule.
Items can be accessed through the standard `dict` syntax (`ast['key']`),
or as attributes (`ast.key`).

[AST][Abstract Syntax Tree] entries are single values if only one item
was associated with a name, or lists if more than one item was matched.
There's a provision in the grammar syntax (the `+:` operator) to force
an [AST][Abstract Syntax Tree] entry to be a list even if only one
element was matched. The value for named elements that were not found
during the parse (perhaps because they are optional) is `None`.

When the `parseinfo=True` keyword argument has been passed to the
`Parser` constructor, a `parseinfo` element is added to [AST][Abstract
Syntax Tree] nodes that are *dict*-like. The element contains a
`collections.namedtuple` with the parse information for the node:

```python
ParseInfo = namedtuple(
    'ParseInfo',
    [
        'buffer',
        'rule',
        'pos',
        'endpos',
        'line',
        'endline',
    ]
)
```

With the help of the `Buffer.line_info()` method, it is possible to
recover the line, column, and original text parsed for the node. Note
that when `ParseInfo` is generated, the `Buffer` used during parsing is
kept in memory for the lifetime of the [AST][Abstract Syntax Tree].

Generation of `parseinfo` can also be controlled using the
`@@parseinfo :: True` grammar directive.

Grammar Name
------------

The prefix to be used in classes generated by **Tatsu** can be passed to
the command-line tool using the `-m` option:

```bash
$ tatsu -m MyLanguage mygrammar.ebnf
```

will generate:

```python
class MyLanguageParser(Parser):
    ...
```

The name can also be specified within the grammar using the `@@grammar`
directive:

```ocaml
@@grammar :: MyLanguage
```

Whitespace
----------

By default, **Tatsu** generated parsers skip the usual whitespace
characters with the regular expression `r'\s+'` using the `re.UNICODE`
flag (or with the `Pattern_White_Space` property if the [regex] module
is available), but you can change that behavior by passing a
`whitespace` parameter to your parser.

For example, the following will skip over *tab* (`\t`) and *space*
characters, but not so with other typical whitespace characters such as
*newline* (`\n`):

```python
parser = MyParser(text, whitespace='\t ')
```

The character string is converted into a regular expression character
set before starting to parse.

You can also provide a regular expression directly instead of a string.
The following is equivalent to the above example:

```python
parser = MyParser(text, whitespace=re.compile(r'[\t ]+'))
```

Note that the regular expression must be pre-compiled to let **Tatsu**
distinguish it from plain string.

If you do not define any whitespace characters, then you will have to
handle whitespace in your grammar rules (as it's often done in [PEG]
parsers):

```python
parser = MyParser(text, whitespace='')
```

Whitespace may also be specified within the grammar using the
`@@whitespace` directive, although any of the above methods will
overwrite the setting in the grammar:

```ocaml
@@whitespace :: /[\t ]+/
```

Case Sensitivity
----------------

If the source language is case insensitive, it can be specified in the
parser by using the `ignorecase` parameter:

```python
parser = MyParser(text, ignorecase=True)
```

You may also specify case insensitivity within the grammar using the
`@@ignorecase` directive:

```ocaml
@@ignorecase :: True
```

The change will affect both token and pattern matching.

Comments
--------

Parsers will skip over comments specified as a regular expression using
the `comments_re` parameter:

```python
parser = MyParser(text, comments_re="\(\*.*?\*\)")
```

For more complex comment handling, you can override the
`Buffer.eat_comments()` method.

For flexibility, it is possible to specify a pattern for end-of-line
comments separately:

```python
parser = MyParser(
    text,
    comments_re="\(\*.*?\*\)",
    eol_comments_re="#.*?$"
)
```

Both patterns may also be specified within a grammar using the
`@@comments` and `@@eol_comments` directives:

```ocaml
@@comments :: /\(\*.*?\*\)/
@@eol_comments :: /#.*?$/
```

Reserved Words and Keywords
---------------------------

Some languages must reserve the use of certain tokens as valid
identifiers because the tokens are used to mark particular constructs in
the language. Those reserved tokens are known as [Reserved Words] or
[Keywords][Reserved Words]

**Tatsu** provides support for preventing the use of [keywords][Reserved
Words] as identifiers though the `@@ keyword` directive,and the `@ name`
decorator.

A grammar may specify reserved tokens providing a list of them in one or
more `@@ keyword` directives:

```ocaml
@@keyword :: if endif
@@keyword :: else elseif
```

The `@ name` decorator checks that the result of a grammar rule does not
match a token defined as a [keyword][Reserved Words]:

```ocaml
@name
identifier = /(?!\d)\w+/ ;
```

There are situations in which a token is reserved only in a very
specific context. In those cases, a negative lookahead will prevent the
use of the token:

```ocaml
statements = {!'END' statement}+ ;
```

Semantic Actions
----------------

There are no constructs for semantic actions in **Tatsu** grammars. This
is on purpose, because semantic actions obscure the declarative nature
of grammars and provide for poor modularization from the
parser-execution perspective.

Semantic actions are defined in a class, and applied by passing an
object of the class to the `parse()` method of the parser as the
`semantics=` parameter. **Tatsu** will invoke the method that matches
the name of the grammar rule every time the rule parses. The argument to
the method will be the [AST][Abstract Syntax Tree] constructed from the
right-hand-side of the rule:

```python
class MySemantics(object):
    def some_rule_name(self, ast):
        return ''.join(ast)

    def _default(self, ast):
        pass
```

If there's no method matching the rule's name, **Tatsu** will try to
invoke a `_default()` method if it's defined:

```python
def _default(self, ast):
    ...
```

Nothing will happen if neither the per-rule method nor `_default()` are
defined.

The per-rule methods in classes implementing the semantics provide
enough opportunity to do rule post-processing operations, like
verifications (for inadequate use of keywords as identifiers), or
[AST][Abstract Syntax Tree] transformation:

```python
class MyLanguageSemantics(object):
    def identifier(self, ast):
        if my_lange_module.is_keyword(ast):
            raise FailedSemantics('"%s" is a keyword' % str(ast))
        return ast
```

For finer-grained control it is enough to declare more rules, as the
impact on the parsing times will be minimal.

If preprocessing is required at some point, it is enough to place
invocations of empty rules where appropriate:

```python
myrule = first_part preproc {second_part} ;

preproc = () ;
```

The abstract parser will honor as a semantic action a method declared
as:

```python
def preproc(self, ast):
    ...
```

Include Directive
-----------------

**Tatsu** grammars support file inclusion through the include directive:

```ocaml
#include :: "filename"
```

The resolution of the *filename* is relative to the directory/folder of
the source. Absolute paths and `../` navigations are honored.

The functionality required for implementing includes is available to all
**Tatsu**-generated parsers through the `Buffer` class; see the
`EBNFBuffer` class in the `tatsu.parser` module for an example.

Building Models
---------------

Naming elements in grammar rules makes the parser discard uninteresting
parts of the input, like punctuation, to produce an *Abstract Syntax
Tree* ([AST][Abstract Syntax Tree]) that reflects the semantic structure
of what was parsed. But an [AST][Abstract Syntax Tree] doesn't carry
information about the rule that generated it, so navigating the trees
may be difficult.

**Tatsu** defines the `tatsu.model.ModelBuilderSemantics` semantics
class which helps construct object models from abtract syntax trees:

```python
from tatsu.model import ModelBuilderSemantics

parser = MyParser(semantics=ModelBuilderSemantics())
```

Then you add the desired node type as first parameter to each grammar
rule:

```ocaml
addition::AddOperator = left:mulexpre '+' right:addition ;
```

`ModelBuilderSemantics` will synthesize a `class AddOperator(Node):` class and
use it to construct the node. The synthesized class will have one
attribute with the same name as the named elements in the rule.

You can also use [Python]'s built-in types as node types, and
`ModelBuilderSemantics` will do the right thing:

```ocaml
integer::int = /[0-9]+/ ;
```

`ModelBuilderSemantics` acts as any other semantics class, so its
default behavior can be overidden by defining a method to handle the
result of any particular grammar rule.

### Walking Models

The class `tatsu.model.NodeWalker` allows for the easy traversal
(*walk*) a model constructed with a `ModelBuilderSemantics` instance:

```python
from tatsu.model import NodeWalker

class MyNodeWalker(NodeWalker):

    def walk_AddOperator(self, node):
        left = self.walk(node.left)
        right = self.walk(node.right)

        print('ADDED', left, right)

model = MyParser(semantics=ModelBuilderSemantics()).parse(input)

walker = MyNodeWalker()
walker.walk(model)
```

When a method with a name like `walk_AddOperator()` is defined, it will
be called when a node of that type is *walked* (the *pythonic* version
of the class name may also be used for the *walk* method:
`walk_add_operator()`.

If a *walk* method for a node class is not found, then a method for the
class's bases is searched, so it is possible to write *catch-all*
methods such as:

```python
def walk_Node(self, node):
    print('Reached Node', node)

def walk_str(self, s):
    return s

def walk_object(self, o):
    raise Exception('Unexpected tyle %s walked', type(o).__name__)
```

Predeclared classes can be passed to `ModelBuilderSemantics` instances
through the `types=` parameter:

```python
from mymodel import AddOperator, MulOperator

semantics=ModelBuilderSemantics(types=[AddOperator, MulOperator])
```

`ModelBuilderSemantics` assumes nothing about `types=`, so any
constructor (a function, or a partial function) can be used.

### Model Class Hierarchies

It is possible to specify a a base class for generated model nodes:

```ocaml
additive
    =
    | addition
    | substraction
    ;

addition::AddOperator::Operator
    =
    left:mulexpre op:'+' right:additive
    ;

substraction::SubstractOperator::Operator
    =
    left:mulexpre op:'-' right:additive
    ;
```

**Tatsu** will generate the base class if it's not already known.

Base classes can be used as the target class in *walkers*, and in *code
generators*:

```python
class MyNodeWalker(NodeWalker):
    def walk_Operator(self, node):
        left = self.walk(node.left)
        right = self.walk(node.right)
        op = self.walk(node.op)

        print(type(node).__name__, op, left, right)


class Operator(ModelRenderer):
    template = '{left} {op} {right}'
```

Templates and Translation
-------------------------

**note**

:   As of **Tatsu** 3.2.0, code generation is separated from grammar
models through `tatsu.codegen.CodeGenerator` as to allow for code
generation targets different from [Python]. Still, the use of inline
templates and `rendering.Renderer` hasn't changed. See the *regex*
example for merged modeling and code generation.

**Tatsu** doesn't impose a way to create translators with it, but it
exposes the facilities it uses to generate the [Python] source code for
parsers.

Translation in **Tatsu** is *template-based*, but instead of defining or
using a complex templating engine (yet another language), it relies on
the simple but powerful `string.Formatter` of the [Python] standard
library. The templates are simple strings that, in **Tatsu**'s style,
are inlined with the code.

To generate a parser, **Tatsu** constructs an object model of the parsed
grammar. A `tatsu.codegen.CodeGenerator` instance matches model objects
to classes that descend from `tatsu.codegen.ModelRenderer` and implement
the translation and rendering using string templates. Templates are
left-trimmed on whitespace, like [Python] *doc-comments* are. This is an
example taken from **Tatsu**'s source code:

```python
class Lookahead(ModelRenderer):
    template = '''\
                with self._if():
                {exp:1::}\
                '''
```

Every *attribute* of the object that doesn't start with an underscore
(`_`) may be used as a template field, and fields can be added or
modified by overriding the `render_fields(fields)` method. Fields
themselves are *lazily rendered* before being expanded by the template,
so a field may be an instance of a `ModelRenderer` descendant.

The `rendering` module defines a `Formatter` enhanced to support the
rendering of items in an *iterable* one by one. The syntax to achieve
that is:

```python
    '''
    {fieldname:ind:sep:fmt}
    '''
```

All of `ind`, `sep`, and `fmt` are optional, but the three *colons* are
not. A field specified that way will be rendered using:

```python
indent(sep.join(fmt % render(v) for v in value), ind)
```

The extended format can also be used with non-iterables, in which case
the rendering will be:

```python
indent(fmt % render(value), ind)
```

The default multiplier for `ind` is `4`, but that can be overridden
using `n*m` (for example `3*1`) in the format.

**note**

:   Using a newline character (`\n`) as separator will interfere with
    left trimming and indentation of templates. To use a newline as
    separator, specify it as `\\n`, and the renderer will understand
    the intention.

Left Recursion
--------------

**Tatsu** provides experimental support for left recursion in [PEG]
grammars. The implementation of left recursion is ongoing; it does not
yet handle all cases. The algorithm used is [Warth et al]'s.

Sometimes, while debugging a grammar, it is useful to turn
left-recursion support on or off:

```python
parser = MyParser(
    text,
    left_recursion=True,
)
```

Left recursion can also be turned off from within the grammar using the
`@@left_recursion` directive:

```ocaml
@@left_recursion :: False
```

Examples
--------

### Tatsu

The file `etc/tatsu.ebnf` contains a grammar for the **Tatsu** grammar
language written in its own grammar language. It is used in the
*bootstrap* test suite to prove that **Tatsu** can generate a parser to
parse its own language, and the resulting parser is made the bootstrap
parser every time **Tatsu** is stable (see `tatsu/bootstrap.py` for the
generated parser).

**Tatsu** uses **Tatsu** to translate grammars into parsers, so it is a
good example of end-to-end translation.

### Regex

The project `examples/regexp` contains a regexp-to-EBNF translator and
parser generator. The project has no practical use, but it's a complete,
end-to-end example of how to implement a translator using **Tatsu**.


### Calc

The project `examples/calc` implements a calculator for simple expressions, and is written as a tutorial over most of the features provided by **Tatsu**.

### g2e

The project `examples/g2e` contains a [ANTLR] to **Tatsu**
grammar translator. The project is a good example of the use of models
and templates in translation. The program, `g2e.py` generates
the **Tatsu** grammar on standard output, but because the model used is
**Tatsu**'s own, the same code can be used to directly generate a parser
from an [ANTLR] grammar. Please take a look at the examples *README* to
know about limitations.

### Other open-source Examples

-   **Christian Ledermann** wrote [parsewkt] a parser for [Well-known
    text] ([WTK][Well-known text]) using **Tatsu**.
-   **Marcus Brinkmann** ([lambdafu]) wrote [smc.mw], a parser for a
    [MediaWiki]-style language.

License
-------

You may use **Tatsu** under the terms of the [BSD]-style license
described in the enclosed **[LICENSE.txt](LICENSE.txt)** file. *If your project
requires different licensing* please [email][Juancarlo Añez].

Contact and Updates
-------------------

For general Q&A, please use the `[tatsu]` tag on [StackOverflow].

To discuss **Tatsu** and to receive notifications about new releases,
please join the low-volume [Tatsu Forum] at *Google Groups*.

Credits
-------

The following must be mentioned as contributors of thoughts, ideas,
code, *and funding* to the **Tatsu** project:

-   **Niklaus Wirth** was the chief designer of the programming
    languages [Euler], [Algol W], [Pascal], [Modula], [Modula-2],
    [Oberon], and [Oberon-2]. In the last chapter of his 1976 book
    [Algorithms + Data Structures = Programs], [Wirth] creates a
    top-down, descent parser with recovery for the [Pascal]-like,
    [LL(1)] programming language [PL/0]. The structure of the program is
    that of a [PEG] parser, though the concept of [PEG] wasn't
    formalized until 2004.
-   **Bryan Ford** [introduced][] [PEG] (parsing expression grammars)
    in 2004.
-   Other parser generators like [PEG.js] by **David Majda** inspired
    the work in **Tatsu**.
-   **William Thompson** inspired the use of context managers with his
    [blog post] that I knew about through the invaluable [Python Weekly]
    newsletter, curated by **Rahul Chaudhary**
-   **Jeff Knupp** explains why **Tatsu**'s use of [exceptions] is
    sound, so I don't have to.
-   **Terence Parr** created [ANTLR], probably the most solid and
    professional parser generator out there. *Ter*, *ANTLR*, and the
    folks on the *ANLTR* forums helped me shape my ideas about
    **Tatsu**.
-   **JavaCC** (originally [Jack]) looks like an abandoned project. It
    was the first parser generator I used while teaching.
-   **Tatsu** is very fast. But dealing with millions of lines of legacy
    source code in a matter of minutes would be impossible without
    [PyPy], the work of **Armin Rigo** and the [PyPy team].
-   **Guido van Rossum** created and has lead the development of the
    [Python] programming environment for over a decade. A tool like
    **Tatsu**, at under six thousand lines of code, would not have been
    possible without [Python].
-   **Kota Mizushima** welcomed me to the [CSAIL at MIT][] [PEG and
    Packrat parsing mailing list], and immediately offered ideas and
    pointed me to documentation about the implementation of *cut* in
    modern parsers. The optimization of memoization information in
    **Tatsu** is thanks to one of his papers.
-   **My students** at [UCAB] inspired me to think about how
    grammar-based parser generation could be made more approachable.
-   **Gustavo Lau** was my professor of *Language Theory* at [USB], and
    he was kind enough to be my tutor in a thesis project on programming
    languages that was more than I could chew. My peers, and then
    teaching advisers **Alberto Torres**, and **Enzo Chiariotti** formed
    a team with **Gustavo** to challenge us with programming languages
    like *LATORTA* and term exams that went well into the eight hours.
    And, of course, there was also the *pirate patch* that should be
    worn on the left or right eye depending on the *LL* or
    *LR* challenge.
-   **Manuel Rey** led me through another, unfinished, thesis project
    that taught me about what languages (spoken languages in general,
    and programming languages in particular) are about. I learned why
    languages use [declensions], and why, although the underlying words
    are in [English], the structure of the programs we write is more
    like [Japanese].
-   [Marcus Brinkmann][lambdafu] has kindly submitted patches that have
    resolved obscure bugs in **Tatsu**'s implementation, and that have
    made the tool more user-friendly, specially for newcomers to parsing
    and translation.
-   [Robert Speer] cleaned up the nonsense in trying to have Unicode
    handling be compatible with 2.7.x and 3.x, and figured out the
    canonical way of honoring escape sequences in grammar tokens without
    throwing off the encoding.
-   [Basel Shishani] has been an incredibly throrough peer-reviewer of
    **Tatsu**.
-   [Paul Sargent] implemented [Warth et al]'s algorithm for supporting
    direct and indirect left recursion in [PEG] parsers.
-   [Kathryn Long] proposed better support for UNICODE in the treatment
    of whitespace and regular expressions (patterns) in general. Her
    other contributions have made **Tatsu** more congruent, and
    more user-friendly.
-   [David Röthlisberger] provided the definitive patch that allows the
    use of [Python] keywords as rule names.

Contributors
------------

The following, among others, have contributted to **Tatsu** with
features, bug fixes, or suggestions:

>   [basel-shishani](https://bitbucket.org/basel-shishani)
    ,
    [drothlis](https://bitbucket.org/drothlis)
    ,
    [franz_g](https://bitbucket.org/franz_g)
    ,
    [gapag](https://bitbucket.org/gapag)
    ,
    [gegenschall](https://bitbucket.org/gegenschall)
    ,
    [gkimbar](https://bitbucket.org/gkimbar)
    ,
    [jimon](https://bitbucket.org/jimon)
    ,
    [lambdafu](https://bitbucket.org/lambdafu)
    ,
    [leewz](https://bitbucket.org/leewz)
    ,
    [linkdd](https://bitbucket.org/linkdd)
    ,
    [nehz](https://bitbucket.org/nehz)
    ,
    [neumond](https://bitbucket.org/neumond)
    ,
    [pauls](https://bitbucket.org/pauls)
    ,
    [pgebhard](https://bitbucket.org/pgebhard)
    ,
    [r_speer](https://bitbucket.org/r_speer)
    ,
    [siemer](https://bitbucket.org/siemer)
    ,
    [sjbrownBitbucket](https://bitbucket.org/sjbrownBitbucket)
    ,
    [starkat](https://bitbucket.org/starkat)
    ,
    [tonico_strasser](https://bitbucket.org/tonico_strasser)
    ,
    [vinay.sajip](https://bitbucket.org/vinay.sajip)
    ,
    [vmuriart](https://bitbucket.org/vmuriart)

Changes
-------

See the [CHANGELOG] for details.

  [AST]: https://en.wikipedia.org/wiki/Abstract_syntax_tree
  [Dennis Ritchie]: http://en.wikipedia.org/wiki/Dennis_Ritchie
  [C]: http://en.wikipedia.org/wiki/C_language
  [Unix]: http://en.wikipedia.org/wiki/Unix
  [EBNF]: http://en.wikipedia.org/wiki/Ebnf
  [memoizing]: http://en.wikipedia.org/wiki/Memoization
  [Packrat]: http://bford.info/packrat/
  [PEG]: http://en.wikipedia.org/wiki/Parsing_expression_grammar
  [Python]: http://python.org
  [re]: https://docs.python.org/3.4/library/re.html
  [Perl]: http://www.perl.org/
  [context managers]: http://docs.python.org/2/library/contextlib.html
  [Cyclomatic complexity]: http://en.wikipedia.org/wiki/Cyclomatic_complexity
  [KLOC]: http://en.wikipedia.org/wiki/KLOC
  [regex]: https://pypi.python.org/pypi/regex
  [colorama]: https://pypi.python.org/pypi/colorama/
  [pygraphviz]: https://pypi.python.org/pypi/pygraphviz
  [Ruby]: http://www.ruby-lang.org/
  [Abstract Syntax Tree]: http://en.wikipedia.org/wiki/Abstract_syntax_tree
  [Semantic Graph]: http://en.wikipedia.org/wiki/Abstract_semantic_graph
  [VIM]: http://www.vim.org/
  [Sublime Text]: https://www.sublimetext.com
  [Reserved Words]: https://en.wikipedia.org/wiki/Reserved_word
  [ANTLR]: http://www.antlr.org/
  [parsewkt]: https://github.com/cleder/parsewkt
  [Well-known text]: http://en.wikipedia.org/wiki/Well-known_text
  [lambdafu]: http://blog.marcus-brinkmann.de/
  [smc.mw]: https://github.com/lambdafu/smc.mw
  [MediaWiki]: http://www.mediawiki.org/wiki/MediaWiki
  [Thomas Bragg]: mailto:tbragg95@gmail.com
  [Juancarlo Añez]: mailto:apalala@gmail.com
  [BSD]: http://en.wikipedia.org/wiki/BSD_licenses#2-clause_license_.28.22Simplified_BSD_License.22_or_.22FreeBSD_License.22.29
  [StackOverflow]: http://stackoverflow.com/tags/tatsu/info
  [Tatsu Forum]: https://groups.google.com/forum/?fromgroups#!forum/tatsu
  [Euler]: http://en.wikipedia.org/wiki/Euler_programming_language
  [Algol W]: http://en.wikipedia.org/wiki/Algol_W
  [Pascal]: http://en.wikipedia.org/wiki/Pascal_programming_language
  [Modula]: http://en.wikipedia.org/wiki/Modula
  [Modula-2]: http://en.wikipedia.org/wiki/Modula-2
  [Oberon]: http://en.wikipedia.org/wiki/Oberon_(programming_language)
  [Oberon-2]: http://en.wikipedia.org/wiki/Oberon-2
  [Algorithms + Data Structures = Programs]: http://www.amazon.com/Algorithms-Structures-Prentice-Hall-Automatic-Computation/dp/0130224189/
  [Wirth]: http://en.wikipedia.org/wiki/Niklaus_Wirth
  [LL(1)]: http://en.wikipedia.org/wiki/LL(1)
  [PL/0]: http://en.wikipedia.org/wiki/PL/0
  [introduced]: http://dl.acm.org/citation.cfm?id=964001.964011
  [PEG.js]: http://pegjs.majda.cz/
  [blog post]: http://dietbuddha.blogspot.com/2012/12/52python-encapsulating-exceptions-with.html
  [Python Weekly]: http://www.pythonweekly.com/
  [exceptions]: http://www.jeffknupp.com/blog/2013/02/06/write-cleaner-python-use-exceptions/
  [Jack]: http://en.wikipedia.org/wiki/Javacc
  [PyPy]: http://pypy.org/
  [PyPy team]: http://pypy.org/people.html
  [CSAIL at MIT]: http://www.csail.mit.edu/
  [PEG and Packrat parsing mailing list]: https://lists.csail.mit.edu/mailman/listinfo/peg
  [UCAB]: http://www.ucab.edu.ve/
  [USB]: http://www.usb.ve/
  [declensions]: http://en.wikipedia.org/wiki/Declension
  [English]: http://en.wikipedia.org/wiki/English_grammar
  [Japanese]: http://en.wikipedia.org/wiki/Japanese_grammar
  [Robert Speer]: https://bitbucket.org/r_speer
  [Basel Shishani]: https://bitbucket.org/basel-shishani
  [Paul Sargent]: https://bitbucket.org/PaulS/
  [Warth et al]: http://www.vpri.org/pdf/tr2007002_packrat.pdf
  [Kathryn Long]: https://bitbucket.org/starkat
  [David Röthlisberger]: https://bitbucket.org/drothlis/
  [franz_g]: https://bitbucket.org/Franz_G
  [gapag]: https://bitbucket.org/gapag/
  [gkimbar]: https://bitbucket.org/gkimbar/
  [jimon]: https://bitbucket.org/jimon/
  [linkdd]: https://bitbucket.org/linkdd/
  [nehz]: https://bitbucket.org/nehz/tatsu
  [neumond]: https://bitbucket.org/neumond/
  [pgebhard]: https://github.com/pgebhard?tab=repositories
  [siemer]: https://bitbucket.org/siemer/
  [vmuriart]: https://bitbucket.org/vmuriart/
  [gegenschall]: https://bitbucket.org/gegenschall/
  [tonico_strasser]: https://bitbucket.org/tonico_strasser/
  [vinay.sajip]: https://bitbucket.org/vinay.sajip/
  [brouhaha]: https://bitbucket.org/brouhaha/
  [sjbrownBitbucket]: https://bitbucket.org/sjbrownBitbucket/
  [CHANGELOG]: CHANGELOG.md

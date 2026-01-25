# {{TatSu}}

> *At least for the people who send me mail about a new language that they\'re designing, the general advice is: do it to learn about how to write a compiler. Don't have any expectations that anyone will use it, unless you hook up with some sort of organization in a position to push it hard. It's a lottery, and some can buy a lot of the tickets. There are plenty of beautiful languages (more beautiful than C) that didn't catch on. But someone does win the lottery, and doing a language at least teaches you something.*
>
> [Dennis Ritchie](http://en.wikipedia.org/wiki/Dennis_Ritchie) (1941-2011) Creator of the [C](http://en.wikipedia.org/wiki/C_language) programming language and of [Unix](http://en.wikipedia.org/wiki/Unix)

{{TatSu}} is a tool that takes grammars in a variation of 
[EBNF](http://en.wikipedia.org/wiki/Ebnf) as input, and outputs [memoizing](http://en.wikipedia.org/wiki/Memoization) ([Packrat](http://bford.info/packrat/)) [PEG](http://en.wikipedia.org/wiki/Parsing_expression_grammar) parsers in [Python](http://python.org).

Why use a [PEG](http://en.wikipedia.org/wiki/Parsing_expression_grammar) parser? Because [regular languages](https://en.wikipedia.org/wiki/Regular_language) (those parsable with Python's `re` package) *"cannot count"*. Any language with nested structures or with balancing of demarcatiors requires more than regular expressions to be parsed.

{{TatSu}} can compile a grammar stored in a string into a `tatsu.grammars.Grammar` object that can be used to parse any given input, much like the [re](https://docs.python.org/3.4/library/re.html) module does with regular expressions, or it can generate a [Python](http://python.org) module that implements the parser.

{{TatSu}} supports [left-recursive](https://en.wikipedia.org/wiki/Left_recursion) rules in [PEG](http://en.wikipedia.org/wiki/Parsing_expression_grammar) grammars, and it honors *left-associativity* in the resulting parse trees.

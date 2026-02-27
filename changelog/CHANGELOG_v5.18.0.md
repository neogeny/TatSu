[]: copyright (c) 2017-2026 juancarlo añez (apalala@gmail.com)
[]: spdx-license-identifier: bsd-4-clause

## Separation of State and Content

### Cursor

* `Tokenizer` classes provide implementations of the `Cursor` protocol 
 which holds the state (e.g. the position) of a parse, while the tokenizer
acts as the source of the input stream.

* All the bookkeeping for a parse with a `ParseContext` was moved to 
`StateStack` that only takes a `Cursor` as initialization parameter. It's
possible to have several parses on the same input at once because the
the state is separate from the `ParseContext` and the `Tokenizer`.

* Methods to represent grammar rules no longer have to be declared in 
a sublclass of `Parser`, but can be declared in any class. The convention
of naming the methods with a leading and a traling underscore was removed
so methods are now named like the grammar rules they represent. 

* When the name of grammar rules is the same as a reserved word in Python, 
the name is modified by appending one or more underscores to it.

* Methods that implement grammar rules now use a `ctx: Ctx` parameter
to caccess and pass the invocation `ParsContext`. `Ctx` is the protocol
that defines only the interface that methods for rules require to perform
a parse according to the input grammar.

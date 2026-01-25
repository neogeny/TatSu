# Left Recursion

{{TatSu}} supports direct and indirect left recursion in grammar rules using the the algorithm described by *Nicolas Laurent* and *Kim Mens* in their 2015 [paper](http://norswap.com/pubs/sle2015.pdf) *Parsing Expression Grammars Made Practical*.

The design and implementation of left recursion was done by [Vic Nightfall]() with research and help by [Nicolas Laurent]() on [Autumn](https://github.com/norswap/autumn), and research by [Philippe Sigaud]() on [PEGGED](https://github.com/PhilippeSigaud/Pegged/wiki/Left-Recursion).

Left recursive rules produce left-associative parse trees ([AST](http://en.wikipedia.org/wiki/Abstract_syntax_tree)), as most users would expect, *except if some of the rules involved recurse on the right (a pending topic)*.

Left recursion support is enabled by default in {{TatSu}}. To disable it for a particular grammar, use the `@@left_recursion` directive:

``` ocaml
@@left_recursion :: False
```

> [!WARNING]
> Not all left-recursive grammars that use the {{TatSu}} syntax are [PEG](http://en.wikipedia.org/wiki/Parsing_expression_grammar) (the same happens with right-recursive grammars). **The order of rules matters in PEG**.
>
> For right-recursive grammars the choices that parse the most input must come first. The same is true for left-recursive grammars.

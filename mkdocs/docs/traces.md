# Traces
:set wrap
{{atSu}}}} compiling and parsing actions have a `trace=` argument. The option is also {{end}}
available in `ParserConfig` and as `--trace` on the command line. For colorization to be enabled the [colorama](https://pypi.python.org/pypi/colorama/) library must be installed.
When used with the `colorize` option (defaults to `True`) ( `--color` on the command line), it 
produces a trace like the following, in which colors mean {{try}}try{{end}}, {{succeed}}succeed {{end}}, and {{fail}}fail{{end}}.

---
<code>
{{try}}↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙expression↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙expression↙expression↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{fail}}⟲ expression↙expression↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙expression↙expression↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{fail}}⟲ expression↙expression↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙term↙expression↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{fail}}⟲ term↙term↙expression↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{fail}}⟲ term↙term↙expression↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙factor↙term↙expression↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{fail}}≢'(' ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙number↙factor↙term↙expression↙start ~1:1{{end}}
<br/> {{console}}3 + 5 * ( 10 - 20 ){{end}}
<br/> {{succeed}}≡'3' /\d+/ ~1:2{{end}}
<br/> {{console}} + 5 * ( 10 - 20 ){{end}}
<br/> {{succeed}}≡number↙factor↙term↙expression↙start ~1:2{{end}}
<br/> {{console}} + 5 * ( 10 - 20 ){{end}}
<br/> {{succeed}}≡factor↙term↙expression↙start ~1:2{{end}}
<br/> {{console}} + 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙start ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{succeed}}≡term↙term↙expression↙start ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{fail}}≢'*' ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙start ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{succeed}}≡term↙term↙expression↙start ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{fail}}≢'/' ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙factor↙term↙expression↙start ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{fail}}≢'(' ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙number↙factor↙term↙expression↙start ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{fail}}≢'' /\d+/ ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{fail}}≢factor↙term↙expression↙start ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{succeed}}≡term↙expression↙start ~1:2{{end}}
<br/> {{console}} + 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙expression↙expression↙start ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{succeed}}≡expression↙expression↙start ~1:3{{end}}
<br/> {{console}}+ 5 * ( 10 - 20 ){{end}}
<br/> {{succeed}}≡'+' ~1:4{{end}}
<br/> {{console}} 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙term↙expression↙start ~1:4{{end}}
<br/> {{console}} 5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙start ~1:5{{end}}
<br/> {{console}}5 * ( 10 - 20 ){{end}}
<br/> {{fail}}⟲ term↙term↙expression↙start ~1:5{{end}}
<br/> {{console}}5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙start ~1:5{{end}}
<br/> {{console}}5 * ( 10 - 20 ){{end}}
<br/> {{fail}}⟲ term↙term↙expression↙start ~1:5{{end}}
<br/> {{console}}5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙factor↙term↙expression↙start ~1:5{{end}}
<br/> {{console}}5 * ( 10 - 20 ){{end}}
<br/> {{fail}}≢'(' ~1:5{{end}}
<br/> {{console}}5 * ( 10 - 20 ){{end}}
<br/> {{try}}↙number↙factor↙term↙expression↙start ~1:5{{end}}
<br/> {{console}}5 * ( 10 - 20 ){{end}}
<br/> {{succeed}}≡'5' /\d+/ ~1:6{{end}}
<br/> {{console}} * ( 10 - 20 ){{end}}
<br/> {{succeed}}≡number↙factor↙term↙expression↙start ~1:6{{end}}
<br/> {{console}} * ( 10 - 20 ){{end}}
<br/> {{succeed}}≡factor↙term↙expression↙start ~1:6{{end}}
<br/> {{console}} * ( 10 - 20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙start ~1:7{{end}}
<br/> {{console}}* ( 10 - 20 ){{end}}
<br/> {{succeed}}≡term↙term↙expression↙start ~1:7{{end}}
<br/> {{console}}* ( 10 - 20 ){{end}}
<br/> {{succeed}}≡'*' ~1:8{{end}}
<br/> {{console}} ( 10 - 20 ){{end}}
<br/> {{try}}↙factor↙term↙expression↙start ~1:8{{end}}
<br/> {{console}} ( 10 - 20 ){{end}}
<br/> {{succeed}}≡'(' ~1:10{{end}}
<br/> {{console}} 10 - 20 ){{end}}
<br/> {{try}}↙expression↙factor↙term↙expression↙start ~1:10{{end}}
<br/> {{console}} 10 - 20 ){{end}}
<br/> {{try}}↙expression↙expression↙factor↙term↙expression↙start ~1:11{{end}}
<br/> {{console}}10 - 20 ){{end}}
<br/> {{fail}}⟲ expression↙expression↙factor↙term↙expression↙start ~1:11{{end}}
<br/> {{console}}10 - 20 ){{end}}
<br/> {{try}}↙expression↙expression↙factor↙term↙expression↙start ~1:11{{end}}
<br/> {{console}}10 - 20 ){{end}}
<br/> {{fail}}⟲ expression↙expression↙factor↙term↙expression↙start ~1:11{{end}}
<br/> {{console}}10 - 20 ){{end}}
<br/> {{try}}↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}
<br/> {{console}}10 - 20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}
<br/> {{console}}10 - 20 ){{end}}
<br/> {{fail}}⟲ term↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}
<br/> {{console}}10 - 20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}
<br/> {{console}}10 - 20 ){{end}}
<br/> {{fail}}⟲ term↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}
<br/> {{console}}10 - 20 ){{end}}
<br/> {{try}}↙factor↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}
<br/> {{console}}10 - 20 ){{end}}
<br/> {{fail}}≢'(' ~1:11{{end}}
<br/> {{console}}10 - 20 ){{end}}
<br/> {{try}}↙number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}
<br/> {{console}}10 - 20 ){{end}}
<br/> {{succeed}}≡'10' /\d+/ ~1:13{{end}}
<br/> {{console}} - 20 ){{end}}
<br/> {{succeed}}≡number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:13{{end}}
<br/> {{console}} - 20 ){{end}}
<br/> {{succeed}}≡factor↙term↙expression↙factor↙term↙expression↙start ~1:13{{end}}
<br/> {{console}} - 20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{succeed}}≡term↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{fail}}≢'*' ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{succeed}}≡term↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{fail}}≢'/' ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{try}}↙factor↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{fail}}≢'(' ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{try}}↙number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{fail}}≢'' /\d+/ ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{fail}}≢factor↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{succeed}}≡term↙expression↙factor↙term↙expression↙start ~1:13{{end}}
<br/> {{console}} - 20 ){{end}}
<br/> {{try}}↙expression↙expression↙factor↙term↙expression↙start ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{succeed}}≡expression↙expression↙factor↙term↙expression↙start ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{fail}}≢'+' ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{try}}↙expression↙expression↙factor↙term↙expression↙start ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{succeed}}≡expression↙expression↙factor↙term↙expression↙start ~1:14{{end}}
<br/> {{console}}- 20 ){{end}}
<br/> {{succeed}}≡'-' ~1:15{{end}}
<br/> {{console}} 20 ){{end}}
<br/> {{try}}↙term↙expression↙factor↙term↙expression↙start ~1:15{{end}}
<br/> {{console}} 20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙factor↙term↙expression↙start ~1:16{{end}}
<br/> {{console}}20 ){{end}}
<br/> {{fail}}⟲ term↙term↙expression↙factor↙term↙expression↙start ~1:16{{end}}
<br/> {{console}}20 ){{end}}
<br/> {{try}}↙term↙term↙expression↙factor↙term↙expression↙start ~1:16{{end}}
<br/> {{console}}20 ){{end}}
<br/> {{fail}}⟲ term↙term↙expression↙factor↙term↙expression↙start ~1:16{{end}}
<br/> {{console}}20 ){{end}}
<br/> {{try}}↙factor↙term↙expression↙factor↙term↙expression↙start ~1:16{{end}}
<br/> {{console}}20 ){{end}}
<br/> {{fail}}≢'(' ~1:16{{end}}
<br/> {{console}}20 ){{end}}
<br/> {{try}}↙number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:16{{end}}
<br/> {{console}}20 ){{end}}
<br/> {{succeed}}≡'20' /\d+/ ~1:18{{end}}
<br/> {{console}} ){{end}}
<br/> {{succeed}}≡number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:18{{end}}
<br/> {{console}} ){{end}}
<br/> {{succeed}}≡factor↙term↙expression↙factor↙term↙expression↙start ~1:18{{end}}
<br/> {{console}} ){{end}}
<br/> {{try}}↙term↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{succeed}}≡term↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{fail}}≢'*' ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{try}}↙term↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{succeed}}≡term↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{fail}}≢'/' ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{try}}↙factor↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{fail}}≢'(' ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{try}}↙number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{fail}}≢'' /\d+/ ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{fail}}≢factor↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{succeed}}≡term↙expression↙factor↙term↙expression↙start ~1:18{{end}}
<br/> {{console}} ){{end}}
<br/> {{try}}↙expression↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{succeed}}≡expression↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{fail}}≢'+' ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{try}}↙expression↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{succeed}}≡expression↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{fail}}≢'-' ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{try}}↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{fail}}≢term↙expression↙factor↙term↙expression↙start ~1:19{{end}}
<br/> {{console}}){{end}}
<br/> {{succeed}}≡expression↙factor↙term↙expression↙start ~1:18{{end}}
<br/> {{console}} ){{end}}
<br/> {{succeed}}≡')'{{end}}
<br/> {{succeed}}≡factor↙term↙expression↙start{{end}}
<br/> {{try}}↙term↙term↙expression↙start{{end}}
<br/> {{succeed}}≡term↙term↙expression↙start{{end}}
<br/> {{fail}}≢'*'{{end}}
<br/> {{try}}↙term↙term↙expression↙start{{end}}
<br/> {{succeed}}≡term↙term↙expression↙start{{end}}
<br/> {{fail}}≢'/'{{end}}
<br/> {{try}}↙factor↙term↙expression↙start{{end}}
<br/> {{fail}}≢'('{{end}}
<br/> {{try}}↙number↙factor↙term↙expression↙start{{end}}
<br/> {{fail}}≢'' /\d+/{{end}}
<br/> {{fail}}≢factor↙term↙expression↙start{{end}}
<br/> {{succeed}}≡term↙expression↙start{{end}}
<br/> {{try}}↙expression↙expression↙start{{end}}
<br/> {{succeed}}≡expression↙expression↙start{{end}}
<br/> {{fail}}≢'+'{{end}}
<br/> {{try}}↙expression↙expression↙start{{end}}
<br/> {{succeed}}≡expression↙expression↙start{{end}}
<br/> {{fail}}≢'-'{{end}}
<br/> {{try}}↙term↙expression↙start{{end}}
<br/> {{fail}}≢term↙expression↙start{{end}}
<br/> {{succeed}}≡expression↙start{{end}}
<br/> {{succeed}}≡start{{end}}
</code>

---

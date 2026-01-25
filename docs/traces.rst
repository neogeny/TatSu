Traces
------
{% include "links.md" %}

|TatSu| compiling and parsing actions have a ``trace=`` argument. The option
is also available in ``ParserConfig`` and as ``--trace`` on the command line.
For colorization to be enabled the colorama_ library must be installed.

When used with the ``colorize`` option (defaults to ``True``)
( ``--color`` on the command line), it produces a trace like the following,
in which colors mean {{try}} `try`, :succeed:`suceed`, and :fail:`fail`.{{end}}



| {{try}} ↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{try}} ↙expression↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{try}} ↙expression↙expression↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{fail}} ⟲ expression↙expression↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{try}} ↙expression↙expression↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{fail}} ⟲ expression↙expression↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{try}} ↙term↙expression↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{try}} ↙term↙term↙expression↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{fail}} ⟲ term↙term↙expression↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{try}} ↙term↙term↙expression↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{fail}} ⟲ term↙term↙expression↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{try}} ↙factor↙term↙expression↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{fail}} ≢'(' ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{try}} ↙number↙factor↙term↙expression↙start ~1:1{{end}}

| {{console}} \3 + 5 * ( 10 - 20 ){{end}}

| {{succeed}} ≡'3' /\d+/ ~1:2{{end}}

| {{console}} \ + 5 * ( 10 - 20 ){{end}}

| {{succeed}} ≡number↙factor↙term↙expression↙start ~1:2{{end}}

| {{console}} \ + 5 * ( 10 - 20 ){{end}}

| {{succeed}} ≡factor↙term↙expression↙start ~1:2{{end}}

| {{console}} \ + 5 * ( 10 - 20 ){{end}}

| {{try}} ↙term↙term↙expression↙start ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{succeed}} ≡term↙term↙expression↙start ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{fail}} ≢'*' ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{try}} ↙term↙term↙expression↙start ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{succeed}} ≡term↙term↙expression↙start ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{fail}} ≢'/' ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{try}} ↙factor↙term↙expression↙start ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{fail}} ≢'(' ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{try}} ↙number↙factor↙term↙expression↙start ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{fail}} ≢'' /\d+/ ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{fail}} ≢factor↙term↙expression↙start ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{succeed}} ≡term↙expression↙start ~1:2{{end}}

| {{console}} \ + 5 * ( 10 - 20 ){{end}}

| {{try}} ↙expression↙expression↙start ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{succeed}} ≡expression↙expression↙start ~1:3{{end}}

| {{console}} \+ 5 * ( 10 - 20 ){{end}}

| {{succeed}} ≡'+' ~1:4{{end}}

| {{console}} \ 5 * ( 10 - 20 ){{end}}

| {{try}} ↙term↙expression↙start ~1:4{{end}}

| {{console}} \ 5 * ( 10 - 20 ){{end}}

| {{try}} ↙term↙term↙expression↙start ~1:5{{end}}

| {{console}} \5 * ( 10 - 20 ){{end}}

| {{fail}} ⟲ term↙term↙expression↙start ~1:5{{end}}

| {{console}} \5 * ( 10 - 20 ){{end}}

| {{try}} ↙term↙term↙expression↙start ~1:5{{end}}

| {{console}} \5 * ( 10 - 20 ){{end}}

| {{fail}} ⟲ term↙term↙expression↙start ~1:5{{end}}

| {{console}} \5 * ( 10 - 20 ){{end}}

| {{try}} ↙factor↙term↙expression↙start ~1:5{{end}}

| {{console}} \5 * ( 10 - 20 ){{end}}

| {{fail}} ≢'(' ~1:5{{end}}

| {{console}} \5 * ( 10 - 20 ){{end}}

| {{try}} ↙number↙factor↙term↙expression↙start ~1:5{{end}}

| {{console}} \5 * ( 10 - 20 ){{end}}

| {{succeed}} ≡'5' /\d+/ ~1:6{{end}}

| {{console}} \ * ( 10 - 20 ){{end}}

| {{succeed}} ≡number↙factor↙term↙expression↙start ~1:6{{end}}

| {{console}} \ * ( 10 - 20 ){{end}}

| {{succeed}} ≡factor↙term↙expression↙start ~1:6{{end}}

| {{console}} \ * ( 10 - 20 ){{end}}

| {{try}} ↙term↙term↙expression↙start ~1:7{{end}}

| {{console}} \* ( 10 - 20 ){{end}}

| {{succeed}} ≡term↙term↙expression↙start ~1:7{{end}}

| {{console}} \* ( 10 - 20 ){{end}}

| {{succeed}} ≡'*' ~1:8{{end}}

| {{console}} \ ( 10 - 20 ){{end}}

| {{try}} ↙factor↙term↙expression↙start ~1:8{{end}}

| {{console}} \ ( 10 - 20 ){{end}}

| {{succeed}} ≡'(' ~1:10{{end}}

| {{console}} \ 10 - 20 ){{end}}

| {{try}} ↙expression↙factor↙term↙expression↙start ~1:10{{end}}

| {{console}} \ 10 - 20 ){{end}}

| {{try}} ↙expression↙expression↙factor↙term↙expression↙start ~1:11{{end}}

| {{console}} \10 - 20 ){{end}}

| {{fail}} ⟲ expression↙expression↙factor↙term↙expression↙start ~1:11{{end}}

| {{console}} \10 - 20 ){{end}}

| {{try}} ↙expression↙expression↙factor↙term↙expression↙start ~1:11{{end}}

| {{console}} \10 - 20 ){{end}}

| {{fail}} ⟲ expression↙expression↙factor↙term↙expression↙start ~1:11{{end}}

| {{console}} \10 - 20 ){{end}}

| {{try}} ↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}

| {{console}} \10 - 20 ){{end}}

| {{try}} ↙term↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}

| {{console}} \10 - 20 ){{end}}

| {{fail}} ⟲ term↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}

| {{console}} \10 - 20 ){{end}}

| {{try}} ↙term↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}

| {{console}} \10 - 20 ){{end}}

| {{fail}} ⟲ term↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}

| {{console}} \10 - 20 ){{end}}

| {{try}} ↙factor↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}

| {{console}} \10 - 20 ){{end}}

| {{fail}} ≢'(' ~1:11{{end}}

| {{console}} \10 - 20 ){{end}}

| {{try}} ↙number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:11{{end}}

| {{console}} \10 - 20 ){{end}}

| {{succeed}} ≡'10' /\d+/ ~1:13{{end}}

| {{console}} \ - 20 ){{end}}

| {{succeed}} ≡number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:13{{end}}

| {{console}} \ - 20 ){{end}}

| {{succeed}} ≡factor↙term↙expression↙factor↙term↙expression↙start ~1:13{{end}}

| {{console}} \ - 20 ){{end}}

| {{try}} ↙term↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{succeed}} ≡term↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{fail}} ≢'*' ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{try}} ↙term↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{succeed}} ≡term↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{fail}} ≢'/' ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{try}} ↙factor↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{fail}} ≢'(' ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{try}} ↙number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{fail}} ≢'' /\d+/ ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{fail}} ≢factor↙term↙expression↙factor↙term↙expression↙start ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{succeed}} ≡term↙expression↙factor↙term↙expression↙start ~1:13{{end}}

| {{console}} \ - 20 ){{end}}

| {{try}} ↙expression↙expression↙factor↙term↙expression↙start ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{succeed}} ≡expression↙expression↙factor↙term↙expression↙start ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{fail}} ≢'+' ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{try}} ↙expression↙expression↙factor↙term↙expression↙start ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{succeed}} ≡expression↙expression↙factor↙term↙expression↙start ~1:14{{end}}

| {{console}} \- 20 ){{end}}

| {{succeed}} ≡'-' ~1:15{{end}}

| {{console}} \ 20 ){{end}}

| {{try}} ↙term↙expression↙factor↙term↙expression↙start ~1:15{{end}}

| {{console}} \ 20 ){{end}}

| {{try}} ↙term↙term↙expression↙factor↙term↙expression↙start ~1:16{{end}}

| {{console}} \20 ){{end}}

| {{fail}} ⟲ term↙term↙expression↙factor↙term↙expression↙start ~1:16{{end}}

| {{console}} \20 ){{end}}

| {{try}} ↙term↙term↙expression↙factor↙term↙expression↙start ~1:16{{end}}

| {{console}} \20 ){{end}}

| {{fail}} ⟲ term↙term↙expression↙factor↙term↙expression↙start ~1:16{{end}}

| {{console}} \20 ){{end}}

| {{try}} ↙factor↙term↙expression↙factor↙term↙expression↙start ~1:16{{end}}

| {{console}} \20 ){{end}}

| {{fail}} ≢'(' ~1:16{{end}}

| {{console}} \20 ){{end}}

| {{try}} ↙number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:16{{end}}

| {{console}} \20 ){{end}}

| {{succeed}} ≡'20' /\d+/ ~1:18{{end}}

| {{console}} \ ){{end}}

| {{succeed}} ≡number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:18{{end}}

| {{console}} \ ){{end}}

| {{succeed}} ≡factor↙term↙expression↙factor↙term↙expression↙start ~1:18{{end}}

| {{console}} \ ){{end}}

| {{try}} ↙term↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{succeed}} ≡term↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{fail}} ≢'*' ~1:19{{end}}

| {{console}} \){{end}}

| {{try}} ↙term↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{succeed}} ≡term↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{fail}} ≢'/' ~1:19{{end}}

| {{console}} \){{end}}

| {{try}} ↙factor↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{fail}} ≢'(' ~1:19{{end}}

| {{console}} \){{end}}

| {{try}} ↙number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{fail}} ≢'' /\d+/ ~1:19{{end}}

| {{console}} \){{end}}

| {{fail}} ≢factor↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{succeed}} ≡term↙expression↙factor↙term↙expression↙start ~1:18{{end}}

| {{console}} \ ){{end}}

| {{try}} ↙expression↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{succeed}} ≡expression↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{fail}} ≢'+' ~1:19{{end}}

| {{console}} \){{end}}

| {{try}} ↙expression↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{succeed}} ≡expression↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{fail}} ≢'-' ~1:19{{end}}

| {{console}} \){{end}}

| {{try}} ↙term↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{fail}} ≢term↙expression↙factor↙term↙expression↙start ~1:19{{end}}

| {{console}} \){{end}}

| {{succeed}} ≡expression↙factor↙term↙expression↙start ~1:18{{end}}

| {{console}} \ ){{end}}

| {{succeed}} ≡')'{{end}}

| {{succeed}} ≡factor↙term↙expression↙start{{end}}

| {{try}} ↙term↙term↙expression↙start{{end}}

| {{succeed}} ≡term↙term↙expression↙start{{end}}

| {{fail}} ≢'*'{{end}}

| {{try}} ↙term↙term↙expression↙start{{end}}

| {{succeed}} ≡term↙term↙expression↙start{{end}}

| {{fail}} ≢'/'{{end}}

| {{try}} ↙factor↙term↙expression↙start{{end}}

| {{fail}} ≢'('{{end}}

| {{try}} ↙number↙factor↙term↙expression↙start{{end}}

| {{fail}} ≢'' /\d+/{{end}}

| {{fail}} ≢factor↙term↙expression↙start{{end}}

| {{succeed}} ≡term↙expression↙start{{end}}

| {{try}} ↙expression↙expression↙start{{end}}

| {{succeed}} ≡expression↙expression↙start{{end}}

| {{fail}} ≢'+'{{end}}

| {{try}} ↙expression↙expression↙start{{end}}

| {{succeed}} ≡expression↙expression↙start{{end}}

| {{fail}} ≢'-'{{end}}

| {{try}} ↙term↙expression↙start{{end}}

| {{fail}} ≢term↙expression↙start{{end}}

| {{succeed}} ≡expression↙start{{end}}

| {{succeed}} ≡start{{end}}



----

..

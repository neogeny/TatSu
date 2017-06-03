.. include:: links.rst
.. include:: roles.rst


Traces
------

|TatSu| compiling and parsing actions have a ``trace=`` argument ( ``--trace`` on the command line). When used with the ``colorize=`` option ( ``--color`` on the command line), it produces trace like the following, in which colors mean :try:`try`, :succeed:`suceed`, and :fail:`fail`.


| :try:`↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :try:`↙expression↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :try:`↙expression↙expression↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :fail:`⟲ expression↙expression↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :try:`↙expression↙expression↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :fail:`⟲ expression↙expression↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :try:`↙term↙expression↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :try:`↙term↙term↙expression↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :fail:`⟲ term↙term↙expression↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :try:`↙term↙term↙expression↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :fail:`⟲ term↙term↙expression↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :try:`↙factor↙term↙expression↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :fail:`≢'(' ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :try:`↙number↙factor↙term↙expression↙start ~1:1`
| :console:`\3 + 5 * ( 10 - 20 )`
| :succeed:`≡'3' /\d+/ ~1:2`
| :console:`\ + 5 * ( 10 - 20 )`
| :succeed:`≡number↙factor↙term↙expression↙start ~1:2`
| :console:`\ + 5 * ( 10 - 20 )`
| :succeed:`≡factor↙term↙expression↙start ~1:2`
| :console:`\ + 5 * ( 10 - 20 )`
| :try:`↙term↙term↙expression↙start ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :succeed:`≡term↙term↙expression↙start ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :fail:`≢'*' ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :try:`↙term↙term↙expression↙start ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :succeed:`≡term↙term↙expression↙start ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :fail:`≢'/' ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :try:`↙factor↙term↙expression↙start ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :fail:`≢'(' ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :try:`↙number↙factor↙term↙expression↙start ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :fail:`≢'' /\d+/ ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :fail:`≢factor↙term↙expression↙start ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :succeed:`≡term↙expression↙start ~1:2`
| :console:`\ + 5 * ( 10 - 20 )`
| :try:`↙expression↙expression↙start ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :succeed:`≡expression↙expression↙start ~1:3`
| :console:`\+ 5 * ( 10 - 20 )`
| :succeed:`≡'+' ~1:4`
| :console:`\ 5 * ( 10 - 20 )`
| :try:`↙term↙expression↙start ~1:4`
| :console:`\ 5 * ( 10 - 20 )`
| :try:`↙term↙term↙expression↙start ~1:5`
| :console:`\5 * ( 10 - 20 )`
| :fail:`⟲ term↙term↙expression↙start ~1:5`
| :console:`\5 * ( 10 - 20 )`
| :try:`↙term↙term↙expression↙start ~1:5`
| :console:`\5 * ( 10 - 20 )`
| :fail:`⟲ term↙term↙expression↙start ~1:5`
| :console:`\5 * ( 10 - 20 )`
| :try:`↙factor↙term↙expression↙start ~1:5`
| :console:`\5 * ( 10 - 20 )`
| :fail:`≢'(' ~1:5`
| :console:`\5 * ( 10 - 20 )`
| :try:`↙number↙factor↙term↙expression↙start ~1:5`
| :console:`\5 * ( 10 - 20 )`
| :succeed:`≡'5' /\d+/ ~1:6`
| :console:`\ * ( 10 - 20 )`
| :succeed:`≡number↙factor↙term↙expression↙start ~1:6`
| :console:`\ * ( 10 - 20 )`
| :succeed:`≡factor↙term↙expression↙start ~1:6`
| :console:`\ * ( 10 - 20 )`
| :try:`↙term↙term↙expression↙start ~1:7`
| :console:`\* ( 10 - 20 )`
| :succeed:`≡term↙term↙expression↙start ~1:7`
| :console:`\* ( 10 - 20 )`
| :succeed:`≡'*' ~1:8`
| :console:`\ ( 10 - 20 )`
| :try:`↙factor↙term↙expression↙start ~1:8`
| :console:`\ ( 10 - 20 )`
| :succeed:`≡'(' ~1:10`
| :console:`\ 10 - 20 )`
| :try:`↙expression↙factor↙term↙expression↙start ~1:10`
| :console:`\ 10 - 20 )`
| :try:`↙expression↙expression↙factor↙term↙expression↙start ~1:11`
| :console:`\10 - 20 )`
| :fail:`⟲ expression↙expression↙factor↙term↙expression↙start ~1:11`
| :console:`\10 - 20 )`
| :try:`↙expression↙expression↙factor↙term↙expression↙start ~1:11`
| :console:`\10 - 20 )`
| :fail:`⟲ expression↙expression↙factor↙term↙expression↙start ~1:11`
| :console:`\10 - 20 )`
| :try:`↙term↙expression↙factor↙term↙expression↙start ~1:11`
| :console:`\10 - 20 )`
| :try:`↙term↙term↙expression↙factor↙term↙expression↙start ~1:11`
| :console:`\10 - 20 )`
| :fail:`⟲ term↙term↙expression↙factor↙term↙expression↙start ~1:11`
| :console:`\10 - 20 )`
| :try:`↙term↙term↙expression↙factor↙term↙expression↙start ~1:11`
| :console:`\10 - 20 )`
| :fail:`⟲ term↙term↙expression↙factor↙term↙expression↙start ~1:11`
| :console:`\10 - 20 )`
| :try:`↙factor↙term↙expression↙factor↙term↙expression↙start ~1:11`
| :console:`\10 - 20 )`
| :fail:`≢'(' ~1:11`
| :console:`\10 - 20 )`
| :try:`↙number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:11`
| :console:`\10 - 20 )`
| :succeed:`≡'10' /\d+/ ~1:13`
| :console:`\ - 20 )`
| :succeed:`≡number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:13`
| :console:`\ - 20 )`
| :succeed:`≡factor↙term↙expression↙factor↙term↙expression↙start ~1:13`
| :console:`\ - 20 )`
| :try:`↙term↙term↙expression↙factor↙term↙expression↙start ~1:14`
| :console:`\- 20 )`
| :succeed:`≡term↙term↙expression↙factor↙term↙expression↙start ~1:14`
| :console:`\- 20 )`
| :fail:`≢'*' ~1:14`
| :console:`\- 20 )`
| :try:`↙term↙term↙expression↙factor↙term↙expression↙start ~1:14`
| :console:`\- 20 )`
| :succeed:`≡term↙term↙expression↙factor↙term↙expression↙start ~1:14`
| :console:`\- 20 )`
| :fail:`≢'/' ~1:14`
| :console:`\- 20 )`
| :try:`↙factor↙term↙expression↙factor↙term↙expression↙start ~1:14`
| :console:`\- 20 )`
| :fail:`≢'(' ~1:14`
| :console:`\- 20 )`
| :try:`↙number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:14`
| :console:`\- 20 )`
| :fail:`≢'' /\d+/ ~1:14`
| :console:`\- 20 )`
| :fail:`≢factor↙term↙expression↙factor↙term↙expression↙start ~1:14`
| :console:`\- 20 )`
| :succeed:`≡term↙expression↙factor↙term↙expression↙start ~1:13`
| :console:`\ - 20 )`
| :try:`↙expression↙expression↙factor↙term↙expression↙start ~1:14`
| :console:`\- 20 )`
| :succeed:`≡expression↙expression↙factor↙term↙expression↙start ~1:14`
| :console:`\- 20 )`
| :fail:`≢'+' ~1:14`
| :console:`\- 20 )`
| :try:`↙expression↙expression↙factor↙term↙expression↙start ~1:14`
| :console:`\- 20 )`
| :succeed:`≡expression↙expression↙factor↙term↙expression↙start ~1:14`
| :console:`\- 20 )`
| :succeed:`≡'-' ~1:15`
| :console:`\ 20 )`
| :try:`↙term↙expression↙factor↙term↙expression↙start ~1:15`
| :console:`\ 20 )`
| :try:`↙term↙term↙expression↙factor↙term↙expression↙start ~1:16`
| :console:`\20 )`
| :fail:`⟲ term↙term↙expression↙factor↙term↙expression↙start ~1:16`
| :console:`\20 )`
| :try:`↙term↙term↙expression↙factor↙term↙expression↙start ~1:16`
| :console:`\20 )`
| :fail:`⟲ term↙term↙expression↙factor↙term↙expression↙start ~1:16`
| :console:`\20 )`
| :try:`↙factor↙term↙expression↙factor↙term↙expression↙start ~1:16`
| :console:`\20 )`
| :fail:`≢'(' ~1:16`
| :console:`\20 )`
| :try:`↙number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:16`
| :console:`\20 )`
| :succeed:`≡'20' /\d+/ ~1:18`
| :console:`\ )`
| :succeed:`≡number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:18`
| :console:`\ )`
| :succeed:`≡factor↙term↙expression↙factor↙term↙expression↙start ~1:18`
| :console:`\ )`
| :try:`↙term↙term↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :succeed:`≡term↙term↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :fail:`≢'*' ~1:19`
| :console:`\)`
| :try:`↙term↙term↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :succeed:`≡term↙term↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :fail:`≢'/' ~1:19`
| :console:`\)`
| :try:`↙factor↙term↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :fail:`≢'(' ~1:19`
| :console:`\)`
| :try:`↙number↙factor↙term↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :fail:`≢'' /\d+/ ~1:19`
| :console:`\)`
| :fail:`≢factor↙term↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :succeed:`≡term↙expression↙factor↙term↙expression↙start ~1:18`
| :console:`\ )`
| :try:`↙expression↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :succeed:`≡expression↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :fail:`≢'+' ~1:19`
| :console:`\)`
| :try:`↙expression↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :succeed:`≡expression↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :fail:`≢'-' ~1:19`
| :console:`\)`
| :try:`↙term↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :fail:`≢term↙expression↙factor↙term↙expression↙start ~1:19`
| :console:`\)`
| :succeed:`≡expression↙factor↙term↙expression↙start ~1:18`
| :console:`\ )`
| :succeed:`≡')'`
| :succeed:`≡factor↙term↙expression↙start`
| :try:`↙term↙term↙expression↙start`
| :succeed:`≡term↙term↙expression↙start`
| :fail:`≢'*'`
| :try:`↙term↙term↙expression↙start`
| :succeed:`≡term↙term↙expression↙start`
| :fail:`≢'/'`
| :try:`↙factor↙term↙expression↙start`
| :fail:`≢'('`
| :try:`↙number↙factor↙term↙expression↙start`
| :fail:`≢'' /\d+/`
| :fail:`≢factor↙term↙expression↙start`
| :succeed:`≡term↙expression↙start`
| :try:`↙expression↙expression↙start`
| :succeed:`≡expression↙expression↙start`
| :fail:`≢'+'`
| :try:`↙expression↙expression↙start`
| :succeed:`≡expression↙expression↙start`
| :fail:`≢'-'`
| :try:`↙term↙expression↙start`
| :fail:`≢term↙expression↙start`
| :succeed:`≡expression↙start`
| :succeed:`≡start`


----

..

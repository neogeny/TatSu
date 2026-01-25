# Traces

{{TatSu}} compiling and parsing actions have a `trace=` argument. The option is also available in `ParserConfig` and as `--trace` on the command line. For colorization to be enabled the [colorama](https://pypi.python.org/pypi/colorama/) library must be installed.

When used with the `colorize` option (defaults to `True`) ( `--color` on the command line), it produces a trace like the following, in which colors mean [try]{.try}, [suceed]{.succeed}, and [fail]{.fail}.

[↙start \~1:1]{.try}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[↙expression↙start \~1:1]{.try}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[↙expression↙expression↙start \~1:1]{.try}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[⟲ expression↙expression↙start \~1:1]{.fail}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[↙expression↙expression↙start \~1:1]{.try}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[⟲ expression↙expression↙start \~1:1]{.fail}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[↙term↙expression↙start \~1:1]{.try}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[↙term↙term↙expression↙start \~1:1]{.try}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[⟲ term↙term↙expression↙start \~1:1]{.fail}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[↙term↙term↙expression↙start \~1:1]{.try}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[⟲ term↙term↙expression↙start \~1:1]{.fail}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[↙factor↙term↙expression↙start \~1:1]{.try}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[≢\'(\' \~1:1]{.fail}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[↙number↙factor↙term↙expression↙start \~1:1]{.try}  
[3 + 5 \* ( 10 - 20 )]{.console}  
[≡\'3\' /d+/ \~1:2]{.succeed}  
[+ 5 \* ( 10 - 20 )]{.console}  
[≡number↙factor↙term↙expression↙start \~1:2]{.succeed}  
[+ 5 \* ( 10 - 20 )]{.console}  
[≡factor↙term↙expression↙start \~1:2]{.succeed}  
[+ 5 \* ( 10 - 20 )]{.console}  
[↙term↙term↙expression↙start \~1:3]{.try}  
[+ 5 \* ( 10 - 20 )]{.console}  
[≡term↙term↙expression↙start \~1:3]{.succeed}  
[+ 5 \* ( 10 - 20 )]{.console}  
[≢\'\*\' \~1:3]{.fail}  
[+ 5 \* ( 10 - 20 )]{.console}  
[↙term↙term↙expression↙start \~1:3]{.try}  
[+ 5 \* ( 10 - 20 )]{.console}  
[≡term↙term↙expression↙start \~1:3]{.succeed}  
[+ 5 \* ( 10 - 20 )]{.console}  
[≢\'/\' \~1:3]{.fail}  
[+ 5 \* ( 10 - 20 )]{.console}  
[↙factor↙term↙expression↙start \~1:3]{.try}  
[+ 5 \* ( 10 - 20 )]{.console}  
[≢\'(\' \~1:3]{.fail}  
[+ 5 \* ( 10 - 20 )]{.console}  
[↙number↙factor↙term↙expression↙start \~1:3]{.try}  
[+ 5 \* ( 10 - 20 )]{.console}  
[≢\'\' /d+/ \~1:3]{.fail}  
[+ 5 \* ( 10 - 20 )]{.console}  
[≢factor↙term↙expression↙start \~1:3]{.fail}  
[+ 5 \* ( 10 - 20 )]{.console}  
[≡term↙expression↙start \~1:2]{.succeed}  
[+ 5 \* ( 10 - 20 )]{.console}  
[↙expression↙expression↙start \~1:3]{.try}  
[+ 5 \* ( 10 - 20 )]{.console}  
[≡expression↙expression↙start \~1:3]{.succeed}  
[+ 5 \* ( 10 - 20 )]{.console}  
[≡\'+\' \~1:4]{.succeed}  
[5 \* ( 10 - 20 )]{.console}  
[↙term↙expression↙start \~1:4]{.try}  
[5 \* ( 10 - 20 )]{.console}  
[↙term↙term↙expression↙start \~1:5]{.try}  
[5 \* ( 10 - 20 )]{.console}  
[⟲ term↙term↙expression↙start \~1:5]{.fail}  
[5 \* ( 10 - 20 )]{.console}  
[↙term↙term↙expression↙start \~1:5]{.try}  
[5 \* ( 10 - 20 )]{.console}  
[⟲ term↙term↙expression↙start \~1:5]{.fail}  
[5 \* ( 10 - 20 )]{.console}  
[↙factor↙term↙expression↙start \~1:5]{.try}  
[5 \* ( 10 - 20 )]{.console}  
[≢\'(\' \~1:5]{.fail}  
[5 \* ( 10 - 20 )]{.console}  
[↙number↙factor↙term↙expression↙start \~1:5]{.try}  
[5 \* ( 10 - 20 )]{.console}  
[≡\'5\' /d+/ \~1:6]{.succeed}  
[\* ( 10 - 20 )]{.console}  
[≡number↙factor↙term↙expression↙start \~1:6]{.succeed}  
[\* ( 10 - 20 )]{.console}  
[≡factor↙term↙expression↙start \~1:6]{.succeed}  
[\* ( 10 - 20 )]{.console}  
[↙term↙term↙expression↙start \~1:7]{.try}  
[\* ( 10 - 20 )]{.console}  
[≡term↙term↙expression↙start \~1:7]{.succeed}  
[\* ( 10 - 20 )]{.console}  
[≡\'\*\' \~1:8]{.succeed}  
[( 10 - 20 )]{.console}  
[↙factor↙term↙expression↙start \~1:8]{.try}  
[( 10 - 20 )]{.console}  
[≡\'(\' \~1:10]{.succeed}  
[10 - 20 )]{.console}  
[↙expression↙factor↙term↙expression↙start \~1:10]{.try}  
[10 - 20 )]{.console}  
[↙expression↙expression↙factor↙term↙expression↙start \~1:11]{.try}  
[10 - 20 )]{.console}  
[⟲ expression↙expression↙factor↙term↙expression↙start \~1:11]{.fail}  
[10 - 20 )]{.console}  
[↙expression↙expression↙factor↙term↙expression↙start \~1:11]{.try}  
[10 - 20 )]{.console}  
[⟲ expression↙expression↙factor↙term↙expression↙start \~1:11]{.fail}  
[10 - 20 )]{.console}  
[↙term↙expression↙factor↙term↙expression↙start \~1:11]{.try}  
[10 - 20 )]{.console}  
[↙term↙term↙expression↙factor↙term↙expression↙start \~1:11]{.try}  
[10 - 20 )]{.console}  
[⟲ term↙term↙expression↙factor↙term↙expression↙start \~1:11]{.fail}  
[10 - 20 )]{.console}  
[↙term↙term↙expression↙factor↙term↙expression↙start \~1:11]{.try}  
[10 - 20 )]{.console}  
[⟲ term↙term↙expression↙factor↙term↙expression↙start \~1:11]{.fail}  
[10 - 20 )]{.console}  
[↙factor↙term↙expression↙factor↙term↙expression↙start \~1:11]{.try}  
[10 - 20 )]{.console}  
[≢\'(\' \~1:11]{.fail}  
[10 - 20 )]{.console}  
[↙number↙factor↙term↙expression↙factor↙term↙expression↙start \~1:11]{.try}  
[10 - 20 )]{.console}  
[≡\'10\' /d+/ \~1:13]{.succeed}  
[- 20 )]{.console}  
[≡number↙factor↙term↙expression↙factor↙term↙expression↙start \~1:13]{.succeed}  
[- 20 )]{.console}  
[≡factor↙term↙expression↙factor↙term↙expression↙start \~1:13]{.succeed}  
[- 20 )]{.console}  
[↙term↙term↙expression↙factor↙term↙expression↙start \~1:14]{.try}  
[- 20 )]{.console}  
[≡term↙term↙expression↙factor↙term↙expression↙start \~1:14]{.succeed}  
[- 20 )]{.console}  
[≢\'\*\' \~1:14]{.fail}  
[- 20 )]{.console}  
[↙term↙term↙expression↙factor↙term↙expression↙start \~1:14]{.try}  
[- 20 )]{.console}  
[≡term↙term↙expression↙factor↙term↙expression↙start \~1:14]{.succeed}  
[- 20 )]{.console}  
[≢\'/\' \~1:14]{.fail}  
[- 20 )]{.console}  
[↙factor↙term↙expression↙factor↙term↙expression↙start \~1:14]{.try}  
[- 20 )]{.console}  
[≢\'(\' \~1:14]{.fail}  
[- 20 )]{.console}  
[↙number↙factor↙term↙expression↙factor↙term↙expression↙start \~1:14]{.try}  
[- 20 )]{.console}  
[≢\'\' /d+/ \~1:14]{.fail}  
[- 20 )]{.console}  
[≢factor↙term↙expression↙factor↙term↙expression↙start \~1:14]{.fail}  
[- 20 )]{.console}  
[≡term↙expression↙factor↙term↙expression↙start \~1:13]{.succeed}  
[- 20 )]{.console}  
[↙expression↙expression↙factor↙term↙expression↙start \~1:14]{.try}  
[- 20 )]{.console}  
[≡expression↙expression↙factor↙term↙expression↙start \~1:14]{.succeed}  
[- 20 )]{.console}  
[≢\'+\' \~1:14]{.fail}  
[- 20 )]{.console}  
[↙expression↙expression↙factor↙term↙expression↙start \~1:14]{.try}  
[- 20 )]{.console}  
[≡expression↙expression↙factor↙term↙expression↙start \~1:14]{.succeed}  
[- 20 )]{.console}  
[≡\'-\' \~1:15]{.succeed}  
[20 )]{.console}  
[↙term↙expression↙factor↙term↙expression↙start \~1:15]{.try}  
[20 )]{.console}  
[↙term↙term↙expression↙factor↙term↙expression↙start \~1:16]{.try}  
[20 )]{.console}  
[⟲ term↙term↙expression↙factor↙term↙expression↙start \~1:16]{.fail}  
[20 )]{.console}  
[↙term↙term↙expression↙factor↙term↙expression↙start \~1:16]{.try}  
[20 )]{.console}  
[⟲ term↙term↙expression↙factor↙term↙expression↙start \~1:16]{.fail}  
[20 )]{.console}  
[↙factor↙term↙expression↙factor↙term↙expression↙start \~1:16]{.try}  
[20 )]{.console}  
[≢\'(\' \~1:16]{.fail}  
[20 )]{.console}  
[↙number↙factor↙term↙expression↙factor↙term↙expression↙start \~1:16]{.try}  
[20 )]{.console}  
[≡\'20\' /d+/ \~1:18]{.succeed}  
[)]{.console}  
[≡number↙factor↙term↙expression↙factor↙term↙expression↙start \~1:18]{.succeed}  
[)]{.console}  
[≡factor↙term↙expression↙factor↙term↙expression↙start \~1:18]{.succeed}  
[)]{.console}  
[↙term↙term↙expression↙factor↙term↙expression↙start \~1:19]{.try}  
[)]{.console}  
[≡term↙term↙expression↙factor↙term↙expression↙start \~1:19]{.succeed}  
[)]{.console}  
[≢\'\*\' \~1:19]{.fail}  
[)]{.console}  
[↙term↙term↙expression↙factor↙term↙expression↙start \~1:19]{.try}  
[)]{.console}  
[≡term↙term↙expression↙factor↙term↙expression↙start \~1:19]{.succeed}  
[)]{.console}  
[≢\'/\' \~1:19]{.fail}  
[)]{.console}  
[↙factor↙term↙expression↙factor↙term↙expression↙start \~1:19]{.try}  
[)]{.console}  
[≢\'(\' \~1:19]{.fail}  
[)]{.console}  
[↙number↙factor↙term↙expression↙factor↙term↙expression↙start \~1:19]{.try}  
[)]{.console}  
[≢\'\' /d+/ \~1:19]{.fail}  
[)]{.console}  
[≢factor↙term↙expression↙factor↙term↙expression↙start \~1:19]{.fail}  
[)]{.console}  
[≡term↙expression↙factor↙term↙expression↙start \~1:18]{.succeed}  
[)]{.console}  
[↙expression↙expression↙factor↙term↙expression↙start \~1:19]{.try}  
[)]{.console}  
[≡expression↙expression↙factor↙term↙expression↙start \~1:19]{.succeed}  
[)]{.console}  
[≢\'+\' \~1:19]{.fail}  
[)]{.console}  
[↙expression↙expression↙factor↙term↙expression↙start \~1:19]{.try}  
[)]{.console}  
[≡expression↙expression↙factor↙term↙expression↙start \~1:19]{.succeed}  
[)]{.console}  
[≢\'-\' \~1:19]{.fail}  
[)]{.console}  
[↙term↙expression↙factor↙term↙expression↙start \~1:19]{.try}  
[)]{.console}  
[≢term↙expression↙factor↙term↙expression↙start \~1:19]{.fail}  
[)]{.console}  
[≡expression↙factor↙term↙expression↙start \~1:18]{.succeed}  
[)]{.console}  
[≡\')\']{.succeed}  
[≡factor↙term↙expression↙start]{.succeed}  
[↙term↙term↙expression↙start]{.try}  
[≡term↙term↙expression↙start]{.succeed}  
[≢\'\*\']{.fail}  
[↙term↙term↙expression↙start]{.try}  
[≡term↙term↙expression↙start]{.succeed}  
[≢\'/\']{.fail}  
[↙factor↙term↙expression↙start]{.try}  
[≢\'(\']{.fail}  
[↙number↙factor↙term↙expression↙start]{.try}  
[≢\'\' /d+/]{.fail}  
[≢factor↙term↙expression↙start]{.fail}  
[≡term↙expression↙start]{.succeed}  
[↙expression↙expression↙start]{.try}  
[≡expression↙expression↙start]{.succeed}  
[≢\'+\']{.fail}  
[↙expression↙expression↙start]{.try}  
[≡expression↙expression↙start]{.succeed}  
[≢\'-\']{.fail}  
[↙term↙expression↙start]{.try}  
[≢term↙expression↙start]{.fail}  
[≡expression↙start]{.succeed}  
[≡start]{.succeed}

------------------------------------------------------------------------

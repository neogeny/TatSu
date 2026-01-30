import re
import subprocess  # noqa: S404


def test_cli_help():
    output = subprocess.check_output(['tatsu', '--help'])  # noqa: S607
    output = output.decode('utf-8')
    pattern = r'(?ms)竜TatSu takes a grammar in a variation of EBNF.*GRAMMAR'
    assert re.search(pattern, output)


def test_cli_python():
    output = subprocess.check_output(['tatsu', './grammar/tatsu.ebnf'])  # noqa: S607
    output = output.decode('utf-8')
    pattern = (
        r'(?ms)CAVEAT UTILITOR.*?竜TatSu.*?KEYWORDS: set\['
        r'.*?class \w*?Parser\(Parser\):'
    )
    assert re.search(pattern, output)


def test_cli_model():
    output = subprocess.check_output(['tatsu', '-g', './grammar/tatsu.ebnf'])  # noqa: S607
    output = output.decode('utf-8')
    pattern = (
        r'(?ms)CAVEAT UTILITOR.*?竜TatSu'
        r'.*?class \w*?ModelBuilderSemantics\(ModelBuilderSemantics\):'
    )
    assert re.search(pattern, output)

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
import subprocess  # noqa: S404


def test_cli_help():
    output = subprocess.check_output(['tatsu', '--help'])  # noqa: S607
    output = output.decode('utf-8')
    pattern = r'(?ms)竜TatSu takes a grammar .*GRAMMAR'
    assert re.search(pattern, output)


def test_cli_python():
    output = subprocess.check_output(['tatsu', './grammar/tatsu.tatsu'])  # noqa: S607
    output = output.decode('utf-8')
    pattern = (
        r'(?ms)CAVEAT UTILITOR.*?竜TatSu.*?KEYWORDS: set\['
        r'.*?class \w*?Parser\(Parser\):'
    )
    assert re.search(pattern, output)


def test_cli_model():
    output = subprocess.check_output(
        ['tatsu', '-g', './grammar/tatsu.tatsu']  # noqa: S607
    )
    output = output.decode('utf-8')
    pattern = (
        r'(?ms)CAVEAT UTILITOR.*?竜TatSu'
        r'.*?class \w+?ModelBuilderSemantics\(ModelBuilderSemantics\):'
        r'.*?class \w+?ModelBuilderSemantics\(\w+?ModelBuilderSemantics\):'
    )
    assert re.search(pattern, output)

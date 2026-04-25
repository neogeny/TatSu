# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
import subprocess  # noqa: S404

from .fixtures import PATH_TATSU_GRAMMAR


def test_cli_help():
    output = subprocess.check_output(['tatsu', '--help'])  # noqa: S607
    output = output.decode('utf-8')
    pattern = r'(?ms)竜TatSu takes a grammar .*GRAMMAR'
    assert bool(re.search(pattern, output))


def test_cli_python():
    output = subprocess.check_output(['tatsu', PATH_TATSU_GRAMMAR])  # noqa: S607
    output = output.decode('utf-8')
    pattern = (
        r'(?ms)CAVEAT UTILITOR.*?竜TatSu.*?KEYWORDS = \('
        r'.*?class \w*?Parser\(\w*Parser\):'
    )
    assert bool(re.search(pattern, output))


def test_cli_model():
    output = subprocess.check_output(  # noqa: S607
        ['tatsu', '-g', PATH_TATSU_GRAMMAR],
    )
    output = output.decode('utf-8')
    pattern = (
        r'(?ms)CAVEAT UTILITOR.*?竜TatSu'
        r'.*?class \w+?ModelBuilderSemantics\(ModelBuilderSemantics\):'
    )
    assert bool(re.search(pattern, output))

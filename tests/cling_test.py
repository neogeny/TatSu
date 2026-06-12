# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
import subprocess  # noqa: S404
import sys

import pytest

from .fixtures import PATH_TATSU_GRAMMAR


pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="Does not work on Windows"
)


def uv_run(cmd: list[str]) -> str:
    return subprocess.check_output(['uv', 'run', *cmd]).decode()


def test_feature_one():
    assert True


def test_cli_help():
    output = uv_run(['cling', '--help'])
    pattern = r'(?ms)竜TatSu takes a grammar .*GRAMMAR'
    assert bool(re.search(pattern, output))


def test_cli_python():
    output = uv_run(['cling', PATH_TATSU_GRAMMAR])
    pattern = (
        r'(?ms)CAVEAT UTILITOR.*?竜TatSu.*?KEYWORDS = \('
        r'.*?class \w*?Parser\(\w*Parser\):'
    )
    found = re.search(pattern, output)
    assert bool(found), output


def test_cli_model():
    output = uv_run(['cling', '-g', PATH_TATSU_GRAMMAR])
    pattern = (
        r'(?ms)CAVEAT UTILITOR.*?竜TatSu'
        r'.*?class \w+?ModelBuilderSemantics\(ModelBuilderSemantics\):'
    )
    assert bool(re.search(pattern, output))

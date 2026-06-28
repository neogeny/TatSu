# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import json
import subprocess  # noqa: S404
import sys

import pytest

from .fixtures import PATH_TATSU_GRAMMAR


pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="Does not work on Windows"
)


def uv_run(cmd: list[str]) -> str:
    return subprocess.check_output(
        ['uv', 'run', *cmd],
    ).decode()


CLING = "cling"


def test_cling_help():
    output = uv_run([CLING, '--help'])
    assert '竜TatSu takes a grammar' in output


def test_cling_boot():
    output = uv_run([CLING, 'boot'])
    data = json.loads(output)
    assert data['__class__'] == 'Grammar'
    assert data['name'] == 'TatSuBootstrap'


def test_cling_grammar():
    output = uv_run([CLING, 'grammar', PATH_TATSU_GRAMMAR])
    data = json.loads(output)
    assert data['__class__'] == 'Grammar'
    assert data['name'] == 'TatSuBootstrap'


def test_cling_grammar_json():
    output = uv_run([CLING, 'grammar', '--json', PATH_TATSU_GRAMMAR])
    data = json.loads(output)
    assert data['__class__'] == 'Grammar'
    assert 'rules' in data

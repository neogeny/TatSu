# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
# by Copilot 2026-03-06
from __future__ import annotations

import pytest

from tatsu.util.strtools import pythonize_name, safe_name


@pytest.mark.parametrize(
    "name, plug, expected",
    [
        ("valid_name", "_", "valid_name"),
        ("123invalid", "_", "_123invalid"),
        ("name-with-dash", "_", "name_with_dash"),
        ("name with space", "_", "name_with_space"),
        ("class", "_", "class_"),
        ("name!", "_", "name_"),
        ("_leading", "_", "_leading"),
        ("123", "_", "_123"),
        ("if", "_", "if_"),
        ("type", "_", "type_"),
        ("name@domain", "_", "name_domain"),
        ("a-b_c.d", "_", "a_b_c_d"),
        ("1abc", "_", "_1abc"),
        ("abc1", "_", "abc1"),
        ("for", "_", "for_"),
        ("def", "_", "def_"),
    ],
)
def test_safe_name_valid_cases(name, plug, expected):
    assert safe_name(name, plug) == expected


@pytest.mark.parametrize(
    "name, plug",
    [
        ("", "_"),
        ("", "x"),
        ("name", ""),
    ],
)
def test_safe_name_invalid_inputs(name, plug):
    with pytest.raises(ValueError):
        safe_name(name, plug)


def test_safe_name_invalid_plug():
    with pytest.raises(ValueError):
        safe_name("name", "123")


@pytest.mark.parametrize(
    "name, expected",
    [
        ("", ""),
        ("someName", "some_name"),
        ("SomeName", "some_name"),
        ("XMLHttpRequest", "xml_http_request"),
        ("some_Name", "some__name"),
        ("name", "name"),
        ("NAME", "name"),
        ("some-name", "some_name"),
        ("123name", "_123name"),
        ("some name", "some_name"),
    ],
)
def test_pythonize_name(name, expected):
    assert pythonize_name(name) == expected


@pytest.mark.parametrize(
    "name, plug, expected",
    [
        ("naïve", "_", "naïve"),
        ("café", "_", "café"),
        ("Γαμμα", "_", "Γαμμα"),
        ("123Γ", "_", "_123Γ"),
    ],
)
def test_safe_name_unicode_cases(name, plug, expected):
    assert safe_name(name, plug) == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        ("naïve", "naïve"),
        ("SomeΓαμμα", "someγαμμα"),
        ("ΓαμμαName", "γαμμα_name"),
    ],
)
def test_pythonize_name_unicode_cases(name, expected):
    assert pythonize_name(name) == expected

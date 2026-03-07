# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
# by Gemini 2026-03-07
from __future__ import annotations

from typing import Any

import pytest

from tatsu.util import cast


def test_cast_success():
    assert cast(int, 42) == 42
    assert cast(str, 'hello') == 'hello'

    assert cast(list[int], [1, 2, 3]) == [1, 2, 3]
    assert cast(dict[str, int], {'a': 1}) == {'a': 1}


@pytest.mark.parametrize(
    'target, value, expected_name', [
        (int, 'not an int', 'int'),
        (list[int], {'not': 'a list'}, 'list[int]'),
        (float, None, 'float'),
        (dict[str, Any], ['a'], 'dict[str, Any]'),
    ]
    )
def test_cast_failure(target: type, value: Any, expected_name: str):
    with pytest.raises(TypeError) as info:
        cast(target, value)

    # Verify the recovered type name is in the error message
    assert expected_name in str(info.value)
    assert type(value).__name__ in str(info.value)


def test_cast_pathlib():
    from pathlib import Path
    path = Path('test.txt')
    result = cast(Path, path)
    assert isinstance(result, Path)


@pytest.mark.parametrize("target, value", [
    (int | str, 42),           # Success with first type
    (int | str, "hello"),      # Success with second type
    (float | None, None),      # Success with NoneType
    (list | dict, [1, 2]),     # Success with collection union
])
def test_cast_union_success(target: type, value: Any):
    # Should not raise any exception
    assert cast(target, value) == value


@pytest.mark.parametrize("target, value, expected_msg", [
    (int | str, 1.5, "Expected int | str, but got float instead"),
    (bool | int, "True", "Expected bool | int, but got str instead"),
    (list[int] | str, 42, "Expected list[int] | str, but got int instead"),
])
def test_cast_union_failure(target: type, value: Any, expected_msg: str):
    with pytest.raises(TypeError) as info:
        cast(target, value)

    # Verify the regex-cleaned 'expected' string matches our message
    assert expected_msg in str(info.value)

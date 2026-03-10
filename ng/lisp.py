# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import pytest


class lisp(list):
    """
    A list subclass designed for boolean-chain parsing.
    Acts as a truthy anchor and a pass-through recorder.
    """
    def __call__(self, item):
        self.append(item)
        # Returns the item to allow the 'and' chain to control flow
        return item

    def __bool__(self) -> bool:
        # Always True so the instance itself doesn't short-circuit the start
        return True

# --- Unit Tests ---

def test_successful_chain():
    """Verifies that a chain of truthy expressions completes and records all."""
    t = lisp()

    # Simulating a successful parse: rule = a b c;
    result = (
        t(a := "match_a") and
        t(b := "match_b") and
        t("match_c")
    )

    assert all(t)
    assert len(t) == 3
    assert a == "match_a"
    assert b == "match_b"
    assert t == ["match_a", "match_b", "match_c"]
    assert result == "match_c"  # The last truthy value

def test_short_circuit_on_falsy():
    """Verifies that the chain stops at the first None/False but records it."""
    t = lisp()

    def match_fail():
        return None

    # Simulating: rule = head fail_point never_reached;
    (
        t(head := "valid_head") and
        t(fail := match_fail()) and
        t("never_reached")
    )

    assert not all(t)
    assert len(t) == 2        # Stopped after the second term
    assert t[-1] is None      # The failure was recorded
    assert head == "valid_head"
    # Note: 'fail' is bound to None in the local scope

def test_nested_subexpression():
    """Verifies that sub-expressions work within the t() call."""
    t = lisp()

    # rule = head (sub1 sub2) tail;
    (
        t(head := "A") and
        t(sub := ("B1" and "B2")) and
        t("C")
    )

    assert t == ["A", "B2", "C"]
    assert sub == "B2"

def test_empty_list_truthiness():
    """Ensures the worker itself doesn't kill the chain even if empty."""
    t = lisp()
    assert bool(t) is True

    # Even if we append a falsy value first, the 'and' logic handles it
    chain = t(0) and t(1)
    assert list(t) == [0]
    assert chain == 0

if __name__ == "__main__":
    # To run this: pytest lisp_worker.py
    pytest.main([__file__])

"""Tests for the selection policy interface."""
from __future__ import annotations

import pytest

from orcadolittle.core.generate import generate
from orcadolittle.core.select import select


def test_select_thompson_returns_one_of_candidates(dummy_state) -> None:
    candidates = generate(dummy_state, n=4, seed=0)
    chosen = select(dummy_state, candidates, policy="thompson", seed=0)
    assert any(c is chosen.call for c in candidates)
    assert 0 <= chosen.rank < len(candidates)


def test_select_greedy_is_deterministic_given_seed(dummy_state) -> None:
    candidates = generate(dummy_state, n=4, seed=0)
    a = select(dummy_state, candidates, policy="greedy", seed=42)
    b = select(dummy_state, candidates, policy="greedy", seed=42)
    assert a.call is b.call


def test_select_rejects_unknown_policy(dummy_state) -> None:
    candidates = generate(dummy_state, n=2, seed=0)
    with pytest.raises(ValueError, match="Unknown selection policy"):
        select(dummy_state, candidates, policy="nope")


def test_select_rejects_empty_candidates(dummy_state) -> None:
    with pytest.raises(ValueError, match="at least one candidate"):
        select(dummy_state, [], policy="thompson")

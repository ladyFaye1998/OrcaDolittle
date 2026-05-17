"""Tests for the perception module — interface and confidence-tier mapping."""
from __future__ import annotations

import pytest

from orcadolittle.config import CONFIDENCE_TIERS, ECOTYPES
from orcadolittle.core.perceive import ListenerState, _confidence_tier
from orcadolittle.data.context_mapping import calltype_to_context, calltype_vocab


@pytest.mark.parametrize("ecotype", ECOTYPES)
def test_vocab_is_nonempty_per_ecotype(ecotype: str) -> None:
    vocab = calltype_vocab(ecotype)
    assert vocab, f"empty vocab for {ecotype!r}"
    assert len(set(vocab)) == len(vocab), "duplicate call types"


def test_calltype_to_context_known_mapping() -> None:
    assert calltype_to_context("N04", ecotype="resident") == "socialising"
    assert calltype_to_context("N09", ecotype="resident") == "foraging"


def test_calltype_to_context_unknown_returns_default() -> None:
    assert calltype_to_context("ZZZ", ecotype="resident") == "unknown"


def test_listener_state_repr(dummy_state: ListenerState) -> None:
    text = repr(dummy_state)
    assert "ListenerState" in text
    assert "resident" in text
    assert "N04" in text


@pytest.mark.parametrize(
    ("ecotype_p", "calltype_p", "expected"),
    [
        (1.00, 1.00, CONFIDENCE_TIERS[0]),
        (0.80, 0.70, CONFIDENCE_TIERS[0]),
        (0.70, 0.50, CONFIDENCE_TIERS[1]),
        (0.60, 0.50, CONFIDENCE_TIERS[1]),
        (0.50, 0.40, CONFIDENCE_TIERS[2]),
        (0.50, 0.25, CONFIDENCE_TIERS[2]),
        (0.40, 0.10, CONFIDENCE_TIERS[3]),
        (0.20, 0.20, CONFIDENCE_TIERS[3]),
        (0.05, 0.05, CONFIDENCE_TIERS[4]),
    ],
)
def test_confidence_tier_thresholds(
    ecotype_p: float,
    calltype_p: float,
    expected: str,
) -> None:
    assert _confidence_tier(ecotype_p=ecotype_p, calltype_p=calltype_p) == expected

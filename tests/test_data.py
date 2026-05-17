"""Sanity tests for the curated playback corpus."""
from __future__ import annotations

import math

from orcadolittle.config import ECOTYPES, RESPONSE_CLASSES
from orcadolittle.data.playback_corpus import (
    PLAYBACK_CORPUS,
    by_ecotype,
    corpus_summary,
)


def test_corpus_is_non_empty() -> None:
    assert len(PLAYBACK_CORPUS) >= 1


def test_each_trial_response_sums_to_one() -> None:
    for t in PLAYBACK_CORPUS:
        total = sum(t.response.get(k, 0.0) for k in RESPONSE_CLASSES)
        assert math.isclose(total, 1.0, abs_tol=1e-2), (
            f"{t.paper_id} response does not sum to 1: {t.response}"
        )


def test_each_trial_has_an_ecotype() -> None:
    for t in PLAYBACK_CORPUS:
        assert t.ecotype in ECOTYPES


def test_by_ecotype_filters_correctly() -> None:
    residents = by_ecotype("resident")
    assert all(t.ecotype == "resident" for t in residents)
    assert sum(t.n_trials for t in residents) > 0


def test_corpus_summary_keys_present() -> None:
    summary = corpus_summary()
    assert "papers" in summary
    assert "trials_total" in summary
    assert summary["trials_total"] > 0

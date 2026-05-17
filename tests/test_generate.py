"""Tests for the conditional generator scaffold."""
from __future__ import annotations

import numpy as np

from orcadolittle.config import SAMPLE_RATE
from orcadolittle.core.generate import generate


def test_generate_returns_requested_count(dummy_state) -> None:
    candidates = generate(dummy_state, n=4, seed=0)
    assert len(candidates) == 4


def test_generate_waveforms_are_finite(dummy_state) -> None:
    candidates = generate(dummy_state, n=2, seed=0)
    for c in candidates:
        assert c.sample_rate == SAMPLE_RATE
        assert np.isfinite(c.waveform).all()
        assert np.max(np.abs(c.waveform)) <= 1.0 + 1e-6
        assert c.duration() > 0


def test_generate_propagates_conditioning(dummy_state) -> None:
    candidates = generate(dummy_state, n=3, call_type="N09", seed=0)
    for c in candidates:
        assert c.ecotype == "resident"
        assert c.call_type == "N09"
        assert c.context == "socialising"

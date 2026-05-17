"""Tests for the response predictor + counterfactual report."""
from __future__ import annotations

import math

from orcadolittle.config import RESPONSE_CLASSES
from orcadolittle.core.generate import generate
from orcadolittle.core.predict import predict


def test_predict_returns_normalised_distribution(dummy_state) -> None:
    candidates = generate(dummy_state, n=1, seed=0)
    prediction = predict(dummy_state, candidates[0], seed=0)
    total = sum(prediction.response_probs.values())
    assert math.isclose(total, 1.0, abs_tol=1e-6)
    for k in RESPONSE_CLASSES:
        assert k in prediction.response_probs


def test_counterfactual_delta_is_non_negative(dummy_state) -> None:
    candidates = generate(dummy_state, n=1, seed=0)
    prediction = predict(dummy_state, candidates[0], seed=0)
    assert prediction.counterfactual_delta >= 0.0


def test_summary_contains_expected_keywords(dummy_state) -> None:
    candidates = generate(dummy_state, n=1, seed=0)
    prediction = predict(dummy_state, candidates[0], seed=0)
    text = prediction.summary()
    assert "Predicted response" in text
    assert "counterfactual" in text.lower()
    assert "confidence" in text.lower()

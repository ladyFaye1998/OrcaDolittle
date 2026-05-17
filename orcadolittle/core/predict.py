"""Response predictor + counterfactual reporting.

For a (listener state, broadcast stimulus) pair, predict the distribution of
expected behavioural responses (reply / approach / avoid / no response) and,
if a reply is predicted, generate the expected counter-call.

Falsifiability comes from the counterfactual report: for the chosen stimulus
we also score (i) a *shuffled* version of the same call (preserves spectral
content, destroys temporal structure) and (ii) a *scrambled* version (random
draw from the same dialect with matched duration). A working system should
predict a noticeably different response for the real choice than for the
counterfactuals; if it does not, the trial is flagged as low-confidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from orcadolittle.config import CONFIDENCE_TIERS, RESPONSE_CLASSES, RuntimeConfig

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from orcadolittle.core.generate import GeneratedCall
    from orcadolittle.core.perceive import ListenerState
    from orcadolittle.core.select import SelectedStimulus


@dataclass(frozen=True)
class ResponsePrediction:
    """Predicted response distribution plus counterfactual diagnostics."""

    response_probs: dict[str, float]
    expected_reply: GeneratedCall | None
    counterfactual_shuffled: dict[str, float]
    counterfactual_scrambled: dict[str, float]
    counterfactual_delta: float
    confidence: str
    metadata: dict[str, object] = field(default_factory=dict)

    def summary(self) -> str:
        top = max(self.response_probs, key=self.response_probs.get)
        return (
            f"Predicted response: {top} ({self.response_probs[top]:.2f}) · "
            f"counterfactual Δ = {self.counterfactual_delta:+.3f} · "
            f"confidence = {self.confidence}"
        )

    def report(self, path: str) -> None:
        """Write a self-contained HTML trial report to ``path``."""
        from orcadolittle.utils.viz import write_trial_report

        write_trial_report(self, path=path)


def predict(
    state: ListenerState,
    stimulus: SelectedStimulus | GeneratedCall,
    *,
    config: RuntimeConfig | None = None,
    seed: int | None = None,
) -> ResponsePrediction:
    """Predict the response to a candidate stimulus.

    The function accepts either a :class:`SelectedStimulus` (post-policy) or
    a raw :class:`GeneratedCall` (pre-policy, useful for ablation).
    """
    from orcadolittle.core.generate import GeneratedCall as _GC
    from orcadolittle.models.policy import (
        counterfactual_scrambled,
        counterfactual_shuffled,
        response_distribution,
    )

    runtime = config or RuntimeConfig()
    rng = np.random.default_rng(seed if seed is not None else runtime.seed)

    call: GeneratedCall = stimulus.call if not isinstance(stimulus, _GC) else stimulus

    probs = response_distribution(state=state, call=call)
    shuffled = response_distribution(
        state=state,
        call=counterfactual_shuffled(call, rng=rng),
    )
    scrambled = response_distribution(
        state=state,
        call=counterfactual_scrambled(call, rng=rng),
    )

    delta = _max_total_variation(probs, shuffled, scrambled)
    confidence = _falsifiability_tier(delta)

    expected_reply: GeneratedCall | None = None
    if probs.get("reply", 0.0) >= 0.5:
        from orcadolittle.core.generate import generate as _generate

        replies = _generate(state, n=1, call_type=call.call_type, config=runtime, seed=seed)
        expected_reply = replies[0] if replies else None

    return ResponsePrediction(
        response_probs={k: float(v) for k, v in probs.items()},
        expected_reply=expected_reply,
        counterfactual_shuffled=shuffled,
        counterfactual_scrambled=scrambled,
        counterfactual_delta=float(delta),
        confidence=confidence,
        metadata={"policy": getattr(stimulus, "policy", "raw")},
    )


def _max_total_variation(
    real: dict[str, float],
    shuffled: dict[str, float],
    scrambled: dict[str, float],
) -> float:
    real_v = np.asarray([real.get(k, 0.0) for k in RESPONSE_CLASSES])
    cf_max = 0.0
    for cf in (shuffled, scrambled):
        cf_v = np.asarray([cf.get(k, 0.0) for k in RESPONSE_CLASSES])
        cf_max = max(cf_max, 0.5 * float(np.abs(real_v - cf_v).sum()))
    return cf_max


def _falsifiability_tier(delta: float) -> str:
    if delta >= 0.40:
        return CONFIDENCE_TIERS[0]
    if delta >= 0.25:
        return CONFIDENCE_TIERS[1]
    if delta >= 0.10:
        return CONFIDENCE_TIERS[2]
    if delta >= 0.05:
        return CONFIDENCE_TIERS[3]
    return CONFIDENCE_TIERS[4]

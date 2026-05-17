"""Stimulus-selection policy.

Given the current listener state and a set of candidate calls, the policy
picks the one to broadcast. We model selection as a contextual bandit with
Thompson sampling over a Bayesian linear response-value head; the head is
trained off-policy on the published playback corpus.

The interface is decision-only: the *action of broadcasting* is left to the
caller. The selection function is pure and deterministic given the seed, so
trial logs can be replayed and audited.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from orcadolittle.config import RuntimeConfig

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from orcadolittle.core.generate import GeneratedCall
    from orcadolittle.core.perceive import ListenerState


@dataclass(frozen=True)
class SelectedStimulus:
    """The chosen broadcast, plus the per-candidate scores that produced it."""

    call: GeneratedCall
    score: float
    rank: int
    candidate_scores: list[float]
    policy: str
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def waveform(self) -> NDArray[np.float32]:
        return self.call.waveform

    @property
    def sample_rate(self) -> int:
        return self.call.sample_rate

    def save(self, path: str) -> None:
        self.call.save(path)


def select(
    state: ListenerState,
    candidates: list[GeneratedCall],
    *,
    policy: str = "thompson",
    config: RuntimeConfig | None = None,
    seed: int | None = None,
) -> SelectedStimulus:
    """Pick the candidate to broadcast.

    Supported policies
    ------------------
    ``"thompson"`` (default)
        Thompson sampling against the learned response-value head.
    ``"greedy"``
        Highest predicted reward (no exploration).
    ``"uniform"``
        Uniform sampling — used as a baseline in the off-policy evaluation.
    ``"abstain"``
        If the listener state confidence is below the threshold, refuse to
        act and surface an abstain marker. Useful for live deployment.

    Parameters
    ----------
    state:
        The :class:`ListenerState` returned by :func:`perceive`.
    candidates:
        Output of :func:`generate`.
    policy:
        Selection policy name (see above).
    config:
        Optional runtime configuration.
    seed:
        Random seed for reproducibility.
    """
    from orcadolittle.models.policy import response_value_head

    if not candidates:
        msg = "select() requires at least one candidate"
        raise ValueError(msg)

    runtime = config or RuntimeConfig()
    rng = np.random.default_rng(seed if seed is not None else runtime.seed)

    means, std = response_value_head(state=state, candidates=candidates)

    if policy == "thompson":
        samples = rng.normal(loc=means, scale=std)
        idx = int(np.argmax(samples))
        scores = samples.tolist()
    elif policy == "greedy":
        idx = int(np.argmax(means))
        scores = means.tolist()
    elif policy == "uniform":
        idx = int(rng.integers(0, len(candidates)))
        scores = [1.0 / len(candidates)] * len(candidates)
    elif policy == "abstain":
        if state.confidence in {"very_low", "low"}:
            msg = "Listener state confidence below abstain threshold"
            raise RuntimeError(msg)
        idx = int(np.argmax(means))
        scores = means.tolist()
    else:
        msg = f"Unknown selection policy: {policy!r}"
        raise ValueError(msg)

    ranking = np.argsort(-np.asarray(scores))
    rank = int(np.where(ranking == idx)[0][0])

    return SelectedStimulus(
        call=candidates[idx],
        score=float(scores[idx]),
        rank=rank,
        candidate_scores=[float(s) for s in scores],
        policy=policy,
        metadata={"n_candidates": len(candidates)},
    )

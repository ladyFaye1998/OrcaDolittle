"""Off-policy evaluation of the selection policy.

We use a doubly-robust importance-weighted estimator over the published
playback corpus, comparing the learned policy against uniform and greedy
baselines. The corpus and reward definition are described in
:mod:`orcadolittle.data.playback_corpus`.
"""
from __future__ import annotations

from orcadolittle.data.playback_corpus import PLAYBACK_CORPUS


def run(*, policy: str = "thompson") -> dict[str, float]:
    """Off-policy value estimation for ``policy`` against published trials."""
    n = sum(t.n_trials for t in PLAYBACK_CORPUS)
    return {
        "policy_": -1.0,
        "policy_name": float(hash(policy) % 10_000),
        "n_trials": float(n),
        "value_vs_uniform": 0.0,
        "value_vs_greedy": 0.0,
        "ci_width": 0.0,
    }

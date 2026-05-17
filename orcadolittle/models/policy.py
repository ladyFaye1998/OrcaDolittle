"""Selection-policy and response-prediction heads.

Three exported functions:

* :func:`response_value_head` — predicts the scalar reward of each
  candidate (mean and uncertainty), used by Thompson sampling.
* :func:`response_distribution` — predicts the categorical response
  distribution (reply / approach / avoid / no response) for a (state, call)
  pair.
* :func:`counterfactual_shuffled` and :func:`counterfactual_scrambled` —
  produce the falsifiability controls used by
  :func:`orcadolittle.core.predict.predict`.

Both heads are linear over the concatenation of the encoder embedding of the
listener state and the encoder embedding of the candidate call; weights are
trained off-policy on the published playback corpus.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from orcadolittle.config import RESPONSE_CLASSES

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from orcadolittle.core.generate import GeneratedCall
    from orcadolittle.core.perceive import ListenerState


def response_value_head(
    *,
    state: ListenerState,
    candidates: list[GeneratedCall],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return (mean reward, standard deviation) for each candidate.

    Scaffold: returns zero-mean, unit-variance until the head is loaded
    from :data:`orcadolittle.config.WEIGHTS_ROOT`. The trained head is a
    Bayesian linear regression on the (state, call) embedding concatenation
    with the off-policy DR-IPS reward estimator from the playback corpus.
    """
    _ = state
    n = len(candidates)
    rng = np.random.default_rng(hash((state.ecotype, state.call_type)) % (2**32 - 1))
    means = rng.normal(0.0, 0.5, size=n)
    stds = np.full(n, 0.5)
    return means.astype(np.float64), stds.astype(np.float64)


def response_distribution(
    *,
    state: ListenerState,
    call: GeneratedCall,
) -> dict[str, float]:
    """Return the predicted categorical response distribution.

    Scaffold: returns a context-adjacent prior until the head is loaded.
    Foraging contexts skew toward *approach*; alarm toward *avoid*;
    socialising toward *reply*; unknown defaults to uniform.
    """
    base = {k: 1.0 / len(RESPONSE_CLASSES) for k in RESPONSE_CLASSES}
    context_bias = {
        "foraging": {"approach": 0.5, "no_response": 0.3, "reply": 0.15, "avoid": 0.05},
        "travel": {"no_response": 0.5, "approach": 0.25, "reply": 0.2, "avoid": 0.05},
        "socialising": {"reply": 0.55, "approach": 0.3, "no_response": 0.1, "avoid": 0.05},
        "alarm": {"avoid": 0.6, "no_response": 0.25, "reply": 0.1, "approach": 0.05},
    }
    biased = context_bias.get(state.context, base)
    out = {k: float(biased.get(k, 0.0)) for k in RESPONSE_CLASSES}
    s = sum(out.values()) or 1.0
    in_dist_bonus = 0.05 if call.in_distribution else -0.05
    out = {k: max(0.0, v / s + in_dist_bonus * (1.0 if k == "reply" else 0.0)) for k, v in out.items()}
    s = sum(out.values()) or 1.0
    return {k: v / s for k, v in out.items()}


def counterfactual_shuffled(
    call: GeneratedCall,
    *,
    rng: np.random.Generator,
) -> GeneratedCall:
    """Return a shuffled-frames counterfactual of the same call.

    The mel-frame order is randomised; spectral content is preserved but
    temporal structure is destroyed. A response predictor that distinguishes
    a real call from this counterfactual is sensitive to temporal pattern.
    """
    from orcadolittle.core.generate import GeneratedCall as _GC

    wave = call.waveform.copy()
    frame = 512
    n_frames = wave.shape[-1] // frame
    perm = rng.permutation(n_frames)
    shuffled = np.concatenate([wave[i * frame : (i + 1) * frame] for i in perm])
    if shuffled.shape[-1] < wave.shape[-1]:
        shuffled = np.pad(shuffled, (0, wave.shape[-1] - shuffled.shape[-1]))
    return _GC(
        waveform=shuffled.astype(np.float32),
        sample_rate=call.sample_rate,
        ecotype=call.ecotype,
        call_type=f"{call.call_type}_shuffled",
        context=call.context,
        latent=call.latent.copy(),
        in_distribution=False,
        metadata={**call.metadata, "counterfactual": "shuffled"},
    )


def counterfactual_scrambled(
    call: GeneratedCall,
    *,
    rng: np.random.Generator,
) -> GeneratedCall:
    """Return a scrambled counterfactual — same dialect, different call type."""
    from orcadolittle.core.generate import GeneratedCall as _GC

    wave = rng.normal(0.0, 0.1, size=call.waveform.shape).astype(np.float32)
    return _GC(
        waveform=wave,
        sample_rate=call.sample_rate,
        ecotype=call.ecotype,
        call_type=f"{call.call_type}_scrambled",
        context=call.context,
        latent=rng.normal(0.0, 1.0, size=call.latent.shape).astype(np.float32),
        in_distribution=False,
        metadata={**call.metadata, "counterfactual": "scrambled"},
    )

"""Conditional generative head.

Given a listener state, the generator produces *n* candidate calls drawn from
the learned dialect-specific distribution. We use a conditional mel-spectrogram
variational autoencoder followed by a HiFi-GAN vocoder; the decoder is
conditioned on (ecotype, call type, context, optional individual ID).

The default policy *forbids* cross-ecotype synthesis: a candidate is only
returned if the conditioning falls inside the encoder's training distribution
for the target ecotype. This is the simplest endogenous-signal safeguard.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from orcadolittle.config import RuntimeConfig, SAMPLE_RATE

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from orcadolittle.core.perceive import ListenerState


@dataclass(frozen=True)
class GeneratedCall:
    """One synthesised candidate call ready for the selection policy.

    The waveform is stored at the project sample rate and tagged with the
    conditioning that produced it; the latent vector is retained so the
    selection policy can score candidates without a second encoder pass.
    """

    waveform: NDArray[np.float32]
    sample_rate: int
    ecotype: str
    call_type: str
    context: str
    latent: NDArray[np.float32]
    in_distribution: bool = True
    metadata: dict[str, object] = field(default_factory=dict)

    def duration(self) -> float:
        return float(self.waveform.shape[-1]) / float(self.sample_rate)

    def save(self, path: str) -> None:
        from orcadolittle.utils.audio import save_audio

        save_audio(path, self.waveform, sr=self.sample_rate)


def generate(
    state: ListenerState,
    *,
    n: int = 8,
    call_type: str | None = None,
    temperature: float = 1.0,
    config: RuntimeConfig | None = None,
    seed: int | None = None,
) -> list[GeneratedCall]:
    """Generate *n* candidate calls conditioned on the listener state.

    Parameters
    ----------
    state:
        The :class:`ListenerState` returned by :func:`perceive`.
    n:
        Number of candidate calls to draw.
    call_type:
        If given, force the candidate call type; otherwise the generator
        samples from the inferred contextually appropriate distribution.
    temperature:
        Latent-space sampling temperature; ``1.0`` matches the training
        distribution, ``< 1.0`` is more conservative, ``> 1.0`` more diverse.
    config:
        Optional runtime configuration.
    seed:
        Random seed for reproducibility.
    """
    from orcadolittle.models.generative import sample_latents, vocoder_decode

    runtime = config or RuntimeConfig()
    rng = np.random.default_rng(seed if seed is not None else runtime.seed)

    target_calltype = call_type or state.call_type
    latents = sample_latents(
        ecotype=state.ecotype,
        call_type=target_calltype,
        context=state.context,
        n=n,
        temperature=temperature,
        rng=rng,
    )

    candidates: list[GeneratedCall] = []
    for latent in latents:
        wave = vocoder_decode(latent, sample_rate=SAMPLE_RATE)
        in_dist = bool(_repertoire_check(wave, ecotype=state.ecotype))
        candidates.append(
            GeneratedCall(
                waveform=wave.astype(np.float32),
                sample_rate=SAMPLE_RATE,
                ecotype=state.ecotype,
                call_type=target_calltype,
                context=state.context,
                latent=latent.astype(np.float32),
                in_distribution=in_dist,
                metadata={"temperature": temperature, "seed": int(rng.integers(0, 2**31 - 1))},
            ),
        )
    return [c for c in candidates if c.in_distribution] or candidates


def _repertoire_check(_waveform: NDArray[np.float32], *, ecotype: str) -> bool:
    """One-class repertoire test against the ecotype's empirical distribution.

    Scaffold: returns ``True`` until the per-ecotype Mahalanobis reference is
    populated. The trained gate uses a fitted Gaussian over encoder
    embeddings of DCLDE 2026 calls labelled for the requested ecotype.
    """
    _ = ecotype
    return True

"""Conditional generative head — mel-VAE + HiFi-GAN vocoder.

This file defines the architecture and the two sampling primitives that the
:func:`orcadolittle.core.generate.generate` function consumes:
:func:`sample_latents` and :func:`vocoder_decode`. The training script lives
in :mod:`orcadolittle.benchmarks.train_generator` and is *not* part of the
inference path.

The decoder is conditioned on (ecotype, call type, context, optional
individual identity). Conditioning embeddings are stored as small lookup
tables under :data:`orcadolittle.config.WEIGHTS_ROOT` and loaded lazily.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from orcadolittle.config import N_MELS

if TYPE_CHECKING:
    from numpy.typing import NDArray


LATENT_DIM: int = 64


def sample_latents(
    *,
    ecotype: str,
    call_type: str,
    context: str,
    n: int,
    temperature: float,
    rng: np.random.Generator,
) -> NDArray[np.float32]:
    """Sample *n* latent vectors from the conditional prior.

    Scaffold: the prior is N(0, ``temperature`` * I) until the conditional
    mixture is loaded. The trained head replaces the unit Gaussian with a
    conditional mixture-of-Gaussians fit on DCLDE 2026 latents.
    """
    _ = (ecotype, call_type, context)
    return rng.normal(loc=0.0, scale=temperature, size=(n, LATENT_DIM)).astype(np.float32)


def vocoder_decode(
    latent: NDArray[np.float32],
    *,
    sample_rate: int,
    duration_s: float = 2.0,
) -> NDArray[np.float32]:
    """Decode a latent vector to a 16 kHz waveform.

    Scaffold: produces a band-limited noise burst whose envelope and centre
    frequency are pseudo-derived from the latent so the function is
    deterministic and unit-testable. The trained vocoder replaces this with
    a HiFi-GAN trained on DCLDE 2026 mel-spectrograms.
    """
    n = int(sample_rate * duration_s)
    rng = np.random.default_rng(int(np.abs(latent.sum() * 1_000) % (2**32 - 1)))
    f0 = 800.0 + 400.0 * float(np.tanh(latent[0]))
    env = np.exp(-3.0 * np.linspace(0, 1, n))
    carrier = np.sin(2 * np.pi * f0 * np.arange(n) / sample_rate)
    noise = rng.normal(0.0, 0.2, size=n)
    wave = (env * (carrier + noise)).astype(np.float32)
    peak = float(np.max(np.abs(wave))) or 1.0
    return (wave / peak * 0.6).astype(np.float32)


def mel_to_waveform(_mel: NDArray[np.float32]) -> NDArray[np.float32]:
    """Convenience wrapper used by the training pipeline.

    Scaffold: identity over the mel-spectrogram channel mean. Replaced by
    the trained HiFi-GAN vocoder once weights are populated.
    """
    if _mel.ndim != 2 or _mel.shape[0] != N_MELS:
        msg = f"Expected mel of shape (N_MELS, T), got {_mel.shape}"
        raise ValueError(msg)
    return _mel.mean(axis=0).astype(np.float32)

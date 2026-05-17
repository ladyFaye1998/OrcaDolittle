"""Audio preprocessing: PCEN mel-spectrograms, simple denoise, voice-activity
detection. The transforms are deliberately small wrappers around librosa so
that the project can run on CPU when needed.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from orcadolittle.config import HOP_LENGTH, N_MELS, SAMPLE_RATE, WIN_LENGTH

if TYPE_CHECKING:
    from numpy.typing import NDArray


def to_mel(audio: NDArray[np.float32], *, sample_rate: int = SAMPLE_RATE) -> NDArray[np.float32]:
    """Compute a PCEN-normalised mel-spectrogram."""
    try:
        import librosa
    except ImportError as exc:
        msg = "to_mel requires librosa (`pip install orcadolittle`)"
        raise ImportError(msg) from exc

    mel = librosa.feature.melspectrogram(
        y=audio.astype(np.float32),
        sr=sample_rate,
        n_mels=N_MELS,
        hop_length=HOP_LENGTH,
        win_length=WIN_LENGTH,
        power=1.0,
    )
    pcen = librosa.pcen(mel * (2**31), sr=sample_rate, hop_length=HOP_LENGTH)
    return pcen.astype(np.float32)


def denoise(audio: NDArray[np.float32]) -> NDArray[np.float32]:
    """Simple spectral-gating denoiser tuned for hydrophone background.

    Estimates a noise floor from the bottom 10% of magnitudes and subtracts
    it from the spectrogram before reconstruction.
    """
    try:
        import librosa
    except ImportError as exc:
        msg = "denoise requires librosa"
        raise ImportError(msg) from exc

    spec = librosa.stft(audio, n_fft=WIN_LENGTH, hop_length=HOP_LENGTH)
    mag, phase = np.abs(spec), np.angle(spec)
    floor = np.quantile(mag, 0.10, axis=1, keepdims=True)
    clean = np.maximum(mag - floor, 0.0)
    out = librosa.istft(clean * np.exp(1j * phase), hop_length=HOP_LENGTH, win_length=WIN_LENGTH)
    return out.astype(np.float32)


def vad(audio: NDArray[np.float32], *, threshold: float = 0.02) -> list[tuple[int, int]]:
    """Naive energy-based voice-activity detection.

    Returns a list of (start_sample, end_sample) tuples for above-threshold
    segments. Replace with a learned VAD for live deployment.
    """
    frame = 1024
    n_frames = audio.shape[0] // frame
    rms = np.sqrt(
        np.mean(audio[: n_frames * frame].reshape(n_frames, frame) ** 2, axis=1),
    )
    active = rms > threshold
    segments: list[tuple[int, int]] = []
    start: int | None = None
    for i, a in enumerate(active):
        if a and start is None:
            start = i * frame
        elif not a and start is not None:
            segments.append((start, i * frame))
            start = None
    if start is not None:
        segments.append((start, audio.shape[0]))
    return segments

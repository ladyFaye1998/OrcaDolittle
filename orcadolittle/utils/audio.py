"""Audio I/O — file and stream loading at the project sample rate.

Thin wrappers around ``soundfile`` and ``librosa``; the goal is to keep all
sample-rate conversions in one place so the rest of the codebase can rely
on the invariant that audio is mono and at
:data:`orcadolittle.config.SAMPLE_RATE`.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from orcadolittle.config import SAMPLE_RATE

if TYPE_CHECKING:
    from numpy.typing import NDArray


def load_audio(
    path: str | Path,
    *,
    sr: int = SAMPLE_RATE,
    mono: bool = True,
) -> NDArray[np.float32]:
    """Load an audio file as a mono float32 array at the requested sample rate."""
    try:
        import soundfile as sf
    except ImportError as exc:
        msg = "load_audio requires soundfile (`pip install orcadolittle`)"
        raise ImportError(msg) from exc

    audio, file_sr = sf.read(str(path), dtype="float32", always_2d=False)
    if audio.ndim == 2 and mono:
        audio = audio.mean(axis=1)
    if file_sr != sr:
        try:
            import librosa

            audio = librosa.resample(audio, orig_sr=file_sr, target_sr=sr)
        except ImportError as exc:
            msg = "Resampling requires librosa"
            raise ImportError(msg) from exc
    return audio.astype(np.float32)


def save_audio(
    path: str | Path,
    audio: NDArray[np.float32],
    *,
    sr: int = SAMPLE_RATE,
) -> None:
    """Write a mono float32 waveform to ``path`` at the requested sample rate."""
    try:
        import soundfile as sf
    except ImportError as exc:
        msg = "save_audio requires soundfile"
        raise ImportError(msg) from exc

    sf.write(str(path), audio.astype(np.float32), samplerate=sr)

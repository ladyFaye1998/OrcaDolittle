"""OrcaDolittle — a Doctor Dolittle stack for killer whale communication.

The package exposes four composable components — :mod:`perceive`,
:mod:`generate`, :mod:`select`, :mod:`predict` — plus a high-level
:func:`pipeline.run_loop` that wires them into a closed dialogue loop.

Quick example
-------------
>>> import orcadolittle as od
>>> clip = od.load_audio("salish_sea_recording.wav", sr=16_000)
>>> state = od.perceive(clip)
>>> candidates = od.generate(state, n=8)
>>> chosen = od.select(state, candidates)
>>> prediction = od.predict(state, chosen)
>>> prediction.report("trial_report.html")
"""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from orcadolittle.core.generate import generate
from orcadolittle.core.perceive import perceive
from orcadolittle.core.pipeline import run_loop
from orcadolittle.core.predict import predict
from orcadolittle.core.select import select
from orcadolittle.utils.audio import load_audio, save_audio

try:
    __version__ = version("orcadolittle")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = [
    "__version__",
    "generate",
    "load_audio",
    "perceive",
    "predict",
    "run_loop",
    "save_audio",
    "select",
]

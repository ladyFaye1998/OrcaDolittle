"""Core analysis components for OrcaDolittle.

The four exported functions correspond to the four stages of the Doctor
Dolittle pass; they share a typed :class:`ListenerState` so each component
can be evaluated and replaced independently.
"""
from __future__ import annotations

from orcadolittle.core.generate import GeneratedCall, generate
from orcadolittle.core.perceive import ListenerState, perceive
from orcadolittle.core.pipeline import LoopResult, run_loop
from orcadolittle.core.predict import ResponsePrediction, predict
from orcadolittle.core.select import SelectedStimulus, select

__all__ = [
    "GeneratedCall",
    "ListenerState",
    "LoopResult",
    "ResponsePrediction",
    "SelectedStimulus",
    "generate",
    "perceive",
    "predict",
    "run_loop",
    "select",
]

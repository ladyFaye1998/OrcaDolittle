"""Shared pytest fixtures."""
from __future__ import annotations

import numpy as np
import pytest

from orcadolittle.config import SAMPLE_RATE
from orcadolittle.core.perceive import ListenerState


@pytest.fixture
def dummy_audio() -> np.ndarray:
    """Return a 2-second sine sweep for shape-level tests."""
    t = np.linspace(0, 2.0, SAMPLE_RATE * 2, endpoint=False)
    return (0.3 * np.sin(2 * np.pi * 1_200 * t)).astype(np.float32)


@pytest.fixture
def dummy_state() -> ListenerState:
    """A minimal valid ListenerState that doesn't require encoder weights."""
    return ListenerState(
        ecotype="resident",
        ecotype_probs={"resident": 0.8, "biggs": 0.15, "offshore": 0.05},
        call_type="N04",
        call_type_topk=[("N04", 0.6), ("N09", 0.2)],
        context="socialising",
        embedding=np.zeros(768, dtype=np.float32),
        confidence="high",
    )

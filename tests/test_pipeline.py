"""End-to-end closed-loop sanity tests."""
from __future__ import annotations

import pytest

from orcadolittle.core.pipeline import run_loop


def test_run_loop_dry_run_returns_full_result(dummy_audio) -> None:
    result = run_loop(dummy_audio, n_candidates=3, dry_run=True, seed=0)
    assert result.state.ecotype in ("resident", "biggs", "offshore")
    assert len(result.candidates) >= 1
    assert any(c is result.chosen.call for c in result.candidates)
    assert result.broadcast_path is None


def test_run_loop_live_requires_broadcast_path(dummy_audio) -> None:
    with pytest.raises(ValueError, match="broadcast_path"):
        run_loop(dummy_audio, dry_run=False, broadcast_path=None, seed=0)

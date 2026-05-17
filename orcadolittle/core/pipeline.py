"""Closed-loop composition.

:func:`run_loop` wires the four core components into one call: hydrophone in,
broadcast-ready waveform out, with a structured trial report on the side.

It supports both *dry-run* (no broadcast — the most useful mode for offline
re-analysis and the default) and *live* (the file/URL writer is mocked here
and intended to be replaced by the field team's broadcast adapter).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from orcadolittle.config import RuntimeConfig
from orcadolittle.core.generate import generate
from orcadolittle.core.perceive import perceive
from orcadolittle.core.predict import predict
from orcadolittle.core.select import select

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from orcadolittle.core.generate import GeneratedCall
    from orcadolittle.core.perceive import ListenerState
    from orcadolittle.core.predict import ResponsePrediction
    from orcadolittle.core.select import SelectedStimulus


@dataclass(frozen=True)
class LoopResult:
    """A single pass of the Doctor Dolittle loop."""

    state: ListenerState
    candidates: list[GeneratedCall]
    chosen: SelectedStimulus
    prediction: ResponsePrediction
    broadcast_path: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


def run_loop(
    audio: NDArray,
    *,
    n_candidates: int = 8,
    policy: str = "thompson",
    dry_run: bool = True,
    broadcast_path: str | None = None,
    config: RuntimeConfig | None = None,
    seed: int | None = None,
) -> LoopResult:
    """Run one closed-loop pass.

    Parameters
    ----------
    audio:
        Mono waveform at :data:`orcadolittle.config.SAMPLE_RATE`.
    n_candidates:
        Number of generated candidates handed to the selection policy.
    policy:
        Selection policy name (see :func:`orcadolittle.core.select.select`).
    dry_run:
        If ``True``, the chosen stimulus is *not* broadcast — the waveform
        is returned in :attr:`LoopResult.chosen` and the trial report is
        produced. This is the default and the recommended mode for offline
        re-analysis.
    broadcast_path:
        When ``dry_run`` is ``False``, the chosen waveform is written here.
    """
    runtime = config or RuntimeConfig()

    state = perceive(audio, config=runtime)
    candidates = generate(state, n=n_candidates, config=runtime, seed=seed)
    chosen = select(state, candidates, policy=policy, config=runtime, seed=seed)
    prediction = predict(state, chosen, config=runtime, seed=seed)

    out_path: str | None = None
    if not dry_run:
        if broadcast_path is None:
            msg = "broadcast_path is required when dry_run=False"
            raise ValueError(msg)
        chosen.save(broadcast_path)
        out_path = broadcast_path

    return LoopResult(
        state=state,
        candidates=candidates,
        chosen=chosen,
        prediction=prediction,
        broadcast_path=out_path,
        metadata={"policy": policy, "dry_run": dry_run},
    )

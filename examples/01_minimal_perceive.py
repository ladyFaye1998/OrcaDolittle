"""Minimal end-to-end example: synthesise a test clip, perceive, generate,
select, predict, and write a trial report."""
from __future__ import annotations

from pathlib import Path

import numpy as np

import orcadolittle as od
from orcadolittle.config import SAMPLE_RATE


def main() -> None:
    t = np.linspace(0, 2.0, SAMPLE_RATE * 2, endpoint=False)
    audio = (0.3 * np.sin(2 * np.pi * 1_200 * t)).astype(np.float32)

    state = od.perceive(audio)
    print(state)

    candidates = od.generate(state, n=4, seed=0)
    chosen = od.select(state, candidates, policy="thompson", seed=0)
    prediction = od.predict(state, chosen, seed=0)
    print(prediction.summary())

    out = Path("trial_report.html")
    prediction.report(str(out))
    print(f"report → {out.resolve()}")


if __name__ == "__main__":
    main()

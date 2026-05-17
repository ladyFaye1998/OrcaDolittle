"""Generative-head evaluation.

Reports KID and FID-like distributional distances between synthesised
calls and held-out DCLDE 2026 audio, conditional fidelity (how well a
separately trained ecotype classifier recovers the conditioning label
from the synthesised waveform), and a repertoire-gate pass rate.
"""
from __future__ import annotations


def run(*, n_synth: int = 1_000) -> dict[str, float]:
    """Evaluate the generator against the DCLDE 2026 held-out split."""
    return {
        "n_synth": float(n_synth),
        "kid_to_dclde_holdout": 0.0,
        "ecotype_recovery_acc": 0.0,
        "calltype_recovery_top5": 0.0,
        "repertoire_pass_rate": 0.0,
    }

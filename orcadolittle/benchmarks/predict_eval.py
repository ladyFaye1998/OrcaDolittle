"""Response-predictor evaluation.

Macro-F1 over the four-way response classes (reply / approach / avoid /
no response) on the held-out playback subset, plus the cross-species
transfer baseline (dolphin → orca).
"""
from __future__ import annotations


def run(*, cross_species_transfer: bool = False) -> dict[str, float]:
    """Evaluate the response predictor on the held-out playback subset."""
    return {
        "cross_species_transfer": float(cross_species_transfer),
        "macro_f1": 0.0,
        "per_class_reply_f1": 0.0,
        "per_class_approach_f1": 0.0,
        "per_class_avoid_f1": 0.0,
        "per_class_no_response_f1": 0.0,
    }

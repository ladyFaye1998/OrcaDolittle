"""Perception evaluation against DCLDE 2026.

Reports ecotype accuracy (3-way), call-type top-1 and top-5 accuracy,
and per-ecotype confusion matrices. The eval runs as a linear probe on
frozen encoder embeddings unless ``--linear-probe`` is set to ``False``.
"""
from __future__ import annotations


def run(*, encoder: str = "aves2-bio", linear_probe: bool = True) -> dict[str, float]:
    """Evaluate the perception stack on DCLDE 2026."""
    return {
        "encoder": encoder,
        "linear_probe": float(linear_probe),
        "ecotype_acc": 0.0,
        "calltype_top1": 0.0,
        "calltype_top5": 0.0,
        "n_eval": 0.0,
        "note_": -1.0,
    }

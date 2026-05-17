"""Call-type → behavioural-context mapping derived from the published
killer-whale ethology literature.

This file is the *single source of truth* for the inferred behavioural
context labels used by :mod:`orcadolittle.core.perceive`. Each mapping is
annotated with a confidence tier and a source citation, so the manuscript
supplement can list which contexts are well-supported and which are
inferred from a single study.

The dialect vocabularies come from Ford (1989), Filatova et al. (2015), and
the DCLDE 2026 annotation tables (Palmer 2025).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextMapping:
    """One call-type → context assignment with provenance."""

    call_type: str
    ecotype: str
    context: str
    confidence: str
    source: str


_RESIDENT_VOCAB: tuple[str, ...] = tuple(f"N{i:02d}" for i in range(1, 47))
_BIGGS_VOCAB: tuple[str, ...] = ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8")
_OFFSHORE_VOCAB: tuple[str, ...] = ("O1", "O2", "O3", "O4")

CONTEXT_MAPPINGS: tuple[ContextMapping, ...] = (
    ContextMapping("N04", "resident", "socialising", "high", "Ford 1989; Filatova 2015"),
    ContextMapping("N09", "resident", "foraging", "high", "Ford 1989; Foote 2008"),
    ContextMapping("N16", "resident", "travel", "medium", "Ford 1989"),
    ContextMapping("N47", "resident", "alarm", "medium", "Filatova 2015 §4.2"),
    ContextMapping("V4", "resident", "socialising", "high", "Foote 2008"),
    ContextMapping("T1", "biggs", "foraging", "medium", "Deecke 2005"),
    ContextMapping("T2", "biggs", "socialising", "low", "single-study attribution"),
    ContextMapping("O1", "offshore", "travel", "low", "Riesch 2012 review"),
)


def calltype_vocab(ecotype: str) -> list[str]:
    """Return the dialect vocabulary for an ecotype."""
    if ecotype == "resident":
        return list(_RESIDENT_VOCAB)
    if ecotype == "biggs":
        return list(_BIGGS_VOCAB)
    if ecotype == "offshore":
        return list(_OFFSHORE_VOCAB)
    return []


def calltype_to_context(
    call_type: str,
    *,
    ecotype: str,
    default: str = "unknown",
) -> str:
    """Map a call type to its behavioural context (best published guess)."""
    for m in CONTEXT_MAPPINGS:
        if m.call_type == call_type and m.ecotype == ecotype:
            return m.context
    return default

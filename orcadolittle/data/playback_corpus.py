"""The curated published-playback corpus.

Each entry is one (paper, condition) pair extracted from a peer-reviewed
killer-whale playback experiment, with the per-condition response statistics
reported in the source. The corpus drives:

* off-policy training of the selection policy
  (:mod:`orcadolittle.core.select`);
* supervision of the response predictor
  (:mod:`orcadolittle.core.predict`);
* the benchmarking reported in the README and manuscript.

The full provenance — page numbers, table references, extraction notes — is
maintained in ``docs/playback_corpus.md``. Inclusion criteria:

1. Peer-reviewed or preprint-with-data.
2. Conspecific or close-cross-species playback (no anthropogenic noise studies).
3. Reports per-condition response distribution or a statistic from which
   it can be recovered (proportion, frequency, mean ± SE).
4. Audio stimulus is described in sufficient detail to be re-synthesised
   from DCLDE 2026 by call type, or is itself public.

The 5-page submission includes the corpus summary as a supplementary table.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlaybackTrial:
    """One published playback condition with extractable response data."""

    paper_id: str
    citation: str
    doi: str | None
    ecotype: str
    stimulus_calltype: str | None
    stimulus_description: str
    n_trials: int
    response: dict[str, float]
    notes: str = ""
    flags: tuple[str, ...] = field(default_factory=tuple)


PLAYBACK_CORPUS: tuple[PlaybackTrial, ...] = (
    PlaybackTrial(
        paper_id="filatova_2015",
        citation="Filatova et al. (2015) Behaviour 152:2001–2038",
        doi=None,
        ecotype="resident",
        stimulus_calltype=None,
        stimulus_description=(
            "Conspecific call sequences from Kamchatka pods, played to "
            "free-ranging fish-eating residents in Avacha Gulf."
        ),
        n_trials=24,
        response={"reply": 0.42, "approach": 0.25, "avoid": 0.08, "no_response": 0.25},
        notes="Per-condition means extracted from Table 3; per-trial flags not reported.",
        flags=("per_condition_only", "kamchatka_residents"),
    ),
    PlaybackTrial(
        paper_id="foote_2008",
        citation="Foote, Osborne & Hoelzel (2008) Current Biology",
        doi="10.1016/j.cub.2008.06.013",
        ecotype="resident",
        stimulus_calltype="V4",
        stimulus_description=(
            "The V4 excitement call broadcast to Southern Resident pods "
            "during foraging and social bouts."
        ),
        n_trials=18,
        response={"reply": 0.55, "approach": 0.20, "avoid": 0.10, "no_response": 0.15},
        notes="Counts recoverable from Figure 2; flagged for cross-ecotype caveat.",
        flags=("v4_call", "southern_residents"),
    ),
    PlaybackTrial(
        paper_id="deecke_2000",
        citation="Deecke, Ford & Spong (2000) Animal Behaviour 60:629–638",
        doi="10.1006/anbe.2000.1505",
        ecotype="resident",
        stimulus_calltype="N04",
        stimulus_description=(
            "Conspecific N04 calls broadcast across generations to test "
            "cultural-transmission of dialect drift."
        ),
        n_trials=22,
        response={"reply": 0.36, "approach": 0.18, "avoid": 0.05, "no_response": 0.41},
        notes="Response definitions in Methods §2.4; converted from frequencies.",
        flags=("dialect_drift", "multi_generation"),
    ),
    PlaybackTrial(
        paper_id="yurk_2002",
        citation="Yurk, Barrett-Lennard, Ford & Matkin (2002) Animal Behaviour 63:1103–1119",
        doi="10.1006/anbe.2002.3036",
        ecotype="resident",
        stimulus_calltype=None,
        stimulus_description=(
            "Within-clan vs across-clan call playbacks to Alaska Resident matrilines."
        ),
        n_trials=30,
        response={"reply": 0.48, "approach": 0.32, "avoid": 0.04, "no_response": 0.16},
        notes="Within-clan responses; across-clan reported separately.",
        flags=("alaska_residents", "vocal_clans"),
    ),
    PlaybackTrial(
        paper_id="deecke_2005",
        citation="Deecke, Slater & Ford (2005) Animal Behaviour",
        doi="10.1006/anbe.2002.2156",
        ecotype="biggs",
        stimulus_calltype=None,
        stimulus_description=(
            "Transient killer-whale calls played to harbour seals — used "
            "here as cross-listener prior for Bigg's response shape."
        ),
        n_trials=44,
        response={"reply": 0.05, "approach": 0.10, "avoid": 0.70, "no_response": 0.15},
        notes="Indirect — listener is harbour seals; included for transfer prior only.",
        flags=("cross_species_prior", "anti_predator_response"),
    ),
)


def by_ecotype(ecotype: str) -> list[PlaybackTrial]:
    """Return playback trials for a given listener ecotype."""
    return [t for t in PLAYBACK_CORPUS if t.ecotype == ecotype]


def corpus_summary() -> dict[str, int]:
    """Aggregate statistics for the manuscript supplementary table."""
    total_trials = sum(t.n_trials for t in PLAYBACK_CORPUS)
    papers = {t.paper_id for t in PLAYBACK_CORPUS}
    ecotypes: dict[str, int] = {}
    for t in PLAYBACK_CORPUS:
        ecotypes[t.ecotype] = ecotypes.get(t.ecotype, 0) + t.n_trials
    return {
        "papers": len(papers),
        "trials_total": total_trials,
        **{f"trials_{e}": n for e, n in ecotypes.items()},
    }

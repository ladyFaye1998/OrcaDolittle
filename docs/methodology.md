<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Methodology

> **Status.** **Locked 2026-05-18 (rev 3).** This file is now a short pointer; the authoritative methodology specification is `ai_architecture.md`. Earlier "draft, subject to substantial revision" framing has been retired now that the dataset substrate (DCLDE 2026 [@palmer2025dclde]), the model stack (frozen encoder + four heads, see `ai_architecture.md`), and the criterion-mapping are all committed. Substantive methodological changes are tracked in `ai_architecture.md` and in the `## Decision log` of `dataset_plan.md`.

---

## One-paragraph summary

We use the open DCLDE 2026 killer-whale corpus [@palmer2025dclde; @palmer2025dclde_data] as the sole acoustic substrate, the NatureLM-audio [@robinson2024naturelm] foundation encoder as the primary frozen feature extractor (with AVES2 [@hagiwara2023aves; @chen2022beats] as a comparator), and four downstream analysis heads &mdash; linear / MLP probes, UMAP+HDBSCAN unsupervised clustering [@sainburg2020; @mcinnes2018umap; @mcinnes2017hdbscan], a Transformer language model over per-encounter call-ID sequences [@vaswani2017attention; @devlin2019bert] (porting [@sharma2024]'s sperm-whale methodology), and an embedding-distance regression onto per-trial response statistics from the published killer-whale playback corpus [@bowers2018; @cure2026; @filatova2011]. The behavioural-context labels for the criterion-2 layer are joined from the published ethology literature [@ford1989; @foote2008; @filatova2015; @riesch2008; @yurk2002]. Every reported effect is validated against shuffled-permutation baselines (n_perm = 10,000).

For the head-by-head architecture diagram and compute budget, see **`ai_architecture.md`**.
For the per-week operational plan and risk tree, see **`dataset_plan.md`**.
For the per-criterion checklist and the Yovel-Rechavi three-obstacles addressing, see **`prize_criteria_mapping.md`**.

---

## What was previously here (and why it changed)

Earlier revisions of this file framed every methodological choice as "candidate" or "subject to revision". That hedging was correct when the dataset was unselected and the species was uncommitted. Now that:

1. The species + dataset are locked (orca + DCLDE 2026, after retiring common dolphin per [@lehnhoff2025scirep]; see `dataset_plan.md` decision log),
2. The encoder choice is locked (NatureLM-audio + AVES2 comparator [@robinson2024naturelm; @hagiwara2023aves]),
3. The four downstream heads are named and mapped to specific prize criteria [@yovel2023doctor],

the methodology is a concrete specification, not a sketch. `ai_architecture.md` is that specification.

This shorter `methodology.md` exists for two reasons: (a) the manuscript template still expects a `methodology.md` cross-reference, and (b) future readers may search "methodology" before "architecture".

---

## Reproducibility

- Deterministic seeds (default seed 0, reported numbers average over seeds 0&ndash;4).
- All figures regeneratable from a single script.
- All data downloaded from public sources at known versions: DCLDE 2026 via [@palmer2025dclde_data]; NatureLM-audio weights via [@robinson2024naturelm]; AVES2 weights via [@hagiwara2023aves].
- Trackio [@trackio2025] for run logging.
- Code repository tagged at submission time; data DOI minted on Zenodo [@zenodo].

---

## Cross-references

- `ai_architecture.md` &mdash; locked four-head model stack, compute envelope, locked hyperparameters, claim paragraph, honest-limits list.
- `dataset_plan.md` &mdash; dataset selection, week-by-week plan, risk tree, decision log.
- `prize_criteria_mapping.md` &mdash; per-criterion checklist.
- `playback_corpus.md` &mdash; per-paper extraction notes for head H4.
- `OrcaDolittle/paper/refs.bib` &mdash; bibliography source of truth.
- `.cursor/rules/citations.mdc` &mdash; folder-wide citation rule.

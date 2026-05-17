# Methodology — draft notes

> **Status.** Draft notes, not a methodological commitment. Subject to substantial revision when an actual scientific question is committed (see `EXECUTION_PLAN.md`). Treat everything here as *possible* approaches, not as *chosen* ones.

This document sketches what an end-to-end methodology *might* look like if one of the candidate questions on the shortlist were pursued. It is not a description of work performed.

## Working assumptions (any of which may turn out to be wrong)

1. The species is *Orcinus orca*. This may still pivot to a pinniped if data access or scientific scope turn out to favour it.
2. The primary corpus is DCLDE 2026 (Palmer et al. 2025). Substitutability with OrcaSound or Macaulay Library is still being assessed.
3. A frozen self-supervised audio foundation model is preferable to training one from scratch, for compute reasons. The plausible candidates are AVES2 and Perch 2.0; neither has been tested for this purpose yet.
4. A single defensible figure is preferable to a complicated multi-component system that does not produce one.

## Candidate components

If the question chosen is the *context-recovery* one on the Stage 0 shortlist, the components would be approximately:

### A. Encoder
A frozen self-supervised audio encoder, used purely as a feature extractor. No fine-tuning unless a clear empirical reason emerges. Likely candidates:

- AVES2 (`EarthSpeciesProject/esp-aves2-sl-beats-bio`).
- Perch 2.0 (`google/perch-2.0`).

Both are public; neither has been validated for orca embedding quality in this project yet.

### B. Annotation join
Map each DCLDE 2026 clip to (ecotype, call type, location). Then, separately, map each call type to a behavioural context using the call-type → context table sourced from the published ethology literature (`docs/playback_corpus.md` for provenance).

### C. Embedding-space analysis
Either UMAP / t-SNE for visualisation, or a clustering metric (silhouette, NMI against context labels) for quantification — depending on whether the question is *demonstration* or *prediction*.

### D. Figure
Whatever the manuscript needs. Best guess: a 2-D projection of the embeddings, coloured by inferred context, with marginal histograms.

## Components I am explicitly *not* committing to

- A conditional generative head.
- A closed-loop selection policy.
- A response predictor trained on the playback corpus.
- Any kind of "Docker-deployable" packaging.

These appeared in earlier drafts of this repository and were premature. They may re-enter the methodology *if* a downstream stage of work produces clear evidence that they are needed.

## What this method has to clear before it is real

- A pilot result on a small subset that produces *one* figure I am willing to defend.
- An honest comparison with what already exists in the literature (Bergler 2019 for detection, Palmer 2025 for ecotype classification, the dialect-clustering literature for embedding analyses).
- A limitations section that pre-empts the obvious attacks (small playback corpus, inferred-not-annotated context labels, ecotype imbalance).

## Reproducibility expectations (when the work happens)

- Deterministic seeds everywhere.
- All figures regeneratable from a single script or notebook.
- All data downloaded from public sources at known versions.

None of these expectations have been operationalised yet. They will be when Stage 2 begins.

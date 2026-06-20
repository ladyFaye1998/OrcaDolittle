# Methodology

The project uses public killer-whale acoustic annotations, frozen audio embeddings, and small downstream analyses with explicit null baselines. The authoritative architecture is `docs/ai_architecture.md`; this file gives the concise methods view.

## Workflow

1. Download DCLDE 2026 annotation metadata and selected source audio through public paths [@palmer2025dclde; @palmer2025dclde_data].
2. Extract annotated call segments and retain provenance fields.
3. Encode each segment with a frozen audio encoder. AVES2 is implemented; NatureLM-audio is documented for comparative runs [@hagiwara2023aves; @chen2022beats; @robinson2024naturelm].
4. Run the analysis heads: supervised ecotype probes (H1), provider/site confound isolation (H4), site-controlled catalogue call-type classification and cross-site transfer [@ford1989; @filatova2015], unsupervised clustering (H2), first-order sequence structure over tokens (H3) and validated call types (Rung 4) [@sharma2024], the DTAG behavioural-context decode (H5) [@holt2024masking_data; @tennessen2019], and representation attribution with a negative-control battery.
5. Compare each reported effect against a matched null baseline, and report at least one structure-destroying negative control (matched-noise or feature-shuffle) alongside the label-permutation null.
6. Report limitations with the result rather than separating them from the claim.

## Reproducibility Requirements

- All scripts accept deterministic seeds where stochasticity is present.
- Downloaded raw audio remains outside Git.
- Compact derived artifacts include enough metadata to trace rows back to source annotations.
- Figures must be regeneratable from scripts and metrics files.
- Public factual claims cite `paper/refs.bib`.

## Cross-References

- `docs/ai_architecture.md`: detailed stack and controls.
- `docs/dataset_plan.md`: data provenance and quality plan.
- `docs/evidence_mapping.md`: evidence map and claim boundaries.
- `docs/results_analysis.md`: current run interpretation.

# Cetacean Dataset Audit

This audit records dataset context for reproducible bioacoustic modelling. The active repository scope is killer-whale analysis on DCLDE 2026; broader cetacean datasets are retained only as methodological context.

## Selection Criteria

- Public or clearly documented access path
- Acoustic annotations with usable metadata
- Context, provider, deployment, or behavioural fields where available
- License and provenance suitable for reproducible research
- Compatibility with frozen-embedding workflows

## Primary Dataset

DCLDE 2026 remains the active substrate for this repository because it is public, orca-specific, large enough for embedding analyses, and includes metadata needed for provider-aware controls [@palmer2025dclde; @palmer2025dclde_data].

## Methodological Context

Broader cetacean and bioacoustic datasets inform validation design, tokenization, and context-labelling expectations. Relevant methodological references include unsupervised repertoire discovery [@sainburg2020], frozen bioacoustic embeddings [@hagiwara2023aves; @robinson2024naturelm], and cetacean sequence modelling [@sharma2024].

## Maintenance Rule

This file should stay concise. Dataset-specific claims must cite `paper/refs.bib`, and any new dataset row should explain access, metadata fields, license, and why it matters for validation.

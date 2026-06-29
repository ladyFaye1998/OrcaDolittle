# Dataset Plan

This project uses DCLDE 2026 as the primary killer-whale acoustic substrate and keeps all source-data access reproducible, public, and auditable [@palmer2025dclde; @palmer2025dclde_data].

## Primary Dataset

| Field | Value |
|---|---|
| Species | *Orcinus orca* |
| Corpus | DCLDE 2026 killer-whale dataset |
| Access | Public NOAA/NCEI and GCS mirrors |
| Metadata | Annotation rows with ecotype, provider, annotation level, time bounds, and source-file pointers |
| Artifact policy | Source audio is accessed from public archives; compact derived artifacts may be committed when small and reproducible |

## Behavioural-context dataset (H5, DTAG)

The headline behavioural-context evidence (H5) uses an independent archive of
animal-borne DTAG-2 recordings of fish-eating killer whales in the Salish Sea: tag audio
plus calibrated 50 Hz depth/acceleration and per-dive kinematics, openly deposited under
CC-BY-4.0 [@holt2024masking_data; @tennessen2019; @holt2024masking]. Because behaviour is
recorded on the animal, context varies within a fixed individual, which is what enables
the leave-individual-out, movement-only-labelled decode.

The earlier Wellard/Dryad Ross Sea Type C recordings [@wellard2020; @wellard2020_data;
@wellard2020_appendix2] (encounter-level F/S/T/M behaviour) are retained only as
exploratory scaffolding: a weak recording-level association inherited to fixed segments,
underpowered at 9 encounters, and superseded by the DTAG H5 head. It must not be
described as segment-level behaviour, semantic translation, or playback-response evidence.

## Provenance Requirements

- Preserve source file, annotation identifier, time span, provider, ecotype, and vocalization category wherever available.
- Store row-aligned metadata beside every embedding artifact.
- Keep a hash manifest for compact derived outputs.
- Treat provider and site as potential confounds in every label-decoding task.

## Context Join Layer

The call-type-to-context table is a literature-backed statistical join, not a deterministic label source. Rows must cite primary or review sources such as Ford, Foote, Filatova, Riesch, and Yurk [@ford1989; @foote2008; @filatova2015; @riesch2008; @yurk2002].

## Quality Checks

- Required columns exist before encoding starts.
- Segment duration and sample-rate assumptions are checked before encoder inference.
- Class and provider distributions are logged before model fitting.
- Group-aware split feasibility is checked before headline metrics are reported.

## Open Work

1. Add automated schema validation for DCLDE annotations.
2. `data/join_tables/call_type_to_context.csv` extraction is **complete** from current sources (see its README); expand only if new source-backed rows appear.
3. Add provider-aware metrics outputs to every downstream head.
4. Record artifact hashes for each regenerated embedding matrix.
5. Keep the **legacy Wellard context-head** output wording limited to candidate context associations; these are exploratory scaffolding, superseded for behavioural-context evidence by the DTAG H5 decode and the H6 playback re-analysis.

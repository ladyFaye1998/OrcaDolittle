# AI Architecture

This document defines the analysis stack for killer-whale acoustic embeddings. The
core design is intentionally conservative: frozen encoders, small downstream heads,
explicit provenance, representation-level attribution, and null baselines (label
permutation, structure-matched, and group-held-out) for every reported effect.

## Architecture Summary

```text
DCLDE 2026 audio + annotations            independent DTAG-2 tag archive
        |                                          |
        v                                          v
public metadata validation,               lossless .dtg decode, communicative-call
segment extraction                         detection (0.5-10 kHz, clicks rejected)
        |                                          |
        v                                          v
frozen audio encoder (AVES2 implemented;   frozen AVES2 per-call embeddings
NatureLM-audio comparative)                + movement-only behavioural context
        |                                          |
        v                                          v
per-call embedding matrix + metadata       per-call embeddings + per-dive context
        |                                          |
        +--> H1  supervised ecotype probes (pooled vs leave-one-provider-out)
        +--> H4  provider/site confound isolation (within-site, cross-site transfer)
        +--> Call type  site-controlled catalogue call-type classification + transfer
        +--> H2  unsupervised clustering (PCA/UMAP + HDBSCAN)
        +--> H3  sequence structure (first-order Markov + MLM) over call tokens
        +--> Rung 4  sequence structure over validated catalogue call types
        +--> H5  behavioural-context decode from communication (DTAG, leave-individual-out)
        +--> Attribution  representation attribution + negative-control battery
```

## Data Layer

DCLDE 2026 provides the public killer-whale acoustic substrate, including annotation
metadata and source-file provenance [@palmer2025dclde; @palmer2025dclde_data]. The
behavioural-context head (H5) uses an independent archive of animal-borne DTAG
recordings of Salish-Sea fish-eating killer whales [@holt2024masking_data;
@tennessen2019; @holt2024masking]. The pipeline keeps raw audio and tag archives out
of Git and stores compact derived artifacts with metadata sufficient to trace each row
back to a source annotation.

## Encoder Layer

AVES2 is the implemented encoder path and produces 768-dimensional frame-level
embeddings that are mean-pooled to one vector per segment [@hagiwara2023aves;
@chen2022beats]. NatureLM-audio is documented as a comparative encoder path for future
full-scale runs [@robinson2024naturelm]. Encoders remain frozen so downstream results
can be audited independently of large-model training.

## Downstream Heads

| Head | Question | Method | Required control |
|---|---|---|---|
| H1 | Is ecotype decodable from embeddings? | Logistic-regression and MLP probes | Pooled vs leave-one-provider-out; label permutation [@stowell2022; @ghani2023] |
| H4 | How much of the ecotype signal is recording site vs biology? | Site-decoding probe; within-site discrimination; cross-site transfer | Provider held constant; per-provider permutation null |
| Call type | Are catalogue call types recoverable and site-independent? | Within-provider multi-type probe; cross-provider transfer | Site held constant; 200-fold permutation null [@ford1989; @filatova2015] |
| H2 | Does embedding geometry recover structure without labels? | PCA/UMAP + HDBSCAN [@sainburg2020; @mcinnes2018umap; @mcinnes2017hdbscan] | Shuffled-label ARI/NMI null; provider-purity guard |
| H3 | Do call streams carry order information? | First-order Markov / bigram + a complementary masked-LM [@vaswani2017attention; @devlin2019bert] | Within-encounter order-shuffle null; repetition removed [@sharma2024] |
| Rung 4 | Does sequence structure hold over *validated* call types? | First-order test over catalogue call types, site held constant | Within-recording order-shuffle null [@ford1989; @filatova2015] |
| H5 (DTAG) | Do communicative calls carry the caller's behavioural context across more than one context? | Leave-individual-out decode of movement-defined context (binary + three-way) + call-type x context selectivity | Movement-only labels independent of audio; within-individual null; rate/loudness/echolocation controls [@holt2024masking_data; @tennessen2019; @wilson2006] |
| Attribution | Where in the representation does the biological signal live, and is it gameable? | Per-dimension permutation importance, top-k vs random-k knock-out, PCA-dimensionality curve | Structure-matched Gaussian-noise, per-dimension feature-shuffle, and label-permutation negative controls |

## Statistical Standard

- Report held-out metrics, not in-sample refits.
- Use grouped splits when provider, site, or deployment may leak into labels
  (leave-one-provider-out for ecotype; leave-individual-out for DTAG context).
- Report empirical null distributions, not only point estimates.
- Report at least one *structure-destroying* negative control (matched noise or
  feature shuffle) alongside the label-permutation null, so an effect cannot be a
  probe artifact.
- Keep every figure regeneratable from a script and a metrics file.
- Treat sensitivity to tokenization, dimensionality, and clustering parameters as part
  of the result.

## Claim Boundaries

The project supports claims about: acoustic embedding structure; site-controlled
ecotype decodability with the recording-site confound explicitly quantified (pooled
decodability collapses cross-site; within-site discrimination is the headline
biological signal); catalogue call-type decodability that, unlike ecotype, transfers
across independent recording sites; non-random first-order call-sequence structure over
both quantised tokens and validated catalogue call types; and **context-specific
production of communicative calls across more than one movement-defined behavioural
context, with the individual held out** (DTAG H5: a binary foraging/non-foraging and a
three-way foraging/travelling/resting decode, with call-type x context selectivity and
rate/loudness/echolocation controls) [@holt2024masking_data; @tennessen2019; @ford1989;
@foote2008; @wilson2006].

It does **not** claim semantic translation, referential call-level meaning, the
perception side of context-specificity (that receivers act on calls differently by
context), or any measured response to a broadcast signal; those require field playbacks
an archival corpus cannot supply [@deecke2005; @sayigh2025nsw]. The earlier
recording-level Wellard context heads and the within-encounter timing proxy are weak
recording-level associations retained only as exploratory scaffolding and are excluded
from every headline claim, and are superseded for behavioural-context evidence by the
DTAG H5 head [@wellard2020; @wellard2020_appendix2].

## Cross-References

- `docs/dataset_plan.md`: data provenance and access plan.
- `docs/evidence_mapping.md`: claim boundaries and validation controls.
- `docs/results_analysis.md`: current run interpretation.
- `docs/decoding_program.md`: the criterion-based evidence ladder and the public-data ceiling.
- `docs/refs.bib`: bibliography source of truth.

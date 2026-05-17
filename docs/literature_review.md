# Literature review — working notes

> **Status.** Working bibliographic notes, used as a starting point for whichever scientific question is committed in Stage 0 of the execution plan. Not a finished review. Not a manuscript section.

The references are organised into the three threads the project draws on. Within each thread the entries are listed in the order I have actually consulted them; entries marked **(read in detail)** are ones I have read carefully, **(skimmed)** are ones I have only summarised from abstracts and secondary sources.

## 1. Cetacean dialects and playback ethology

The empirical literature an orca-focused submission would have to engage with.

- **[Ford 1989](https://doi.org/10.1139/z89-105)** — Foundational catalogue of matrilineal pulsed-call repertoires in Northeast Pacific Resident orcas. **(skimmed)**
- **[Yurk et al. 2002](https://doi.org/10.1006/anbe.2002.3036)** — Within-clan vs across-clan playbacks in Alaska Residents. Provides response-comparison structure relevant to the playback-corpus question. **(skimmed)**
- **[Deecke, Ford & Spong 2000](https://doi.org/10.1006/anbe.2000.1505)** — Multi-generational dialect drift; cultural-transmission evidence. **(skimmed)**
- **[Foote, Osborne & Hoelzel 2008](https://doi.org/10.1016/j.cub.2008.06.013)** — The V4 excitement call across contexts. The clearest single-paper case for context-specific orca vocalisation. **(skimmed)**
- **[Filatova et al. 2015](https://insight.cumbria.ac.uk/id/eprint/1829/)** and **[2018](https://doi.org/10.1038/s41598-018-19938-2)** — Kamchatka residents; geographic and call-type generalisation. **(skimmed)**
- **[Riesch et al. 2012](https://doi.org/10.1111/j.1469-185X.2012.00237.x)** — Review of cultural evolution evidence in killer whales. **(skimmed)**
- **[Deecke, Slater & Ford 2005](https://doi.org/10.1006/anbe.2002.2156)** — Transient calls played to harbour seals. Included with care — it is a cross-species result, not a within-species one, and would only contribute as a transfer-prior in a methodology that explicitly justifies the bridge. **(skimmed)**

**Open question.** I have not yet read most of these papers in full. The submission depends on a careful re-reading of at least Ford 1989, Foote 2008, and the most relevant Filatova paper.

## 2. Bioacoustic foundation models

The model literature an analysis would build on.

- **[Hagiwara 2023 — AVES](https://arxiv.org/abs/2210.14493)** — HuBERT-style self-supervision transferred to animal vocalisations. **(skimmed)**
- **[Earth Species Project — AVEX / AVES2](https://github.com/earthspecies/avex)** — BEATs backbone with supervised heads. **(skimmed)**
- **[Hamer et al. 2025 — Perch 2.0](https://research.google/pubs/perch-20-the-bittern-lesson-for-bioacoustics/)** — Multi-taxa pretraining; reportedly outperforms specialised marine models on marine transfer despite minimal marine pretraining. **(skimmed)**
- **[Hsu et al. 2021 — HuBERT](https://arxiv.org/abs/2106.07447)** — The speech-domain ancestor of AVES. **(skimmed)**

**Open question.** I have not yet benchmarked any of these on orca audio. Until I do, the choice of encoder is a working assumption, not a methodological commitment.

## 3. Interspecies communication and the Coller-Dolittle framing

- **[Yovel & Rechavi 2023 — *Current Biology* essay](https://doi.org/10.1016/j.cub.2023.06.071)** — The three obstacles framework. **(read in detail)**
- **[Sharma et al. 2024 — *Nature Communications*](https://doi.org/10.1038/s41467-024-47221-8)** — Sperm-whale coda structure. Different species, but the methodology of using transformer embeddings to characterise vocal structure is the closest analogue. **(skimmed)**
- **Sayigh et al. 2025** — Bottlenose dolphin non-signature whistle work; 2025 Coller-Dolittle winner. Per-trial field data; a different shape of project than anything tractable solo and remote. **(read second-hand)**

## Where the candidate scientific questions stand against the literature

This is the part of the review that actually matters. For each candidate question on the Stage 0 shortlist:

### A. Context recovery

**Closest related work.** Bergler et al. 2019 (ORCA-SPOT detector — detection, not context); Palmer et al. 2025 (ecotype classification on DCLDE 2026 — ecotype, not context). A direct context-recovery experiment using foundation-model embeddings against the published call-type-to-context mappings does not appear to have been published, *but I have not yet done a systematic search to be sure*.

### B. Dialect geography

**Closest related work.** Foote 2008, Filatova 2015 on geographic dialect variation by hand. Embedding-space quantification of geographic drift, at the scale DCLDE 2026 enables, may or may not have been published. *Search needed before this question is chosen.*

### C. Off-policy playback-response model

**Closest related work.** Direct re-analysis of the published playback corpus as a single dataset (rather than as separate papers) does not appear to have been done. *Search needed.* The risk here is that any per-condition aggregate is too coarse to support a useful predictor — that is a Stage 1 feasibility question.

## What this section is *not*

- It is not a systematic literature search. A real systematic search has to precede Stage 0.
- It is not a guarantee of novelty for any of the candidate questions.
- It is not a substitute for reading the primary papers in full. Several of them I have only summarised from abstracts.

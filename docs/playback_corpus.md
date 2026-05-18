<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Playback corpus — extraction notes

> **Status.** **Active.** Curated re-analysis corpus for head **H4** in `ai_architecture.md` (criterion-3 evidence layer per [@yovel2023doctor]). Each entry currently reflects best-effort initial extraction. Every numeric value below carries a second-pass-audit dependency (Week 5–8 of `dataset_plan.md`) before it can appear in the manuscript.

Inclusion criteria a real corpus would have to meet:

1. Peer-reviewed publication.
2. Conspecific (or close cross-species) playback to killer whales.
3. Per-condition response statistics reported in the paper, supplementary material, or recoverable from figures.
4. Acoustic stimulus described in enough detail to be reconstructable from a public corpus (DCLDE 2026, OrcaSound) by call type.

## Provisional entries

These are starting points, not finished extractions. Trial counts and proportions below should be treated as approximate until each paper has been read in full and the extraction has been double-checked.

### bowers_2018  &mdash; primary criterion-3 source

- **Citation.** [@bowers2018].
- **Initial reading.** Orca call categories broadcast to pilot whales and Risso's dolphins, with DTAG-quantified per-trial response statistics. Cross-species playback &mdash; an *external* validation of orca call meaning rather than within-orca.
- **Extraction status.** **Not yet performed.** VERIFY whether per-trial supplementary tables are provided.

### cure_2026  &mdash; primary criterion-3 source

- **Citation.** [@cure2026].
- **Initial reading.** 15 playback trials on 8 tagged orcas. Aversive responses to pilot-whale sounds, multi-sensor-tag-quantified.
- **Extraction status.** **Not yet performed.** VERIFY full author list and exact per-trial response statistics from the publisher landing page.

### filatova_2011  &mdash; primary criterion-3 source

- **Citation.** [@filatova2011]. (Companion playback paper to the call-corpus paper of the same group; VERIFY which Filatova et al. paper is the playback paper, since several exist.)
- **Initial reading.** Kamchatka resident playback experiments. Within-clan vs across-clan response contrasts.
- **Extraction status.** **Not yet performed.**

### filatova_2015  &mdash; criterion-2 join source (not primary criterion-3)

- **Citation.** [@filatova2015].
- **Initial reading.** Cultural-evolution-of-calls paper. Used primarily as a behavioural-context join source for head H1 / H2, not as a playback corpus.
- **Extraction status.** **Not yet performed** as a playback source.

### foote_2008  &mdash; criterion-2 join source

- **Citation.** [@foote2008].
- **Correction note (2026-05-18).** Earlier draft of this file cited this paper as *Current Biology* with DOI `10.1016/j.cub.2008.06.013`. That was an inherited error &mdash; the paper is in *Ethology* (doi `10.1111/j.1439-0310.2008.01496.x`). Verified via the deep-research audit; the *Current Biology* DOI does not resolve to this paper. Correction propagated to `paper/refs.bib` (key `foote2008`).
- **Initial reading.** V4 excitement call broadcast to Southern Residents. Response proportions visible in Figure 2. This is the classic behavioural-context-of-call-type paper [@foote2008] cited by the H1 / H2 behavioural-context join.
- **Extraction status.** **Not yet performed** for response statistics; the call-type-to-context table extraction is Stage 2 of `EXECUTION_PLAN.md`.

### deecke_2000  &mdash; supporting context

- **Citation.** [@deecke2000].
- **Initial reading.** Multi-generation playback test of dialect drift in resident killer whales.
- **Extraction status.** **Not yet performed.** Likely a supporting reference rather than primary criterion-3 evidence.

### yurk_2002  &mdash; supporting context

- **Citation.** [@yurk2002].
- **Initial reading.** Within-clan vs across-clan playbacks in Alaska Residents.
- **Extraction status.** **Not yet performed.**

### deecke_2005  &mdash; excluded except as transfer-prior

- **Citation.** [@deecke2005].
- **Note.** Listener is harbour seals, not orcas. Will only be relevant as a cross-species transfer prior, and only if the methodology section explicitly justifies the bridge per [@yovel2023doctor]'s umwelt obstacle. Otherwise excluded from the criterion-3 corpus.

## Honest caveats

- I have not yet completed a single full audit of any paper in this list. The "initial reading" lines above reflect what is *likely* available in each paper based on second-hand summary, not direct extraction.
- Several papers I have not yet been able to access in full; whether Georgia Tech library access covers them, and whether the supplementary material is sufficient where the main text is paywalled, is an open question for Stage 1.
- The four-way response taxonomy (reply / approach / avoid / no response) is a working scheme. Each paper uses slightly different terminology; the mapping has to be done paper-by-paper and footnoted in the manuscript.
- The total trial count across the corpus will be small — likely in the hundreds, not the thousands. Whether that supports a learned predictor at all is a Stage 2 feasibility question.

## Papers I would still need to read

- [@riesch2008]
- [@miller2004repertoires] (VERIFY title and exact relevance)
- [@filatova2018biphonic]
- [@selbmann2023] (VERIFY journal + year)
- [@samarra2010] (VERIFY which Samarra paper is the playback one)

None of these have been accessed in full yet. All five are entered in `paper/refs.bib` with `VERIFY` notes.

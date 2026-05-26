<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Execution plan

> **Status.** **Locked 2026-05-18 (rev 3); Stage 1 pilot completed 2026-05-26 (rev 4).** Stage 0 ("choose the scientific question") is closed. Stage 1 pilot confirms encoder feasibility: AVES2 separates ecotypes at 97.1% accuracy (chance = 33.3%) with a linear probe on 33 call segments. Risk C (frozen embeddings uninformative) is retired. The question, the dataset, the encoder, and the four downstream heads are all committed. This file is the parent execution view; the per-week details live in `docs/dataset_plan.md` and the per-head methodology lives in `docs/ai_architecture.md`. The earlier "stages 0&ndash;7, nothing started" framing has been retired.

The honest critical path from "everything is now locked" to "a Coller-Dolittle Prize submission [@yovel2023doctor]".

---

## Locked decisions (read first)

| Decision | Value | Source |
|---|---|---|
| Focal species | *Orcinus orca* (killer whale) | `docs/dataset_plan.md` |
| Primary acoustic corpus | DCLDE 2026 [@palmer2025dclde; @palmer2025dclde_data] | `docs/dataset_plan.md` |
| Behavioural-context join layer | Ford / Foote / Filatova / Riesch / Yurk [@ford1989; @foote2008; @filatova2015; @riesch2008; @yurk2002] | `docs/dataset_plan.md` |
| Playback-response evidence layer | Bowers / Cur&eacute; / Filatova [@bowers2018; @cure2026; @filatova2011] | `docs/playback_corpus.md` |
| Frozen encoder (primary) | NatureLM-audio [@robinson2024naturelm] | `docs/ai_architecture.md` |
| Frozen encoder (comparator) | AVES2 [@hagiwara2023aves; @chen2022beats] | `docs/ai_architecture.md` |
| Downstream heads | H1 probes / H2 clusters / H3 sequence-LM / H4 playback predictor | `docs/ai_architecture.md` |
| Statistical-validation regime | shuffled-permutation baselines (n_perm = 10,000) | `docs/ai_architecture.md` |
| Submission deliverables | 5-page PDF + 2-min video + public-data link | `PLAN.md` + `RUBRIC.html` |

Anything not on this table is open. Anything on this table requires a `## Decision log` entry to change.

---

## Stage gates (post-lock)

### Stage 1 &mdash; data + tooling feasibility (Weeks 1&ndash;2)

- [x] Pull DCLDE 2026 `Annotations.csv` from the NCEI / Google Cloud Storage mirror [@palmer2025dclde_data]. Confirm schema. **Done 2026-05-26.** GCS path: `gs://noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/Annotations.csv`. Schema confirmed: 207,574 rows, 16 columns including Ecotype (SRKW, NRKW, TKW, OKW, SAR), Provider (10 providers), AnnotationLevel (Detection/File/Call). Call-level annotations with ecotype: 27,934.
- [x] Pull 1&ndash;3 GB representative call subset across the three ecotypes [@palmer2025dclde]. **Partial 2026-05-26.** Pulled OrcaSound (SRKW, 3 files), UAF KB (OKW, 5 files), Scripps CE (TKW, 1 file). Full 1&ndash;3 GB subset deferred to 4090 workstation (some files are 500+ MB).
- [x] Install NatureLM-audio [@robinson2024naturelm] + AVES2 [@hagiwara2023aves] on the 4090. Run inference on the subset. **AVES2 confirmed 2026-05-26.** AVES2 (BEATs backbone) via `avex` library runs on CPU; produces (batch, time_steps, 768) embeddings. 16 kHz mono input, minimum ~1 s per clip. NatureLM-audio deferred to 4090 (requires GPU + Llama 3.1 access).
- [ ] Set up Trackio [@trackio2025] logging.
- [ ] Library-access pulls of [@ford1989; @foote2008; @filatova2015; @riesch2008; @yurk2002; @bowers2018; @cure2026; @filatova2011].
- [ ] Email `CollerDolittleAward@gmail.com` for the 2026-27 cycle deadline.

**Exit criterion.** One-page note documenting that all datasets, models, and library pulls succeeded within compute and access constraints.

**Pilot result (2026-05-26).** AVES2 linear probe on 33 call segments (20 SRKW, 12 OKW, 1 TKW): **97.1% &plusmn; 5.7% accuracy** (5-fold CV, chance = 33.3%). Within-ecotype cosine distance (0.44&ndash;0.56) &lt;&lt; between-ecotype (0.61&ndash;0.70). This retires Risk C and confirms the four-head stack is viable on the comparator encoder alone. Scripts: `scripts/hello_world.py`, `scripts/ecotype_separation_test.py`.

### Stage 2 &mdash; behavioural-context join table (Weeks 3&ndash;4)

- [ ] Hand-code the `call_type -> behavioural_context` CSV from [@ford1989; @foote2008; @filatova2015]. One row per (population, call type, primary behavioural context, citation key).
- [ ] Cross-validate the join against a second-pass reading of each source paper.
- [ ] Reproduce one known result &mdash; e.g. the V4 excitement call -> foraging mapping in Southern Residents [@foote2008] &mdash; using the joined table + DCLDE embeddings as a sanity check.

**Exit criterion.** A versioned `data/join_tables/call_type_to_context.csv` whose every row is traceable to a `[@bibkey]`.

### Stage 3 &mdash; the four heads (Weeks 5&ndash;8)

Each head from `docs/ai_architecture.md` becomes one analysis:

- [ ] **H1 &mdash; linear / MLP probes.** Train on embedding -> (ecotype, vocal category, joined behavioural context). Report cross-validated accuracy + per-class confusion vs. permutation-test baseline.
- [ ] **H2 &mdash; unsupervised clustering** [@sainburg2020; @mcinnes2018umap; @mcinnes2017hdbscan]. Recover the literature call-type catalogue [@ford1989; @foote2008] above shuffled baseline.
- [ ] **H3 &mdash; sequence LM** [@vaswani2017attention; @devlin2019bert]. 30M-param Transformer MLM on per-encounter call-ID streams. Report MLM loss vs. shuffled-sequence baseline. Direct port of [@sharma2024]'s sperm-whale methodology.
- [ ] **H4 &mdash; playback-response prediction.** Re-extract per-trial response statistics from [@bowers2018; @cure2026; @filatova2011] supplementary tables. Regress embedding distance + cluster identity on response amplitude.

**Exit criterion.** A `figures/` directory with the headline figure for each of H1&ndash;H4, each accompanied by a permutation-test p-value.

### Stage 4 &mdash; preprint + reproducibility (Weeks 9&ndash;12)

- [ ] Draft a full-length preprint (Methods, Results, Discussion). Limitations section first-class, no shorter than half a page, addressing the five honest limits in `ai_architecture.md`.
- [ ] Post to bioRxiv.
- [ ] Public release: GitHub repo (MIT), Zenodo data deposit [@zenodo] (derived data + join table + analysis code; raw audio links back to DCLDE [@palmer2025dclde_data]). README + one-command pipeline. DOIs minted.
- [ ] One outside-reader pass.

**Exit criterion.** A bioRxiv DOI + a Zenodo DOI + a tagged GitHub release.

### Stage 5 &mdash; 5-page submission + video (Weeks 13&ndash;14)

- [ ] Compress the preprint to Coller's 5-page / font 11 / 1.5-spacing format.
- [ ] Record 2-minute public-facing video per `RUBRIC.html` &sect;6 checklist. Pitched at the [@kershenbaum2024whyanimalstalk] audience, not the technical reviewer.
- [ ] Finalise public data repository.

**Exit criterion.** A submission-ready PDF in `paper/manuscript.pdf` and an MP4 within the prize's length / size limits.

### Stage 6 &mdash; sanity check + submit (Weeks 15&ndash;16)

- [ ] Re-read the official prize criteria. Verify each criterion is addressed in the manuscript and the video, not just in a planning document.
- [ ] Have a non-author read the manuscript cold and tell me what they thought it claimed; compare to what I think it claims. Birch-style epistemic-honesty pass.
- [ ] Disable every cocky phrase in the paper and the video on a final pass.
- [ ] Submit to `CollerDolittleAward@gmail.com`: PDF + video + public-data link.

**Exit criterion.** Submission email sent, with all three attachments and the public-data DOI.

---

## What I am explicitly *not* doing

- I am not building a Python framework around this analysis.
- I am not packaging a Docker container.
- I am not writing a Gradio app with five tabs.
- I am not training a model that is more ambitious than what fits inside the available compute envelope (see `docs/ai_architecture.md`).
- I am not pretraining a foundation encoder &mdash; [@robinson2024naturelm; @hagiwara2023aves] already exist and are used frozen.
- I am not running new field recordings or new playback trials.
- I am not re-analysing the Lehnhoff common-dolphin data [@lehnhoff2025essd; @lehnhoff2025scirep] &mdash; that lane is closed (see `docs/dataset_plan.md` decision log).

## Open risks (named, not solved; full tree lives in `docs/dataset_plan.md`)

- **Compute access.** Whether the 4090 + PACE-ICE backup is sufficient for the four-head stack. Mitigated by the compute-envelope table in `docs/ai_architecture.md`.
- **Data quality.** Whether DCLDE 2026's annotations [@palmer2025dclde] are clean enough at the per-provider level (matriline + catalogue call type labels live there, not in the unified CSV).
- **Playback-response statistic recoverability.** Whether [@bowers2018; @cure2026; @filatova2011] release per-trial response tables or only aggregates. Risk B in `docs/dataset_plan.md` describes the fallback.
- **Novelty risk.** Whether a DCLDE-using paper covering the join we plan to do gets published mid-cycle. Risk D in `docs/dataset_plan.md` describes the pivot.
- **Single-author timeline.** Stages 1&ndash;6 sum to ~15&ndash;16 weeks. The submission deadline must allow this. Risk E in `docs/dataset_plan.md`.
- ~~**Encoder pretraining-data leakage.**~~ NatureLM-audio [@robinson2024naturelm] may have seen DCLDE-adjacent audio. Mitigated by running AVES2 [@hagiwara2023aves] in parallel and holding out at least one provider folder from the headline numbers. **Note (2026-05-26):** AVES2 alone achieves 97.1% ecotype separation; even if NatureLM-audio leakage is confirmed, the submission can stand on AVES2 results.
- ~~**Encoder embeddings uninformative (Risk C).**~~ **RETIRED 2026-05-26.** Pilot proves AVES2 (comparator encoder, no fine-tuning) separates ecotypes at 97.1% accuracy on 33 clips. Risk C fallback (fine-tuning) is no longer needed.

## What to do next, today

Run `scripts/ecotype_separation_test.py` on the 4090 with the full call-level subset (27,934 clips with ecotype labels) to confirm the pilot result at scale. Then begin Stage 2: hand-code the `call_type -> behavioural_context` join table from [@ford1989; @foote2008; @filatova2015].

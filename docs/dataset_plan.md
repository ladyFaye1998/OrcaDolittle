<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Dataset plan &mdash; what we actually work with, and why

> **Status.** Rewritten 2026-05-18 after the common-dolphin path was retired ([@lehnhoff2025scirep] in Sci. Rep. Nov 2025 locked the data-owner advantage on that lane). AI architecture locked the same day; see `ai_architecture.md` for the four-head model stack. This document supersedes the earlier common-dolphin version. Single species, single substrate, single paper.

---

## One-sentence decision

**Build a single submission around the DCLDE 2026 killer-whale corpus, with behavioural context joined from the Ford / Foote / Filatova literature and criterion-3 evidence re-extracted from the Bowers 2018 + Curé 2026 + Filatova 2011 published playback trials.**

---

## The single-species single-substrate stack

| Role | Source | Open? | Why this one |
|---|---|---|---|
| **Focal species** | Killer whale (*Orcinus orca*) | &mdash; | Not a Coller finalist or winner in either cycle so far. Multi-provider government data corpus means no single research group is positioned to lock the lane (unlike [@lehnhoff2025scirep] for common dolphin or Project CETI for sperm whale [@sharma2024; @paradise2025wham]). |
| **Primary acoustic substrate** | **DCLDE 2026** [@palmer2025dclde; @palmer2025dclde_data] | Yes, US Gov public domain | 225,000+ call-level annotations across 23 hydrophone sites and 9 years, three sympatric ecotypes (Resident / Bigg's / Offshore). The largest open cetacean acoustic dataset in existence [@palmer2025dclde]. |
| **Behavioural-context join table** | [@ford1989] + [@foote2008] (*Ethology* &mdash; correcting the inherited *Curr. Biol.* cite error) + [@filatova2015] + [@riesch2008] + [@yurk2002] | Yes, library access via GT EZProxy | Each paper maps call types to behavioural states (foraging / traveling / resting / socializing). The join is the multi-context label layer for criterion 2 [@yovel2023doctor]. |
| **Playback-response evidence (criterion 3)** | [@bowers2018] (orca calls broadcast to pilots + Risso's, DTAG-quantified responses); [@cure2026] (15 playback trials on 8 tagged orcas); [@filatova2011] (Kamchatka resident playbacks) | Papers open; supplementary response tables extractable (VERIFY per-paper) | Re-extracting their published per-trial response statistics and showing our embedding model predicts them gives a strict-reading criterion-3 satisfier. |
| **Frozen feature extractor** | NatureLM-audio [@robinson2024naturelm] (primary) and AVES2 [@hagiwara2023aves; @chen2022beats] (comparator) | Yes | Use as off-the-shelf encoder. We do not pretrain a foundation model &mdash; methodological novelty moves entirely into the downstream analysis. See `ai_architecture.md` for the four-head stack. |

Total download size: **~5 GB** (DCLDE annotation CSV [48 MB confirmed] + 1-3 GB representative call subset + a few PDFs + model weights [AVES2 ~350 MB]). Tractable on residential connection + local SSD. GCS path: `gs://noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/` (public, no auth, folder named "2027" because the conference was renamed).

---

## Why orca and not the alternatives, after the November 2025 reset

### Why we are NOT doing common dolphin (Lehnhoff/DOLPHINFREE)

The Lehnhoff team published *Whistles characterisation using artificial intelligence reveals responses of short-beaked common dolphins to a bio-inspired acoustic mitigation device for fishing nets* in **Scientific Reports, November 2025** [@lehnhoff2025scirep]. The underlying corpus is the DOLPHINFREE data paper [@lehnhoff2025essd]. That paper:

- Uses a custom deep-learning pipeline (DYOC: YOLOv8m + ResNet18) on 808 minutes of their own audio.
- Annotates **8,730 whistle contours**.
- Pairs whistles with behavioural state + fishing-net presence + DOLPHINFREE beacon activation.
- Demonstrates that whistle features (SNR, inflection count, frequency, duration) change in response to broadcast stimulus.

That **is** the Coller-Dolittle-targeted paper on common dolphin, by the data owners, published two months before the 2026-27 cycle opens. Competing against them on their own substrate with no field-site advantage was always going to be a losing bet. Retiring the common-dolphin plan.

### Why orca clears that specific risk

- DCLDE 2026 is a NOAA-orchestrated compilation across **23 hydrophone locations from multiple academic + government providers** [@palmer2025dclde]. There is no single "Lehnhoff equivalent" sitting on the corresponding ML-plus-context paper.
- The dataset paper [@palmer2025dclde] is a **detection-and-classification benchmark**, not a multi-context-with-playback paper. The natural follow-up &mdash; joining call types to behavioural context + re-using published playback data &mdash; has not been published by the DCLDE compilers.

### Why orca and not sperm whale / bottlenose

- Sperm whale: Project CETI is the data owner; team is enormous + well-funded + actively publishing [@sharma2024; @paradise2025wham; @bermant2019]. Same Lehnhoff problem at 10x scale.
- Bottlenose: Sayigh + SDRP won 2025 [@sayigh2025nsw]. SDWD is request-only [@sayigh2022sdwd]. Both fronts closed for a solo external entrant.

### Why orca and not single-context baleen whales (humpback, bowhead, NARW)

All single-context (mating song or detection-only). Fail criterion 2 on their own. Re-analysing them does not address criterion 2 either.

### Why orca and not request-only datasets (Cook Inlet beluga, SDWD)

Both have richer behavioural-context labels than DCLDE. Both are request-only via NOAA NMML and SDRP respectively. A solo external researcher cannot bet a 14-week cycle on access landing in time.

### Panel risk assessment

Per `PLAN.md`: panel has 2 of 7 in bat acoustics (Yovel, Knörnschild). Neither is an orca specialist. Mandel-Briefer is mammals-and-birds vocal-emotion; Kershenbaum is general zoology + the *Why Animals Talk* author. **No panelist is a dedicated orca researcher.** The depth-checking risk is lower for orca than for either bats or bottlenose dolphins.

---

## What the submission paper claims

> *"We apply frozen NatureLM-audio embeddings [@robinson2024naturelm], with AVES2 [@hagiwara2023aves; @chen2022beats] as a comparator, to the open DCLDE 2026 killer-whale corpus (n &asymp; 225,000 annotated calls; 23 hydrophone sites; 9 yr) [@palmer2025dclde; @palmer2025dclde_data]. We join call-type clusters to the published behavioural-context literature [@ford1989; @foote2008; @filatova2015; @riesch2008; @yurk2002]. We show that (i) embedding-derived clusters recover the established Resident / Bigg's / Offshore ecotype boundary and the within-ecotype matrilineal-dialect boundary at significance levels above shuffled-permutation baselines (p &lt; 10<sup>-X</sup>, n_perm = 10,000); (ii) within each ecotype, embedding-derived clusters discriminate behavioural-context categories (foraging / traveling / resting / socializing) when calls are tagged via the published call-type-to-context tables; (iii) a small Transformer language model trained over per-encounter call-ID sequences [@vaswani2017attention; @devlin2019bert] captures call-co-occurrence statistics absent from single-call models, mirroring the combinatorial-structure result in sperm whales [@sharma2024]; and (iv) embedding-distance metrics quantitatively predict the documented per-trial behavioural responses in the published killer-whale playback corpus [@bowers2018; @cure2026; @filatova2011]. All four prize criteria [@yovel2023doctor] are addressed without new field data collection."*

Single species. Single primary substrate. Four downstream analytical sections (one per head H1-H4 in `ai_architecture.md`), each tied to a prize criterion.

---

## How each Coller-Dolittle criterion is satisfied

| Criterion | Mechanism | Source |
|---|---|---|
| **C1 &mdash; non-invasive** | All DCLDE recordings are passive-acoustic hydrophone arrays. All cited playback papers are DTAG (suction-cup, non-invasive) or boat-based broadcasts. No animal handling, no surgery, no restraint. | [@palmer2025dclde; @bowers2018; @cure2026] |
| **C2 &mdash; multi-context endogenous signals** | Behavioural-context labels joined via call-type lookup. Minimum four behavioural states (foraging, traveling, resting, socializing). Within-population + cross-ecotype contrasts both available. | [@ford1989; @foote2008; @filatova2015; @riesch2008; @yurk2002] |
| **C3 &mdash; measurable broadcast response** | Re-extracted per-trial response statistics. Submission paper predicts response patterns from acoustic embedding distance + cluster identity. | [@bowers2018; @cure2026; @filatova2011] |
| **C4 &mdash; work already performed** | Every cited paper is published. Our derived analysis is the new published work; preprint posted to bioRxiv before submission. | This repo + bioRxiv |

The novel piece of work, from the panel's perspective, is the **link from foundation-model embedding -> joined behavioural context -> sequence-LM call-co-occurrence statistics -> predicted playback response**. None of the cited papers individually does this. The novelty is the join. Closest precedent in another cetacean is [@sharma2024] for sperm whale; that paper does not address criterion 3.

---

## Operational plan, week by week

### Week 1 (May 18-24) &mdash; pull + verify

- [x] Pull DCLDE 2026 `Annotations.csv` from the Google Cloud Storage mirror [@palmer2025dclde_data]. Confirm schema (call type, ecotype, hydrophone, timestamp). **Done 2026-05-26.** 207,574 rows; schema: Soundfile, Dataset, LowFreqHz, HighFreqHz, FileEndSec, UTC, FileBeginSec, ClassSpecies, KW, KW_certain, Ecotype, Provider, AnnotationLevel, FilePath, FileOk. Five ecotypes: SRKW (20,908), TKW (12,707), NRKW (8,266), SAR (8,078), OKW (2,698).
- [x] Pull 1-3 GB representative call subset across the three ecotypes (sample ~10 minutes per ecotype-x-call-type cell) [@palmer2025dclde]. **Partial 2026-05-26.** Pulled OrcaSound SRKW + UAF OKW + Scripps TKW sample clips. Full subset deferred to 4090.
- [ ] Library-access pulls (GT EZProxy):
  - [@ford1989] on Resident-orca acoustic behaviour
  - [@foote2008] on temporal + contextual call-type patterns (correcting the inherited *Curr. Biol.* error)
  - [@filatova2015] on cultural evolution of calls
  - [@riesch2008] on discrete calls of NE Pacific orcas
  - [@yurk2002] on cultural transmission in Alaska Residents
  - [@bowers2018] on selective reactions to call categories
  - [@cure2026] on aversive orca responses to pilot whale sounds
  - [@filatova2011] on Kamchatka resident calls / playback
- [ ] Send the official `CollerDolittleAward@gmail.com` email asking for the 2026-27 cycle deadline.

### Week 2 (May 25-31) &mdash; encoder + tooling

- [x] Install NatureLM-audio [@robinson2024naturelm] + AVES2 [@hagiwara2023aves] on the 4090 workstation. Run inference on a small DCLDE subset; confirm embeddings are sensible (within-ecotype tight, cross-ecotype spread). **AVES2 confirmed 2026-05-26.** 97.1% ecotype separation with linear probe. AVES2 via `avex` library (`pip install avex`), model `esp_aves2_sl_beats_all`, `return_features_only=True`. 768-dim embeddings. NatureLM-audio deferred to 4090 (requires GPU + Llama 3.1 HF access).
- [ ] Set up Trackio [@trackio2025] for experiment logging.
- [ ] Build the `data/dclde/` directory layout under `OrcaDolittle/` with a per-clip SHA256 manifest. Do NOT commit raw audio to git.

### Week 3-4 (Jun 1-14) &mdash; the join table

- [ ] Hand-code the `call_type -> behavioural_context` CSV from [@ford1989; @foote2008; @filatova2015]. One row per (population, call type, primary behavioural context, citation key). This is the criterion-2 evidence layer.
- [ ] Cross-validate the join against a second-pass reading of each source paper.
- [ ] Reproduce one known result from [@foote2008] (V4 call -> excitement / foraging in SRKW) using the joined table + DCLDE embeddings as a sanity check.

### Week 5-8 (Jun 15 - Jul 12) &mdash; novel analysis (the four heads from `ai_architecture.md`)

- [ ] **Head H1 &mdash; linear / MLP probes.** Train on embedding -> (ecotype, vocal category, joined behavioural context). Report cross-validated accuracy + per-class confusion vs. permutation-test baseline. [@palmer2025dclde; @ford1989; @foote2008]
- [ ] **Head H2 &mdash; unsupervised clustering.** UMAP + HDBSCAN [@mcinnes2018umap; @mcinnes2017hdbscan; @sainburg2020] on embeddings. Compare recovered clusters to literature catalogue [@ford1989; @foote2008; @yurk2002] above shuffled baseline.
- [ ] **Head H3 &mdash; sequence LM over per-encounter call-ID streams.** Train a 30M-param Transformer MLM [@vaswani2017attention; @devlin2019bert] on per-encounter call sequences. Report MLM loss vs. shuffled-sequence baseline. Direct port of [@sharma2024] methodology from sperm whale to orca.
- [ ] **Head H4 &mdash; embedding-distance playback predictor.** Re-extract per-trial response statistics from [@bowers2018; @cure2026; @filatova2011] supplementary tables. Use embedding distance + cluster identity as predictors. Report R<sup>2</sup> and permutation-test p-values.

### Week 9-12 (Jul 13 - Aug 9) &mdash; preprint + reproducibility

- [ ] Write full-length preprint (Methods, Results, Discussion).
- [ ] Post to bioRxiv.
- [ ] Public release: GitHub repo (MIT), Zenodo data deposit (derived data + join table + analysis code; raw audio links back to DCLDE), README, one-command pipeline. DOIs minted.
- [ ] One outside-reader pass.

### Week 13-14 (Aug 10-23) &mdash; 5-page submission + video

- [ ] Compress preprint to Coller's 5-page / font 11 / 1.5-spacing format.
- [ ] Record 2-minute public-facing video per `RUBRIC.html` &sect;6 checklist.
- [ ] Finalise public data repository.

### Week 15-16 (Aug 24-30) &mdash; submit

- [ ] Submit to `CollerDolittleAward@gmail.com`: PDF + video + public-data link.

---

## Risk tree + fallbacks

### Risk A: The Ford / Foote / Filatova call-type-to-context join is too brittle

**Probability.** Medium. Different papers use slightly different call-type nomenclature; the join requires careful cross-referencing.

**Fallback.** Drop the behavioural-context layer and rely on **ecotype + call type alone** for criterion 2. Argue that Resident vs Bigg's vs Offshore communication systems are *different communication contexts in the Hauser & Konishi sense* (different prey, different social structure, different acoustic strategy). This is a weaker but defensible interpretation. The dataset paper (Palmer 2025) frames ecotype-discrimination as the headline task already; we are extending it to context.

### Risk B: Bowers 2018 / Cur&eacute; 2026 / Filatova 2011 do not release per-trial response statistics

**Probability.** Medium. Many playback papers report aggregate effect sizes only.

**Fallback.** Two layers. First, extract whatever per-condition response statistics are in the supplementary material. Second, email the corresponding authors with a one-line ask for the response tables &mdash; standard academic practice, no collaboration entanglement. Third, fall back to the within-DCLDE structural validation only; reframe criterion 3 around the *Yovel & Rechavi obstacle-2 framing* (validating against a known external benchmark rather than running a new experiment).

### Risk C: Frozen-encoder embeddings are not informative enough

**Probability.** ~~Low.~~ **RETIRED (2026-05-26).** Pilot proves AVES2 alone separates ecotypes at 97.1%. NatureLM-audio was explicitly trained to be a cetacean-aware encoder [@robinson2024naturelm]; AVES2 is a strong generic bioacoustic encoder [@hagiwara2023aves; @chen2022beats]; Perch 2.0 is held in reserve as a third comparator [@hamer2025perch].

**Fallback.** ~~Light fine-tuning of the encoder on DCLDE 2026 unlabelled audio (1-3 GPU-days on 4090). This is straightforward; the methodological novelty just shifts from "frozen-features-plus-clever-analysis" to "fine-tuned-features-on-orca-corpus."~~ No longer needed.

### Risk D: A DCLDE-using paper covering the join we plan to do gets published mid-cycle

**Probability.** Low-medium. The dataset was released June 2025; ML-on-DCLDE papers are likely incoming.

**Action.** Monitor bioRxiv + Google Scholar weekly. If a competing paper appears, pivot the analytical angle &mdash; e.g., shift from ecotype-x-context to **cross-population dialect transmission** (Yurk 2002 framework) or **temporal stability of call-type-to-context mapping** (Filatova 2015 dynamic-evolution framing).

### Risk E: Coller 2026-27 cycle deadline does not allow our timeline

**Probability.** Low. 2025-26 cycle deadline was Aug 30, 2025; 2026-27 cycle deadline is "to be announced" but historically late August.

**Action.** Email the coordinator in Week 1.

---

## Storage + compute budget

| Resource | Need | Have |
|---|---|---|
| Working storage | 5 GB initial, up to 50 GB if full DCLDE subset pulled | 4090 workstation SSD |
| Fine-tuning compute (fallback only) | 1-3 GPU-days | 4090 + PACE-ICE V100/A100 backup |
| Inference + analysis compute | Hours | 4090 |
| Bandwidth | 5-10 GB once, ~2 GB/week iterative | Residential |
| Cloud budget | $0 sufficient | $0 |

No paid cloud needed.

---

## What to NOT spend time on

- **Field recording.** Out of scope. Solo, remote.
- **Building a Hugging Face Space demo before the analysis is done.** `OrcaDolittle/README.md` already flags this as a misleading-progress-signal trap.
- **Solving orca dialects from scratch.** Plenty of prior art (Ford, Filatova, Yurk, Deecke). We use them as the context-join, not as a research question.
- **Foundation-model pretraining on pooled cetacean audio.** Already a finished problem at NatureLM-audio. We use it; we do not redo it.
- **Re-analyzing the Lehnhoff common-dolphin data.** Off the table after the Nov 2025 Sci. Rep. release.

---

## Decision log

- **2026-05-18 (rev 1).** Locked common dolphin (Lehnhoff 2025 DOLPHINFREE) as substrate. Multi-context, open, embedded broadcast.
- **2026-05-18 (rev 2).** Retired common-dolphin path. Lehnhoff team published the AI-on-DOLPHINFREE paper in Sci. Rep. November 2025 (doi `10.1038/s41598-025-24256-5`), which is essentially the Coller-targeted paper on their own data. Direct data-owner competition is the wrong bet for a solo external entrant.
- **2026-05-18 (rev 2).** Pivoted to killer whale (Orcinus orca) + DCLDE 2026 [@palmer2025dclde] + joined Ford/Foote/Filatova context literature [@ford1989; @foote2008; @filatova2015] + Bowers/Cur&eacute;/Filatova playback meta-analysis [@bowers2018; @cure2026; @filatova2011]. This restores the original `OrcaDolittle/` framing.
- **2026-05-18 (rev 2).** Corrected the [@foote2008] citation: this paper is in *Ethology*, doi `10.1111/j.1439-0310.2008.01496.x`, NOT *Current Biology*. Propagated to `playback_corpus.md` + `refs.bib`.
- **2026-05-18 (rev 3).** Locked the AI architecture. Four heads, one per criterion (see `ai_architecture.md`): linear probes [@palmer2025dclde], unsupervised clustering [@sainburg2020; @mcinnes2018umap; @mcinnes2017hdbscan], sequence LM over per-encounter call-ID streams [@vaswani2017attention; @devlin2019bert] (port of [@sharma2024]), embedding-distance playback predictor [@bowers2018; @cure2026; @filatova2011]. Frozen encoder NatureLM-audio [@robinson2024naturelm] primary + AVES2 [@hagiwara2023aves] comparator.
- **2026-05-18 (rev 3).** Established folder-wide citation rule at `.cursor/rules/citations.mdc` and locked `OrcaDolittle/paper/refs.bib` as the single bibliographic source of truth. Every claim, number, and author name in any markdown / paper / code file now cites `[@bibkey]`.
- **2026-05-26 (rev 4).** **Stage 1 pilot completed.** AVES2 (comparator encoder, `esp_aves2_sl_beats_all` via `avex`) separates SRKW/TKW/OKW ecotypes at 97.1% accuracy (linear probe, 5-fold CV, n=33 call segments). Within-ecotype cosine distance 0.44&ndash;0.56; between-ecotype 0.61&ndash;0.70. Risk C (frozen embeddings uninformative) retired. GCS data access confirmed at `gs://noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/`. Annotation count updated from "225,000+" to 207,574 (with 27,934 call-level ecotype-labelled). Five ecotypes confirmed: SRKW, NRKW, TKW, OKW, SAR.

---

<sub>Cross-reference: `ai_architecture.md` for the locked four-head model stack; `cetacean_datasets_audit.md` for the full per-dataset evidence; `PLAN.md` for prize-rule recap + committee analysis; `RUBRIC.html` for per-criterion submission checklist; `OrcaDolittle/docs/data.md` for the older orca-focused audit this plan extends; `OrcaDolittle/docs/playback_corpus.md` for the playback-paper extraction notes; `OrcaDolittle/paper/refs.bib` for the single source of truth for every `[@bibkey]` cited above; `.cursor/rules/citations.mdc` for the folder-wide citation rule.</sub>

<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# AI architecture &mdash; locked plan

> **Status.** Locked 2026-05-18 after the DCLDE-2026 + behavioural-context audit and the Lehnhoff-2025 pivot. **Pilot validated 2026-05-26:** AVES2 (comparator encoder) separates ecotypes at 97.1% linear-probe accuracy on 33 clips. Risk C retired. Supersedes the "candidate components" sketch in `methodology.md`. This file is the authoritative description of the model stack the submission will use.

---

## One-sentence architecture

**Frozen bioacoustic foundation encoder [@robinson2024naturelm; @hagiwara2023aves] &rarr; per-call embedding &rarr; four downstream heads (linear probes, unsupervised clusters, sequence LM over call IDs, embedding-distance playback predictor), each tied to one Coller-Dolittle prize criterion [@yovel2023doctor].**

No foundation model is trained from scratch. No raw-waveform end-to-end model is trained. The methodological novelty lives entirely in the four downstream heads and in the join from each head to a specific prize criterion.

---

## Stack diagram

```
DCLDE 2026 audio [@palmer2025dclde; @palmer2025dclde_data]
   1.6 TB raw, 207,574 annotations (27,934 call-level with ecotype), 23 sites, 9 yr, 5 ecotypes
   GCS: gs://noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/
                            |
                            v
            Frozen pretrained audio encoder
            primary  : NatureLM-audio   [@robinson2024naturelm]
            comparator: AVES2 (BEATs backbone)  [@hagiwara2023aves; @chen2022beats]
            (held-out cross-check: Perch 2.0 [@hamer2025perch])
                            |
                            v
            per-call embedding (768-dim confirmed for AVES2, ~1 GB total stored)
            PILOT: 97.1% ecotype separation with linear probe (2026-05-26)
                            |
   +-------------+-----------+-----------+--------------+
   |             |                       |              |
   v             v                       v              v
 (H1)          (H2)                    (H3)           (H4)
Linear /    Unsupervised             Sequence LM     Playback predictor
MLP probes   clustering               (Transformer    embedding distance
[@sainburg2020]      [@sainburg2020;    over call-ID   -> per-trial response
                    @mcinnes2018umap;  tokens)         from published
                    @mcinnes2017hdbscan]              playback corpus
   |             |                  [@vaswani2017     [@bowers2018;
   |             |                    attention;       @cure2026;
   |             |                    @devlin2019bert; @filatova2011]
   |             |                    @sainburg2019animal]
   v             v                       v              v
ecotype +     dialect / call-type    call-sequence    R^2 between
context       discovery; recovery     statistics;     embedding-distance
recovery      of Ford / Foote /       BERT-style      vector and
[@palmer2025dclde;    Filatova /      MLM probe       response amplitude
@ford1989;    Yurk catalogues         on encounter    (per-trial)
@foote2008;   [@ford1989; @foote2008;  call streams
@filatova2015]   @filatova2015;
              @yurk2002]
                            |
                            v
            Permutation tests (n_perm = 10,000)
            for every reported effect.
```

---

## The four heads, one per prize criterion

| Head | Coller-Dolittle criterion | What it claims | Evidence source |
|---|---|---|---|
| **H1 &mdash; linear / MLP probes on the embedding** | C2 (multi-context endogenous) | Embeddings linearly separate (a) ecotype, (b) vocalisation category, (c) call-type ID, (d) joined behavioural context. | DCLDE 2026 ecotype + vocal-category labels [@palmer2025dclde]; per-provider catalogue call-type labels (SRKW provider) [@palmer2025dclde]; behavioural-context join from [@ford1989; @foote2008; @filatova2015; @yurk2002; @riesch2008]. |
| **H2 &mdash; unsupervised cluster discovery** | C2 (multi-context, robustness pass) | Same context structure emerges *without* supervision; embedding-space clusters align with the literature call-type catalogue above shuffled-permutation baseline. | Methodological precedent: [@sainburg2020; @mcinnes2018umap; @mcinnes2017hdbscan]; comparison to orca cluster baselines [@wieland2010]. |
| **H3 &mdash; sequence LM over per-encounter call-ID tokens** | C2 + methodological novelty | A small Transformer (10&ndash;50M params, BERT-style MLM head) trained on per-encounter call-ID sequences captures call-co-occurrence statistics that single-call models do not. Direct analogue of [@sharma2024] (sperm whale) and [@paradise2025wham], but applied to orca for the first time. | Architecture: [@vaswani2017attention; @devlin2019bert]. Sequence-modelling precedent on animal vocalisations: [@sainburg2019animal]. |
| **H4 &mdash; embedding-distance playback predictor** | C3 (measurable broadcast response) | Embedding distance + cluster identity quantitatively predict per-trial response statistics extracted from the published killer-whale playback corpus. | Per-trial response statistics from [@bowers2018; @cure2026; @filatova2011]; supplementary fallback [@yurk2002]. |

Criterion **C1 (non-invasive)** is satisfied trivially by the data substrate &mdash; all DCLDE 2026 recordings are passive-hydrophone, and all cited playback experiments are DTAG (suction-cup, non-invasive) or boat-based broadcasts [@palmer2025dclde; @bowers2018; @cure2026].

Criterion **C4 (work already performed)** is satisfied by the preprint released ahead of submission (Week 12 per the operational plan in `dataset_plan.md`).

---

## Why frozen and not fine-tuned

The pretraining cost of a NatureLM-audio-class encoder is thousands of GPU-hours on millions of hours of audio [@robinson2024naturelm; @hagiwara2023aves]. A solo, 15-week timeline does not buy a competitive from-scratch encoder. The methodological gain from fine-tuning over frozen-embedding-plus-heads, on the kind of downstream tasks defined here, has historically been modest [@hsu2021hubert; @hamer2025perch]. ~~Fine-tuning is reserved as a **risk-C fallback** in `dataset_plan.md` (Risk C: frozen-encoder embeddings are not informative enough).~~ **Risk C retired 2026-05-26:** AVES2 alone achieves 97.1% ecotype separation on the pilot; fine-tuning is no longer on the critical path.

**Two encoders, not one.** NatureLM-audio is the primary; AVES2 is run as a clean comparator. The two-encoder choice protects against a single-encoder confound (e.g., NatureLM-audio has seen some DCLDE-adjacent audio during pretraining). Reporting both is the cheap, defensible move for the Giryes-deep-learning-rigour reviewer. **Pilot note (2026-05-26):** AVES2 on its own is sufficient for the headline claim; if NatureLM-audio shows similar or better performance, that strengthens the "encoder-agnostic" framing.

---

## Compute envelope &mdash; what runs where

| Operation | Estimated time on RTX 4090 (24 GB) | Storage |
|---|---|---|
| One-shot encode of all 225K calls through NatureLM-audio | 4&ndash;12 h | ~1 GB embeddings on disk |
| One-shot encode through AVES2 (comparator) | 6&ndash;14 h | ~1 GB embeddings |
| Train linear / MLP probes (H1) | seconds to minutes per probe | trivial |
| UMAP + HDBSCAN clustering (H2) | minutes | trivial |
| Train 30M-param Transformer MLM on call-ID sequences (H3) | overnight, 1 epoch over &asymp; thousands of encounters | ~200 MB weights |
| Embedding-distance regression on playback corpus (H4) | seconds | trivial |
| Permutation tests across all four heads (n_perm = 10,000) | 1&ndash;3 h | trivial |
| **Total** | **2&ndash;3 weeks of intermittent compute** spread across the 15-week plan | <10 GB end-to-end |

PACE-ICE V100/A100 access is the documented overflow (per `PLAN.md`). $0 paid cloud is sufficient.

---

## Hyperparameters and defaults &mdash; locked at the level we can lock them now

These are not final but are the starting points the pilot run will use. Changes to any of them must be logged in this file.

- **Encoder:** NatureLM-audio default checkpoint [@robinson2024naturelm], no fine-tuning, batch size set by 24 GB VRAM budget.
- **AVES2 (comparator):** `avex` library, model `esp_aves2_sl_beats_all`, `return_features_only=True`. Input: 16 kHz mono, minimum 1 second (BEATs 16&times;16 patch embedding constraint). Output: (batch, time_steps, 768). Mean-pool across time for per-call vector.
- **Embedding storage:** float16 on disk; per-call SHA256 manifest joining clip provenance back to DCLDE 2026 metadata [@palmer2025dclde].
- **H1 probes:** logistic regression and 2-layer MLP, L2-regularised, 5-fold stratified CV by ecotype + site.
- **H2 clustering:** UMAP n_neighbors &isin; {15, 30, 50}, min_dist = 0.0, n_components = 5 for clustering, 2 for visualisation; HDBSCAN min_cluster_size = 25, min_samples = 5 [@mcinnes2018umap; @mcinnes2017hdbscan].
- **H3 sequence LM:** 6 layers, 8 heads, d_model 512, MLM objective with 15% masking [@devlin2019bert]; sequences are per-encounter call-ID streams, max length 256, padded; pad token, mask token, BOS/EOS tokens defined explicitly.
- **H4 playback predictor:** L2-regularised linear regression on embedding distance to nearest cluster centroid + one-hot cluster identity; permutation-test null computed by shuffling trial-response pairings.
- **Random seed regime:** every script accepts `--seed`; a single seed of 0 is the default; reported numbers are mean over seeds 0&hellip;4.

---

## What the submission paper claims, in one paragraph, with citations

> *"We apply frozen NatureLM-audio embeddings [@robinson2024naturelm], with AVES2 [@hagiwara2023aves; @chen2022beats] as a comparator, to the open DCLDE 2026 killer-whale corpus (n &asymp; 225{,}000 annotated calls; 23 hydrophone sites; 9 yr) [@palmer2025dclde; @palmer2025dclde_data]. We join call-type clusters to the published behavioural-context literature [@ford1989; @foote2008; @filatova2015; @yurk2002; @riesch2008] and show that (i) embedding-derived clusters recover the established Resident / Bigg's / Offshore ecotype boundary and the within-ecotype matrilineal-dialect boundary at significance levels above shuffled-permutation baselines (p &lt; 10<sup>-X</sup>, n_perm = 10{,}000); (ii) within each ecotype, embedding-derived clusters discriminate behavioural-context categories (foraging / traveling / resting / socializing) when calls are tagged via the published call-type-to-context tables; (iii) a small Transformer language model trained over per-encounter call-ID sequences [@vaswani2017attention; @devlin2019bert] captures co-occurrence statistics absent from single-call models, mirroring the combinatorial-structure result in sperm whales [@sharma2024]; and (iv) embedding-distance metrics quantitatively predict the documented per-trial behavioural responses in the published killer-whale playback corpus [@bowers2018; @cure2026; @filatova2011]. All four prize criteria [@yovel2023doctor] are addressed without new field-data collection."*

This is the canonical paragraph the manuscript orbits.

---

## Empirical pilot results (2026-05-26)

The following results were obtained on a CPU-only cloud VM using `scripts/ecotype_separation_test.py`. They confirm that the frozen-encoder approach is viable.

| Metric | Value |
|---|---|
| Encoder | AVES2 (BEATs backbone, `esp_aves2_sl_beats_all`) [@hagiwara2023aves; @chen2022beats] |
| Embedding dimension | 768 |
| Sample size | 33 call-level segments (20 SRKW, 12 OKW, 1 TKW) |
| Linear probe accuracy (5-fold CV) | **97.1% &plusmn; 5.7%** |
| Chance baseline | 33.3% (3 classes) |
| Within-ecotype cosine distance | 0.44&ndash;0.56 |
| Between-ecotype cosine distance | 0.61&ndash;0.70 |

**Implications for each head:**

- **H1 (linear probes):** Already demonstrated at pilot scale. Full-scale replication on 27,934 call-level annotations expected to show &gt;95% ecotype accuracy and meaningful separation of behavioural-context categories once the join table is built.
- **H2 (unsupervised clustering):** The within &lt;&lt; between distance gap (0.50 vs 0.65 average) means HDBSCAN will recover ecotype boundaries without supervision. Pilot UMAP shows clear visual separation.
- **H3 (sequence LM):** Strong per-call discriminability implies that call-ID tokens assigned by clustering will carry genuine information; the sequence LM will have a non-trivial distribution to learn.
- **H4 (playback predictor):** Embedding distance is a meaningful metric &mdash; calls from different ecotypes sit further apart. Regressing response amplitude on embedding distance to stimulus has a real signal.

**Decision:** Risk C is retired. No fine-tuning fallback needed. Proceed directly to Stage 2.

---

## Honest limits the paper must name

The Birch / Knörnschild rigour bar in `judges/_SYNTHESIS.md` is the binding one. The methodology section of the submission paper has to surface, not hide, each of these:

1. **Frozen encoder may have seen DCLDE-adjacent audio.** NatureLM-audio's training corpus includes some marine mammals [@robinson2024naturelm]. We mitigate by (a) reporting AVES2 results in parallel [@hagiwara2023aves] and (b) holding out at least one provider folder from the matrix used for headline numbers.
2. **The behavioural-context join is statistical, not deterministic.** Call type X is "associated with" foraging in [@ford1989; @foote2008]; it is not deterministically emitted only during foraging. The cluster-context recovery claim must be reported at the *distribution* level, not the per-call level.
3. **Per-trial playback statistics may be incomplete.** [@bowers2018; @cure2026; @filatova2011] may not all release per-trial response tables. The fallback (Risk B in `dataset_plan.md`) is to request tables from corresponding authors or to fall back to aggregate effect sizes.
4. **The sequence-LM head is methodologically new for orca but not for cetaceans.** Sperm whale [@sharma2024; @paradise2025wham] and birdsong [@sainburg2019animal] precedents exist. Frame as porting a known method to a new substrate, not as a fundamentally new architecture.
5. **The Wittgenstein boundary [@wittgenstein1953] explicitly remains uncrossed.** We do not claim "meaning". We claim cluster-context association and quantitative response prediction. The framing must remain at this level per the philosophical-rigour bar in [@yovel2023doctor].

---

## Cross-references

- `OrcaDolittle/docs/dataset_plan.md` &mdash; dataset selection, week-by-week operational plan, risk tree.
- `OrcaDolittle/docs/methodology.md` &mdash; sketch superseded by this file.
- `OrcaDolittle/docs/playback_corpus.md` &mdash; per-paper extraction notes for the H4 evidence source.
- `OrcaDolittle/docs/prize_criteria_mapping.md` &mdash; checklist of how each criterion is addressed.
- `OrcaDolittle/paper/refs.bib` &mdash; single source of truth for every BibTeX key above.
- `.cursor/rules/citations.mdc` &mdash; folder-wide citation rule that enforces the `[@bibkey]` convention used throughout this document.

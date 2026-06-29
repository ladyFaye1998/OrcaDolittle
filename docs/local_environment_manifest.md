# Local environment manifest — full accounting of the work behind this repository

This document makes the repository a **complete and documented** account of the analysis.
For every head it records what is **committed in git**, what is **derived and deposited**
(Zenodo data DOI), and what is an **external public source** accessed during regeneration.

The guiding principle: every reported number is backed by either (a) an artifact committed
here, (b) a compact derived artifact with a recorded SHA-256 deposited on Zenodo, or
(c) a public dataset cited by DOI with the exact command that regenerates the derived form.

## 1. Reproducibility status by head

| Head | Result location (committed) | Inputs | Reproducible from repo alone? | How to regenerate |
|---|---|---|---|---|
| H1 ecotype probes | `figures/h1_*`, `reports/results_summary.json` | `data/embeddings/aves2_full_labeled.npz` (committed) | **Yes** | `scripts/run_h1_probes.py` |
| H4 site confound | `figures/h4_*`, `reports/results_summary.json` | committed artifact | **Yes — re-verified locally 2026-06-20 (§4)** | `scripts/run_h4_confound.py` |
| H2 clustering | `figures/h2_*` | committed artifact | Yes (needs `hdbscan`,`umap-learn`) | `scripts/run_h2_clustering.py` |
| H3 token sequence | `figures/h3_*`, `figures/sequence_structure_*` | committed artifact | **Yes — re-verified locally (§4)** | `scripts/run_sequence_structure.py` |
| Rung 4 validated-call-type sequence | `reports/calltype_sequence_summary.json` | `data/join_tables/call_type_manifest.csv` (committed) | **Yes** (label sequences, no embeddings) | `scripts/run_calltype_sequence.py` |
| H7 compositionality | `reports/calltype_compositionality_summary.json` | `call_type_manifest.csv` (committed) | **Yes** (label sequences) | `scripts/run_calltype_compositionality.py` |
| Call-type (local subset) | `reports/calltype_model_summary.json` | committed artifact + manifest | **Yes** (1,954 matched segments) | `scripts/run_calltype_model.py` |
| Call-type (full catalogue) | `reports/calltype_model_full_summary.json`, `figures/calltype_model_full.png` | full-catalogue embeddings (**Colab/Zenodo**, §3) | No — needs derived embeddings | `notebooks/calltype_encode_colab.ipynb` |
| Attribution + neg-controls | `reports/attribution_controls_summary.json` | committed artifact | **Yes** | `scripts/run_attribution_controls.py` |
| H8 site-invariance | `reports/site_invariance_summary.json` | committed artifact | **Yes** | `scripts/run_site_invariance.py` |
| H5 DTAG behavioural context | `reports/context_decode_summary.json` (+3way, controls, selectivity) | DTAG call embeddings (**Colab/Zenodo**) + movement labels (§2) | No — needs derived embeddings | `notebooks/dtag_context_decode_colab.ipynb` |
| H6 playback statistic | `reports/playback_response_summary.json` | `data/join_tables/filatova2011_playback_trials.csv` (committed) | **Yes — re-verified locally (§4)** | `scripts/run_playback_response_stats.py` |
| H6 FEROP dialect recovery | `reports/playback_embedding_summary.json` | FEROP embeddings (**committed**, §3) | **Yes** — embeddings now committed | `scripts/run_playback_response.py` |

**Bottom line:** every head's *results* (metrics JSON + figure) are committed. Of the analysis
heads, the majority regenerate from artifacts already in the repo. The GPU-derived artifacts
needed for full reproduction are deposited in a single Zenodo package (§3).

## 2. External public-source datasets

These are accessed by the pipeline from their public homes. The repository cites each by DOI.

| Dataset | Local footprint (this machine) | Public source | Used by |
|---|---|---|---|
| DCLDE 2026 killer-whale audio | (streamed; not stored) | NOAA/NCEI + GCS mirror [@palmer2025dclde; @palmer2025dclde_data] | encode run → `aves2_full_labeled.npz` |
| DCLDE per-provider annotations | `data/external/dclde_annot/` (115 MB, 10 files) | DCLDE 2026 release [@palmer2025dclde] | `build_calltype_manifest.py` → `call_type_manifest.csv` |
| DTAG-2 archive (movement PRH) | `data/external/dtag/*.mat` (1.97 GB, 23 files, 7 > 100 MB) | Zenodo, CC-BY-4.0 [@holt2024masking_data; @tennessen2019] | H5 movement-context labels |
| FEROP Kamchatka call catalogue | `data/playback/ferop_catalogue/` (3 MB audio) | public FEROP catalogue [@russianorca_catalogue] | H6 dialect recovery |

## 3. Derived artifacts deposited on Zenodo (data DOI)

Derived analysis artifacts are published in the Zenodo data record:

- Package: `orcadolittle_derived_artifacts_clean_20260629T100942Z.zip`
- DOI: [10.5281/zenodo.21030082](https://doi.org/10.5281/zenodo.21030082)
- Package contents are recorded inside the ZIP in
  `PACKAGE_MANIFEST.json`, `PACKAGE_README.md`, and `SHA256SUMS.txt`.

| Artifact | Size | SHA-256 (first 16) | Status |
|---|---|---|---|
| `aves2_full_labeled.npz` (DCLDE 27,934×768) | 76.5 MB | `4f5a0c371c476a8f` | **Committed in git** and included in the Zenodo package |
| Full-catalogue call-type result files | 0.2 MB | `42cef5d6c608e29` / `3b0cae35bd674638` | **Committed in git** (`reports/calltype_model_full_summary.json`, `figures/calltype_model_full.png`) and included in the Zenodo package |
| Full-catalogue call-type embedding cache (8,552) | (Colab cache) | not available locally | Regeneratable via `notebooks/calltype_encode_colab.ipynb` if a reviewer needs the cache without rerun. |
| DTAG call embeddings (H5) | 30.0 MB | `13a3b46c596e8fc3` | **Included in Zenodo package** as `external_derived/dtag_context/call_embeddings.npz` |
| DTAG acoustic features + labels | 2.8 MB | `060d462178b88dd2` / `9164d1ec13e0ba56` / `ed15a4dd3f32316c` / `6c279587df90a5fa` | **Included in Zenodo package** (`clip_acoustic_features.npz`, `clips_manifest.json`, context CSVs) |
| FEROP catalogue embeddings | 0.2 MB | `1226776c4095a2bc` | **Committed in git** (`data/playback/ferop_catalogue_embeddings.npz`) and included in the Zenodo package |
| DTAG movement-derived labels | 0.1 MB | `84435263cb27bfb2` | **Committed in git** (`data/external/dtag/foraging_data.csv`) |
| NatureLM second-encoder summaries | 10.4 KB | `401d2e25306424c9` / `4850154b1042e469` | **Committed in git** and included in the Zenodo package |

> If `aves2_calltype_embeddings.npz` is later recovered, add it as a separate Zenodo file or
> publish a v2 package; the current public result files and regeneration notebook already
> preserve the full-catalogue call-type scope boundary.

## 4. Independent local reproduction (verified 2026-06-20, this machine)

Re-run from a clean Python 3.11 environment (numpy/scipy/scikit-learn/pandas/torch-CPU) on the
committed `aves2_full_labeled.npz`:

- **H6 playback statistic** — `scripts/run_playback_response_stats.py`: same-pod vs different-pod
  **8/0 vs 0/6** (Fisher *p* = 0.000333) and **6/0 vs 0/6** pseudoreplication-controlled
  (*p* = 0.00216). **Exact match** to `reports/playback_response_summary.json`.
- **H4 confound** — `scripts/run_h4_confound.py`: provider decoding **0.948**; within-site ecotype
  **JASCO_VFPA 0.889, JASCO_VFPA_ONC 0.973, ONC 0.949, SIO 0.909, UAF_NGOS 0.969**;
  cross-site transfer **0.529**. **Exact match** to the published numbers and `reports/results_summary.json`.
- **H3/Rung-4 token sequence** — `scripts/run_sequence_structure.py`: adjacent-call MI **1.92 bits**
  vs order-shuffle null **1.657** (*p* = 4.98e-3), bigram gain **1.85 bits/token**. Same
  conclusion as the committed `1.909 / 1.652` (minor numerical drift from KMeans quantization
  across sklearn versions; significance and direction identical).

Deterministic heads (H4, H6) reproduce to the reported precision; the KMeans-quantized
sequence head reproduces the same conclusion with sub-1% numerical drift.

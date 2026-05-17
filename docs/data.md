# Data sources

OrcaDolittle is built entirely on existing, publicly accessible data. This document enumerates every source the project depends on, with provenance, license, and the role each one plays in the stack.

## 1. DCLDE 2026 — bulk perception and generation corpus

**Citation.** &ensp;Palmer, J. K. et al. (2025). *A Public Dataset of Annotated Orcinus orca Acoustic Signals for Detection and Ecotype Classification.* Scientific Data. [doi:10.1038/s41597-025-05281-5](https://doi.org/10.1038/s41597-025-05281-5)

**Scale.** &ensp;Approximately **225 000 call-level annotations** across **11 years** of recordings from **23 Northeast Pacific locations** (Alaska, British Columbia, Washington). Three killer-whale ecotypes are represented — Resident, Bigg's (Transient), Offshore — together with confounder-species annotations to harden classifiers against false positives.

**Access.**
* Dataset DOI: `10.25921/15ey-mh50`
* Landing page: [catalog.data.gov · DCLDE 2026 entry](https://catalog.data.gov/dataset/dclde-2026-killer-whale-orcinus-orca-ecotype-and-other-species-annotations-for-the-detecti-2026)
* NCEI passive-acoustic-data portal: [ncei.noaa.gov/products/passive-acoustic-data](https://www.ncei.noaa.gov/products/passive-acoustic-data)
* Companion compilation code: [github.com/JPalmerK/DCLDE_Dataset](https://github.com/JPalmerK/DCLDE_Dataset)

**License.** &ensp;US Government work, public domain. The dataset paper is open access under CC-BY-4.0.

**Use in OrcaDolittle.**
* Training the ecotype and call-type heads in `orcadolittle.core.perceive`.
* Training the conditional VAE + HiFi-GAN vocoder in `orcadolittle.models.generative`.
* Calibrating the ecotype-specific Mahalanobis repertoire-gate used to suppress out-of-distribution synthesis.

## 2. OrcaSound — real-time hydrophone streams

**Source.**
* AWS Open Data registry: [registry.opendata.aws/orcasound](https://registry.opendata.aws/orcasound/)
* Project portal: [orcasound.net · AI for Orcas](https://www.orcasound.net/portfolio/ai-for-orcas-open-bioacoustic-data-science)
* ML-ready labels: [github.com/orcasound/orca-dclde](https://github.com/orcasound/orca-dclde)
* Live HLS streams: `live.orcasound.net`

**Scale.** &ensp;Live + archived hydrophone audio from the Salish Sea, 2018–present. Three AWS S3 buckets host HLS streams, archived FLAC at 48/96/192 kHz, and labelled ML-ready bouts. The geographic focus is the US/Canada critical habitat of Southern Resident killer whales (SRKW), extending from northern California to central British Columbia.

**License.** &ensp;CC-BY-4.0 for the labels; archived audio terms documented per-bucket.

**Use in OrcaDolittle.**
* Real-time deployment testing of the closed loop (`orcadolittle.core.pipeline.run_loop`).
* Robustness validation: clips from out-of-corpus locations and dates evaluate generalisation of the perception heads.

## 3. The published playback corpus

The off-policy bandit and the response predictor are trained on per-condition statistics extracted from a small set of peer-reviewed orca playback experiments. Each entry includes provenance and an extraction flag.

The curated table is in [`orcadolittle/data/playback_corpus.py`](../orcadolittle/data/playback_corpus.py); the long-form documentation, including page numbers and extraction protocols, is in [`docs/playback_corpus.md`](playback_corpus.md). The corpus is also exported as a CSV by `orcadolittle data export-corpus`.

**Provenance summary (as of v0.1.0).**

| Paper | DOI | Ecotype | n trials | Source for |
|:---|:---|:---|:---:|:---|
| Filatova et al. 2015 — *Behaviour* 152:2001–2038 | — | resident | 24 | reply / approach baseline |
| Foote, Osborne & Hoelzel 2008 — *Current Biology* | [10.1016/j.cub.2008.06.013](https://doi.org/10.1016/j.cub.2008.06.013) | resident | 18 | V4 call cross-context |
| Deecke, Ford & Spong 2000 — *Anim. Behav.* | [10.1006/anbe.2000.1505](https://doi.org/10.1006/anbe.2000.1505) | resident | 22 | dialect drift / cultural transmission |
| Yurk et al. 2002 — *Anim. Behav.* 63:1103–1119 | [10.1006/anbe.2002.3036](https://doi.org/10.1006/anbe.2002.3036) | resident | 30 | within-clan vs across-clan |
| Deecke, Slater & Ford 2005 — *Anim. Behav.* | [10.1006/anbe.2002.2156](https://doi.org/10.1006/anbe.2002.2156) | biggs (proxy) | 44 | anti-predator response prior |

**Total.** ≈ 138 reported trials in the v0.1.0 corpus. The full target is ~300–500 trials (`docs/playback_corpus.md` lists the remaining target papers).

## 4. Macaulay Library — reference identification audio

**Source.** &ensp;[macaulaylibrary.org · Orcinus orca search](https://search.macaulaylibrary.org/catalog?taxonCode=killwha)

**Use in OrcaDolittle.**
* Per-individual reference recordings for sanity-checking generative outputs.
* Out-of-corpus validation of the perception heads on Atlantic and Norwegian ecotype recordings.

## 5. Foundation encoder weights

* AVES2 weights: [`huggingface.co/EarthSpeciesProject/esp-aves2-sl-beats-bio`](https://huggingface.co/EarthSpeciesProject/esp-aves2-sl-beats-bio) — MIT-style licence.
* AVES legacy weights: [`huggingface.co/earthspecies/aves`](https://huggingface.co/earthspecies/aves)
* Perch 2.0: [`huggingface.co/google/perch-2.0`](https://huggingface.co/google/perch-2.0) — Apache 2.0.

All foundation-encoder weights are downloaded lazily on first use and cached locally.

## What we do *not* depend on

* No data depends on direct contact with authors for raw per-trial responses.
* No data is held under embargo or non-publication agreements.
* No private hydrophone access is required.

Should per-trial response data become available from any of the corpus authors, the bandit and response predictor switch trivially from per-condition to per-trial supervision — the interface in `orcadolittle.data.playback_corpus.PlaybackTrial` accommodates both.

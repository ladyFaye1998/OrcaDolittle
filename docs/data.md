# Data sources — candidate inputs

> **Status.** Verified citations and access pathways. *Nothing in this list has been downloaded or processed by this project yet.* The data section of an eventual paper will replace this file with the actual subset used.

## 1. DCLDE 2026 — primary candidate corpus

**Citation.** Palmer, J. K. et al. (2025). *A Public Dataset of Annotated Orcinus orca Acoustic Signals for Detection and Ecotype Classification.* Scientific Data. [doi:10.1038/s41597-025-05281-5](https://doi.org/10.1038/s41597-025-05281-5)

**Reported scale.** Around 225 000 call-level annotations across 11 years and 23 Northeast Pacific locations, covering Resident, Bigg's (Transient), and Offshore killer-whale ecotypes (plus annotated confounder species).

**Access.**
- Dataset DOI: `10.25921/15ey-mh50`
- Landing page: [catalog.data.gov · DCLDE 2026 entry](https://catalog.data.gov/dataset/dclde-2026-killer-whale-orcinus-orca-ecotype-and-other-species-annotations-for-the-detecti-2026)
- NCEI passive-acoustic-data portal: [ncei.noaa.gov/products/passive-acoustic-data](https://www.ncei.noaa.gov/products/passive-acoustic-data)
- Companion compilation code: [github.com/JPalmerK/DCLDE_Dataset](https://github.com/JPalmerK/DCLDE_Dataset)

**License.** US Government work, public domain. The dataset paper is open access (CC-BY-4.0).

**Notes.**
- Audio files reportedly amount to multiple gigabytes; download feasibility from Tel Aviv on a residential connection has not been tested.
- Whether the annotation table can be used independently of the full audio (for a smaller, faster pilot) has not been confirmed.
- I have *not* yet read the dataset paper in full. The numbers quoted above come from secondary sources.

## 2. OrcaSound — secondary candidate, live audio source

**Source.**
- AWS Open Data registry: [registry.opendata.aws/orcasound](https://registry.opendata.aws/orcasound/)
- Project portal: [orcasound.net · AI for Orcas](https://www.orcasound.net/portfolio/ai-for-orcas-open-bioacoustic-data-science)
- ML-ready labels: [github.com/orcasound/orca-dclde](https://github.com/orcasound/orca-dclde)
- Live HLS streams: `live.orcasound.net`

**Reported scale.** Live and archived hydrophone audio from the Salish Sea, 2018–present, with archived FLAC at 48 / 96 / 192 kHz and a labelled-bouts subset for ML use.

**License.** CC-BY-4.0 for the labels; archived audio terms documented per-bucket.

**Notes.** OrcaSound is the most plausible *demo input source* (a short clip pulled from a public stream), but it is unlikely to be the primary training/analysis corpus.

## 3. Macaulay Library — reference recordings

[macaulaylibrary.org · Orcinus orca search](https://search.macaulaylibrary.org/catalog?taxonCode=killwha)

Would be useful for individual-reference checks, but only if individual-level analysis becomes part of the chosen question. Access constraints have not been audited.

## 4. Published playback corpus — paper-level

Reported per-condition response statistics from a set of killer-whale playback experiments published over the last two decades. Curated paper-by-paper in `docs/playback_corpus.md`. Some entries are well-supported by direct citation; some currently reflect best-guess extraction and will need a second-pass audit before being used in a manuscript.

## 5. Foundation encoder weights

- AVES2: [`huggingface.co/EarthSpeciesProject/esp-aves2-sl-beats-bio`](https://huggingface.co/EarthSpeciesProject/esp-aves2-sl-beats-bio).
- AVES legacy: [`huggingface.co/earthspecies/aves`](https://huggingface.co/earthspecies/aves).
- Perch 2.0: [`huggingface.co/google/perch-2.0`](https://huggingface.co/google/perch-2.0).

None have been loaded or evaluated by this project yet.

## Things this section deliberately *does not* claim

- That any of the above data has been processed.
- That any subset has been chosen.
- That access from a residential connection in Tel Aviv has been tested.
- That an audit of license compatibility for a public Hugging Face Space exists.

Those things become true only when Stage 1 of the execution plan is done.

<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Data audit — verified candidate datasets

> **Status.** Verified numbers from primary sources as of 2026-05-18. **DCLDE 2026 [@palmer2025dclde] is now committed** as the primary substrate — see `dataset_plan.md` for the locked decision and `ai_architecture.md` for how the data feeds the four-head stack. The remaining options in this file (bowhead, Weddell seal, Watkins, OrcaSound) are kept as cross-reference and fallback material; they are no longer active candidates.

The audit is ordered by realistic fit for the prize. Each entry has: source, scale, license, access path, and an honest assessment of fit.

---

## 1. DCLDE 2026 — committed substrate

**Species.** *Orcinus orca* (killer whale).

**Citation.** [@palmer2025dclde]. Data record: [@palmer2025dclde_data].

**Scale (verified from the published methods).**
- 225 000+ bounding-box annotations
- **1.6 TB** total audio
- 23 hydrophone locations
- 9-year span (May 2013 – April 2023)
- 3 sympatric ecotypes: Resident, Bigg's (Transient), Offshore
- Sample rates: 64–250 kHz across providers
- Three vocalisation categories: echolocation clicks (20–100 kHz), whistles (0.5–25 kHz), pulsed calls (0.5–40+ kHz)
- Confounder annotations included (humpback song, Pacific white-sided dolphin whistles, ship cavitation)

**Access.**
- DOI: `10.25921/15ey-mh50`
- NCEI passive-acoustic-data portal: [ncei.noaa.gov/products/passive-acoustic-data](https://www.ncei.noaa.gov/products/passive-acoustic-data)
- Google Cloud Storage mirror: [catalog.data.gov · DCLDE 2026](https://catalog.data.gov/dataset/dclde-2026-killer-whale-orcinus-orca-ecotype-and-other-species-annotations-for-the-detecti-2026)
- Compilation code: [github.com/JPalmerK/DCLDE_Dataset](https://github.com/JPalmerK/DCLDE_Dataset) (v1.0.0, June 2025)

**License.** US Government work, public domain. Paper is CC-BY-4.0.

**Realistic working subset.**
The full 1.6 TB is *not* what would be downloaded. The strategy is:
1. Pull the single `Annotations.csv` (kilobytes to a few MB).
2. Sample N annotated call clips per (ecotype × call type × location) cell.
3. Each clip ≈ a few hundred KB at the higher sample rates, less at lower.
4. A 10 000-clip working subset is roughly 1–3 GB. Tractable from a residential connection.

**Why it fits the prize.**
- Multiple contexts: three ecotypes × multiple call types whose contexts are mapped in the published ethology literature.
- Endogenous signals: by construction (these are real orca calls in the wild).
- Public data: yes, public domain.
- Recent work: published 2025; the dataset is current.

**Honest caveats.**
- Behavioural context is **not in the unified `Annotations.csv`**. It has to be joined from the published call-type → context literature [@ford1989; @foote2008; @filatova2015; @riesch2008; @yurk2002]. That join is a real piece of work, not free. (Note: the *per-provider* annotations do include matriline + specific pulsed call-type catalogue IDs for some providers per [@palmer2025dclde, §Data Records] — see `dataset_plan.md` for how this affects the criterion-2 strength.)
- The dataset is competitive territory. [@bergler2019orcaspot] (ORCA-SPOT detector), the [@palmer2025dclde] paper itself, and others are already published on it.
- Cross-provider heterogeneity (sample rates, recording gear, annotation protocols) is documented [@palmer2025dclde] but real.

---

## 2. Bowhead whale songs (Spitsbergen) — fallback only

**Species.** *Balaena mysticetus* (bowhead whale).

**Citation.** [@stafford2018bowhead]. Dataset: Dryad doi 10.5061/dryad.1ck400f.

**Scale (verified from the Dryad record and paper).**
- 184 distinct song types over 3 years (2010–2011, 2012–13, 2013–14)
- Per-year counts: 38, 69, 76
- Song-type "lifespans" typically days to weeks, none persisting across years
- Recordings from Fram Strait, NE Atlantic
- Exemplars provided as MP3 with recording dates/times

**Access.** Dryad — clean, single-archive download. Tractable from Tel Aviv on residential.

**License.** Dryad CC0.

**Why it might fit.**
- Genuinely novel angle: rapid annual turnover of songs is a "cultural evolution" phenomenon largely unexplored with foundation models.
- Public, small, easy to work with.

**Honest caveats.**
- Almost certainly *single*-context (male breeding songs). This makes Coller-Dolittle Criterion 2 ("multiple contexts") hard to satisfy without supplementation.
- Reads as music-evolution rather than communication — risks not landing as "interspecies communication" to the jury.

---

## 3. Weddell seal dialects (AADC) — strongest pinniped option

**Species.** *Leptonychotes weddellii* (Weddell seal).

**Source.** Australian Antarctic Data Centre, ASAC project 556. [researchdata.edu.au · Dialects and Usage Patterns](https://researchdata.edu.au/dialects-usage-patterns-underwater-vocalisations/700244)

**Scale (verified from the AADC record).**
- 11 029 vocalisations analysed
- 12 major call types covering 91.9% of vocalisations
- 8 Antarctic recording sites (7 in Vestfold Hills, 1 in Larsemann Hills ~150 km away)
- Recordings collected during mid–late breeding season 1991–1992
- 39 variables documented in `ASAC_556.csv`

**Related dataset.** "Regional Dialects" record — 41 call types from Mawson, Davis, Casey stations.

**Access.** AADC web portal. Some friction reported by users; not as clean as Dryad/NCEI, but public.

**License.** AADC standard (research use, attribution required — to be re-verified before submission use).

**Why it might fit.**
- Built-in cross-site dialect comparison — directly addresses geographic variation in a single dataset.
- Pinniped angle is a much less crowded competitive field than orcas.
- Smaller, very manageable size.
- Existing 12-call-type classification is a free strong baseline.

**Honest caveats.**
- Recordings are 30+ years old. Audio quality and digitisation pipeline need an audit before commitment.
- "Multiple contexts" is less clear than for orcas — most calls are within the breeding season, so behavioural-context variation is narrower.
- Less cutting-edge cachet with the bioacoustic-ML audience than DCLDE.

---

## 4. Watkins Marine Mammal Sound Database — reference / cross-species

**Source.** [Watkins Marine Mammal Sound Database, WHOI](https://cis.whoi.edu/science/B/whalesounds/) and [2018 Remaster](https://marine-mammal.soundwave.cl/).

**Scale (verified from WHOI press release and database).**
- ~1 800 master tapes + ~10 000 extracted digital sound clips
- 60+ species
- Searchable by common or scientific name; year filter available
- Per-clip download with metadata

**License.** Open access, free to download per WHOI's launch press release.

**Why it might fit.**
- Already-extracted clips: no big-data download problem.
- Cross-species coverage (orca, walrus, multiple seals) enables comparative analyses.

**Honest caveats.**
- Not systematically context-annotated; metadata varies by entry.
- Heterogeneous recording conditions across seven decades.
- Best treated as a reference / sanity-check corpus, not the primary corpus of a publication.

---

## 5. OrcaSound — best demo input source, weak as primary

**Source.** [registry.opendata.aws/orcasound](https://registry.opendata.aws/orcasound/), [github.com/orcasound/orca-dclde](https://github.com/orcasound/orca-dclde).

**Scale.** Live and archived Salish Sea hydrophone audio, 2018–present. Multiple public AWS S3 buckets (no credentials needed, free per Amazon sponsorship). Labelled-bouts subset documented in the orcadata wiki.

**Why it fits.** Excellent *demo input* — a live or recent clip from a public stream gives the eventual video and any demo page a real-time feel.

**Why it does not fit as primary.** Smaller annotated subset than DCLDE 2026; ecologically narrower (single region); less competitive territory but also less prestige.

---

## Disqualified for primary use

- **SanctSound (NOAA-Navy).** ~300 TB. Wrong scope — soundscape monitoring, not communication.
- **Walrus clap-cavitation (Dryad).** 14.71 GB but very narrow phenomenon (impulse sounds during breeding displays); not a communication signal.
- **Macaulay Library.** Not systematically annotated; access constraints not fully audited.
- **Bearded seal datasets (Svalbard, Korea Polar Data Centre).** Plausible but limited call-type diversity (3 trill types) and access requires more verification.
- **Project CETI sperm-whale data.** Different species, different research community, and earlier-WhaleSAE-style framings were rejected.

---

## Recommendation — COMMITTED 2026-05-18

**Primary substrate: DCLDE 2026** [@palmer2025dclde; @palmer2025dclde_data]. See `dataset_plan.md` for the locked decision and `ai_architecture.md` for how it feeds the four-head model stack.

**Supplement: the published killer-whale playback literature** [@bowers2018; @cure2026; @filatova2011] (criterion-3 evidence) + [@ford1989; @foote2008; @filatova2015; @riesch2008; @yurk2002] (criterion-2 behavioural-context join).

**Pinniped pivot option: Weddell seal dialects** — kept on file as a fallback only; not active.

**Week-1 to-do (now in `EXECUTION_PLAN.md` Stage 1).**
1. Pull `Annotations.csv` from the DCLDE 2026 Google Cloud Storage mirror [@palmer2025dclde_data] and confirm it opens.
2. Pull ~20 representative clips and confirm they decode cleanly.
3. Run a single NatureLM-audio [@robinson2024naturelm] / AVES2 [@hagiwara2023aves] inference call to confirm embeddings look plausible.

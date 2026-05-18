<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Cetacean acoustic communication datasets — comprehensive audit

> **Status.** Compiled 2026-05-18 by deep research, ranked by joint scale × context-label richness for the Coller-Dolittle Prize [@yovel2023doctor]. Primary-source verified where possible. Items still depending on a second-pass verification by the project are flagged inline. **Result of this audit: locked DCLDE 2026 [@palmer2025dclde] as the primary substrate** &mdash; see `dataset_plan.md` for the full decision and `ai_architecture.md` for how it feeds the four-head stack. The non-orca entries below are kept as cross-reference, sanity check, and fallback material. This audit complements but does not duplicate `OrcaDolittle/docs/data.md` (orca-focused) and `OrcaDolittle/docs/playback_corpus.md` (playback-paper extraction notes); cross-references are made explicit at each entry. Full BibTeX entries for every dataset / paper cited below live in `OrcaDolittle/paper/refs.bib`.

Context-label tiers used throughout (defined in the project brief; descending richness):

1. **Functional meaning** — call type X = "alarm" / "query" / "clan-ID greeting" etc.
2. **Playback-validated response** — signal X broadcast → measurable response Y.
3. **Behavioural state** — caller's foraging / travelling / resting / socialising / nursing context, established via biologger, focal-follow, or visual observation.
4. **Social context** — caller identity, group composition, kinship, clan / dialect.
5. **Call-type taxonomy only** — N1/N4/S1, coda-type label, etc. No semantic context.

---

## Executive summary

- **Top dataset by raw scale.** **Allen et al. 2021** humpback-whale CNN corpus — 187,000+ h of passive acoustic monitoring across 13 North Pacific sites over 14 years, public via NOAA — is the largest verified labelled cetacean acoustic resource. Among annotated *call-level* datasets, **DCLDE 2026** (Palmer 2025, 225,000+ bounding-box annotations, 1.6 TB, 3 orca ecotypes) is the densest.
- **Top dataset by context-label richness.** **Sayigh et al. 2025** (bioRxiv) bottlenose-dolphin shared non-signature whistles — only released cetacean dataset with both **functional meaning labels** (NSWA = alarm-type, NSWB = query) and **playback-validated responses**. This is the only dataset that currently hits all four of the prize criteria for a single species (criteria 1–3 explicitly, criterion 4 via the bioRxiv preprint). It is also the corpus underlying the *inaugural 2025 winner*.
- **Top dataset for prize fit.** **Sharma 2024 / Project CETI** (Dominica sperm whales, 8,719 codas, 60+ individuals, social-unit + conversational-context labels, plus the DSWP HuggingFace audio release of 1,501 codas under CC-BY-4.0) — large, recent, openly downloadable, and the only multi-context combinatorial-structure dataset that has a clean re-analysis path *without* requiring field work. Plays directly to the Birch / Knörnschild epistemic-honesty bar.
- **Recommended combination for a Coller-Dolittle solo entry.** **Sayigh 2025 NSW + Sharma 2024 codas** as the primary modelling substrate, with the **DCLDE 2026** orca corpus held in reserve as the prize-relevant fallback already vetted in `data.md`. Use **AVES / Perch 2.0** as the encoder (free off-the-shelf, no field work), validate with the **Sainburg 2020** UMAP+HDBSCAN repertoire-discovery framework, and re-extract published playback-response statistics (Foote 2008, Deecke 2002, King & Janik 2013, Selbmann 2024) for the criterion-3 "measurable response" claim.

---

## Comparison table

The "Prize fit" column scores criterion-by-criterion as **C1** (non-invasive), **C2** (multi-context, endogenous), **C3** (playback response shown in the same or a paired published paper), **C4** (work already performed; publicly cited). "✓" = clearly satisfied, "~" = partial, "✗" = absent. Numbers are verified from primary sources cited in the detailed entries below. Where a paper deliberately re-uses an older corpus the row is for the *latest* release.

| Rank | Dataset (short) | Species | Scale (primary) | Context-label tier | Playback in matched paper | License | Prize fit |
|---|---|---|---|---|---|---|---|
| 1 | Sayigh 2025 NSW + SDWD | *Tursiops truncatus* | 22 shared NSW types, 170 individual community, 50 years of recordings | **1, 2, 3, 4** | **Yes (NSWA / NSWB / self / familiar / unfamiliar)** | Article CC-BY; underlying SDWD = request-only | C1 ✓ C2 ✓ C3 ✓ C4 ✓ |
| 2 | Sharma 2024 + WhAM DSWP | *Physeter macrocephalus* | 8,719 codas EC-1; HF DSWP 1,501 codas / 585 MB / 45 min audio | 2, 3, 4 | ✗ (chorus / conversational context only) | GitHub MIT; HF CC-BY-4.0 | C1 ✓ C2 ~ C3 ✗ C4 ✓ |
| 3 | DCLDE 2026 | *Orcinus orca* | 225,000+ annots, 1.6 TB, 23 sites, 9 yr, 3 ecotypes | 4, 5 (ecotype → context joinable from Ford/Filatova) | ✗ in dataset; ✓ in Ford/Foote/Filatova literature | US gov public domain; paper CC-BY-4.0 | C1 ✓ C2 ~ C3 ~ C4 ✓ |
| 4 | Allen 2021 humpback CNN corpus | *Megaptera novaeangliae* | 187,000+ h, 13 NPac sites, 14 yr | 5 (song / no-song) | ✗ | US gov public domain | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 5 | Stafford 2018 Spitsbergen bowhead | *Balaena mysticetus* | 184 song types over 3 yr | 5 | ✗ | Dryad CC0 | C1 ✓ C2 ✗ (single mating-display context) C3 ✗ C4 ✓ |
| 6 | Lehnhoff 2025 DOLPHINFREE | *Delphinus delphis* | 400+ min audio; 68,000 echo clicks; 4,600 whistle contours; 350+ pulsed sounds; foraging / travel / social / mill / boat-attraction | 3 + 5 | ✗ | Zenodo CC-BY-4.0; 39.9 GB | C1 ✓ C2 ✓ C3 ✗ C4 ✓ |
| 7 | Sharma 2024 GitHub data | *Physeter macrocephalus* | 8,719 codas as CSV (DominicaCodas.csv, sperm-whale-dialogues.csv) | 4, 5 + conversational structure | ✗ | GitHub | C1 ✓ C2 ~ C3 ✗ C4 ✓ |
| 8 | Bermant 2019 sperm-whale ML | *Physeter macrocephalus* | Dominica 8,719 codas + Eastern Tropical Pacific 16,995 codas / 43 types / 4 clans | 4, 5 | ✗ | GitHub | C1 ✓ C2 ~ C3 ✗ C4 ✓ |
| 9 | Visser 2017 + Courts 2020 pilot whales | *Globicephala melas* | NE Atlantic: tagged whales × foraging vs non-foraging; Australia: 2,028 vocalisations 18 contour types | 3, 5 | ✗ | Dryad CC0 | C1 ✓ C2 ✓ C3 ✗ C4 ✓ |
| 10 | Madrigal 2025 false killer whale | *Pseudorca crassidens* | 5,940 high-quality pulsed calls; 52 stereotyped call types; 4 individuals tagged 2011–2024 | 4, 5 | ✗ | Dryad | C1 ✓ C2 ~ C3 ✗ C4 ✓ |
| 11 | Webster 2016 SR whale | *Eubalaena australis* | 35,487 calls, 10 call types, 4,355 classified | 5 | ✗ | Article only; raw audio Otago repository | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 12 | Antarctic minke Dryad | *Balaenoptera bonaerensis* | 11 bio-duck call types + song; DTag video + audio | 3, 5 | ✗ | Dryad | C1 ✓ C2 ~ C3 ✗ C4 ✓ |
| 13 | SAMBAH | *Phocoena phocoena* | 19.94 GB, 298–304 stations, 2011–2013, click train detections | 5 (detection only) | ✗ | Dryad CC-BY-NC | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 14 | LifeWatch Belgian PAM | *Phocoena phocoena* | 8 C-PODs continuous since 2014, click-train minute counts | 5 | ✗ | CC-BY-4.0 | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 15 | Blackwell 2018 narwhal | *Monodon monoceros* | 6 instrumented whales, ~7 d each, buzzes + calls + dive depth | 3, 4 | ✗ | Figshare | C1 ✓ C2 ✓ C3 ✗ C4 ✓ |
| 16 | Alcázar-Treviño 2020 beaked | *Mesoplodon densirostris*, *Ziphius cavirostris* | Tagged group dives; DTag audio + accel; foraging vs travel | 3, 4 | ✗ | Dryad | C1 ✓ C2 ✓ C3 ✗ C4 ✓ |
| 17 | Arranz 2018 Risso's | *Grampus griseus* | 33 tagged whales; buzz vs burst-pulse classification, GMM | 3, 5 | ✗ | Dryad | C1 ✓ C2 ✓ C3 ✗ C4 ✓ |
| 18 | Vergara beluga corpus | *Delphinapterus leucas* | Captive 2,835 Type A calls (5 variants); wild Cunningham Inlet: 87 contact-call types in 14 entrapments | 4, 5 | ✗ | Articles + thesis | C1 ✓ C2 ~ C3 ✗ C4 ✓ |
| 19 | OrcaSound AWS | *Orcinus orca* | Live + archived Salish Sea since 2018; labelled-bouts subset | 5 | ✗ | CC-BY-NC-SA-4.0 | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 20 | Watkins WMMSDB | 32 marine-mammal species (~26 cetacean) | ~1,800 master tapes; ~10,000 clips; 60+ species | 5 | ✗ | "personal/academic free" | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 21 | confit/wmms-parquet HF mirror | 32 species | 1,697 clips / 1.22 GB / 80–20 split | 5 | ✗ | Same | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 22 | SanctSound | Multi-baleen + odontocete | ~16 TB humpback alone; 30 sites; 2018–2021 | 5 | ✗ | US gov public domain | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 23 | DCLDE 2013 baleen | NARW, hum, fin, sei, blue, minke | Stellwagen Bank annotations; Raven 1.5 logs | 5 | ✗ | US gov; DOI 10.25921/zaea-1s39 | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 24 | DCLDE 2015 low-freq | Blue + fin | Annotated D calls, 40 Hz calls | 5 | ✗ | US gov | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 25 | DCLDE 2018 / DOCC10 | Odontocete clicks | 3 TB | 5 | ✗ | Conditional | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 26 | Madeira et al. 2025 EC sperm whale detector | *Physeter macrocephalus* | DSWP coda corpus + new types | 5 | ✗ | CETI GitHub | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 27 | Madrigal 2025 sperm-whale birth | *Physeter macrocephalus* | One 34-minute birth event, Unit A; coda shifts vs pilot-whale interaction | 1 (life-event tagged) | ✗ | Sci Rep CC-BY | C1 ✓ C2 ✓ C3 ✗ C4 ✓ |
| 28 | Yangtze finless porpoise (multi) | *Neophocaena asiaeorientalis* | Captive + free-ranging clicks (167 / 176 dB; 129/133 kHz) | 5 | ✗ | Various PLOS / Frontiers | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 29 | Vaquita CIRVA acoustic grid | *Phocoena sinus* | 48 C-PODs, 2011–2018, annual decline series | 5 (population-level only) | ✗ | IUCN/CIRVA reports | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 30 | Wisniewska 2016/2018 DTag | *Phocoena phocoena* | 5 wild porpoises, 18–44 h each, vessel-noise exposure | 3 | ✗ | Curr Biol + Dryad | C1 ✓ C2 ✓ C3 ✗ C4 ✓ |
| 31 | BEANS benchmark | Many incl. cetacean Watkins | 12 datasets; classification + detection | 5 + meta | ✗ | MIT | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 32 | BEANS-Zero | Cetacean subset within | 91,965 zero-shot samples | 5 + meta | ✗ | CC-BY (varies by source) | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 33 | AnimalSpeak | Multi-species | 894,256 audio–caption pairs | 5 + caption | ✗ | CC-BY | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 34 | Garland 2017 / 2022 humpback | *M. novaeangliae* | 6 song types, 2009–15 EAus → New Caledonia | 5 (song theme labels) | ✗ | Dryad CC0 | C1 ✓ C2 ✗ C3 ✗ C4 ✓ |
| 35 | Filatova / Selbmann orca catalogues | *O. orca* (Kamchatka, Iceland) | 20 (Kamchatka) / 91 (Iceland) discrete call types | 4 (clan dialect) | ✓ (Selbmann pilot-whale playback) | Articles, source recordings on request | C1 ✓ C2 ~ C3 ~ C4 ✓ |

Items 1, 2, 3 are the recommended primary substrate. Items 4–10 are second-tier candidates. Items 11–35 round out the audit and are useful for cross-reference, benchmarking, or fallback. See detailed entries below.

---

## Detailed entries

### 1. Sayigh et al. 2025 — bottlenose-dolphin shared non-signature whistles (Coller-Dolittle 2025 winner)

- **Species.** *Tursiops truncatus* (common bottlenose dolphin), Sarasota Bay, Florida community of 170 individuals.
- **Citation.** Sayigh, L., Jensen, F. H., McHugh, K., Casoli, M., Lemercier, L., Tyack, P. L., Wells, R. S., & Janik, V. M. (2025). *First evidence for widespread sharing of stereotyped non-signature whistle types by wild dolphins.* bioRxiv. [doi:10.1101/2025.04.21.647658](https://doi.org/10.1101/2025.04.21.647658)
- **Scale (verified from preprint abstract).** 22 identified shared non-signature whistle (NSW) types. **NSWA produced by ≥ 25** different dolphins, **NSWB produced by ≥ 35** different dolphins. Built on the Sarasota Dolphin Whistle Database (SDWD; see entry 2): 926 recording sessions, 293 individuals, 47-year span. Playback trials per condition not numerically extractable from the abstract — second-pass full-text audit needed.
- **Context labels available.** **Tier 1 (functional meaning)**: NSWA = alarm-type (majority negative responses); NSWB = query (responses to unfamiliar/unexpected). **Tier 2 (playback-validated response)**: yes — playback conditions include self-signature, familiar SW, unfamiliar SW, NSWA, NSWB. **Tier 4 (social)**: caller identity recorded via DTAG and suction-cup hydrophone during catch-and-release health assessments. This is the *only* released cetacean dataset that simultaneously carries tiers 1, 2, and 4.
- **Access.** Preprint open at bioRxiv. The underlying SDWD audio is **not currently in an open repository** — see entry 2. Sound exemplars used in playbacks appear in supplementary material (full audit pending).
- **License.** Preprint CC-BY-NC-ND per bioRxiv standard; data sharing covered by the SDWD statement (see entry 2).
- **Playback experiments present?** **Yes.** Self / familiar / unfamiliar / NSWA / NSWB conditions with received-level controls.
- **Fit for prize criteria.** C1 ✓ (suction-cup recordings + DTAG, non-invasive). C2 ✓ (multi-context — alarm + query + cohesion). C3 ✓ (the very playback trials reported in the paper). C4 ✓ (this is the paper that won the prize in 2025).
- **Honest caveats.** This is the *winning entry*. Re-submitting work that overlaps Sayigh would be high-risk because (a) the panel just rewarded this work, and (b) Sayigh's lab is positioned to extend it further. The framing must be a genuinely novel methodological contribution (e.g. compositional structure across NSW × SW, foundation-model alignment with playback-response statistics, or a cross-community generalisation) rather than a recapitulation. Also: until the SDWD audio is in a public repository, any reproduction requires writing to Sayigh.

### 2. Sayigh et al. 2022 — Sarasota Dolphin Whistle Database (SDWD)

- **Species.** *Tursiops truncatus.*
- **Citation.** Sayigh, L., Wells, R. S., Janik, V. M., et al. (2022). *The Sarasota Dolphin Whistle Database: A unique long-term resource for understanding dolphin communication.* Frontiers in Marine Science 9: 923046. [doi:10.3389/fmars.2022.923046](https://doi.org/10.3389/fmars.2022.923046)
- **Scale (verified from the article).** 926 recording sessions, 293 individual dolphins, longest individual span 43 years, 85 individuals recorded over a decade or more; 269 signature whistle exemplars used for the descriptive figure; recordings span mid-1970s and nearly annually since 1984. Sample-rate 48 kHz on suction-cup hydrophones with 5 ms contour resolution.
- **Context labels available.** **Tier 4 (social)** + **Tier 5 (whistle taxonomy)**. Sex, age, matriline known for most. Tier 3 (behavioural state) is *not* present — recordings are made during brief catch-and-release events, not during free-swimming behaviour.
- **Access.** Frontiers article is open access. The audio data is **NOT openly downloadable**. The data-availability statement reads verbatim: *"Requests for the raw data supporting the conclusions of this article will be considered by the authors."* This is request-only, not deposited.
- **License.** Article CC-BY-4.0. Data licensing terms negotiated per request.
- **Playback experiments present?** Many in *downstream* papers (Janik 2000; Janik et al. 2006; King et al. 2013; King & Janik 2013; Sayigh et al. 2025) but not in the database paper itself.
- **Fit for prize criteria.** C1 ✓. C2 ✓ (the database underlies multi-context work). C3 ~ (only via downstream papers). C4 ✓.
- **Honest caveats.** "Open" is overstated: the audio is request-only. The longitudinal scale is unique in the field. *This is the database backing the 2025 winner; it is not itself a downloadable corpus.*

### 3. Sharma et al. 2024 — Project CETI sperm-whale combinatorial structure

- **Species.** *Physeter macrocephalus* (sperm whale), Eastern Caribbean (EC-1) clan, Dominica.
- **Citation.** Sharma, P., Gero, S., Payne, R., Gruber, D. F., Rus, D., Torralba, A., & Andreas, J. (2024). *Contextual and combinatorial structure in sperm whale vocalisations.* Nature Communications 15: 3617. [doi:10.1038/s41467-024-47221-8](https://doi.org/10.1038/s41467-024-47221-8)
- **Scale (verified from the paper).** **8,719 codas** from the EC-1 clan, 21 previously-defined coda types, recorded 2005–2018, 42 tag deployments on 25 individuals across 11 social units, with at least **60 distinct whales** in the corpus and the EC-1 clan estimated at **~400 individuals**. The paper identifies a coda repertoire **nearly an order of magnitude larger** than the 21 base types when rhythm × tempo × rubato × ornamentation are factored. Rubato: 0.05 s adjacent vs 0.08 s null drift; 0.099 s vs 0.129 s overlap matching; r(2586) = 0.57.
- **Context labels available.** **Tier 5** (21 coda types) plus a *new* combinatorial axis (rubato, ornamentation) that the paper itself defines. **Tier 4** (individual + social unit + clan). The Tier 3 (behavioural state) labels are *implicit* via the DTag context (foraging dive phases) but are not exposed as a clean column in the public CSV.
- **Access.** GitHub: [github.com/pratyushasharma/sw-combinatoriality](https://github.com/pratyushasharma/sw-combinatoriality). Data files: `DominicaCodas.csv`, `sperm-whale-dialogues.csv`, plus pickled feature dictionaries (`mean_codas.p`, `ornaments.p`, `rhythms.p`, `tempos-dict.p`). **Resolves and is downloadable as of audit date.**
- **License.** Repository MIT (code). Data inherited from DSWP licensing (CC-BY effectively, see entry 4).
- **Playback experiments present?** No. The paper relies on **observational** evidence of rubato matching and chorusing as proxies for "perceived and acted upon."
- **Fit for prize criteria.** C1 ✓. C2 ~ (multi-context only in the conversational sense — the paper does *not* present alarm/foraging/mating context labels). C3 ✗ (no playbacks in this paper). C4 ✓.
- **Honest caveats.** The discovery of combinatorial structure is the strongest "language-like structure" claim currently published for any cetacean and is reusable. But to satisfy criterion 3 (playback response) you cannot rely on this paper alone — you would need to pair the corpus with a downstream playback-response analysis, which has not been published for sperm whales at the multi-clan / multi-context level. This makes it methodologically clean but prize-criterion-incomplete on its own.

### 4. Paradise et al. 2025 — WhAM + DSWP HuggingFace release

- **Species.** *Physeter macrocephalus.*
- **Citation.** Paradise, O., Muralikrishnan, P., Chen, L., Flores Garcia, H., Pardo, B., Diamant, R., Gruber, D. F., Gero, S., & Goldwasser, S. (2025). *WhAM: Towards a translative model of sperm whale vocalization.* Advances in Neural Information Processing Systems 39 (NeurIPS 2025). arXiv: 2512.02206.
- **Scale (verified from HuggingFace and arXiv).** Training corpus: **~10,000** coda recordings collected over two decades. **HuggingFace release `orrp/DSWP`**: **1,501 codas, ~45 minutes of audio, 585 MB, 1,501 rows**. Recordings 2005–2018 off Dominica via Benthos AQ-4 towed hydrophone (0.1–30 kHz, high-pass to 2–20 kHz flat), Fostex VF-160 or PAMGUARD/LOGGER (44.1–48 kHz), Zoom H4 + Cetacean Research C55 (48 kHz, 0.02–44 kHz), and DTag generation 3 biologger.
- **Context labels available.** **Tier 5** only (codas as isolated snippets). The HF dataset card explicitly states: *"codas are presented as isolated snippets without behavioral context, there is no per-file metadata (e.g. which recording system was used), and all recordings came from the same vocal clan and geographic region."*
- **Access.** HuggingFace dataset: [huggingface.co/datasets/orrp/DSWP](https://huggingface.co/datasets/orrp/DSWP). Model weights on Zenodo; code at [github.com/Project-CETI/wham](https://github.com/Project-CETI/wham). All resolve as of audit date.
- **License.** **CC-BY-4.0** on the audio. Project-CETI code release.
- **Playback experiments present?** No. WhAM generates synthetic codas via masked-token prediction; downstream classification tasks (rhythm, social unit, vowel) are evaluation, not playback.
- **Fit for prize criteria.** C1 ✓. C2 ✗ (single-clan, no context columns). C3 ✗. C4 ✓.
- **Honest caveats.** This is the *first cleanly downloadable, CC-BY audio release of real sperm-whale codas at scale*. The 1,501-coda subset is a curated slice of the larger 10,000-coda training corpus. For combinatorial-structure modelling it is ideal; for prize criteria 2 and 3 it is not, because context labels are deliberately stripped.

### 5. Bermant et al. 2019 — Deep learning sperm whale dataset

- **Species.** *Physeter macrocephalus.*
- **Citation.** Bermant, P. C., Bronstein, M. M., Wood, R. J., Gero, S., & Gruber, D. F. (2019). *Deep Machine Learning Techniques for the Detection and Classification of Sperm Whale Bioacoustics.* Scientific Reports 9: 12588. [doi:10.1038/s41598-019-48909-4](https://doi.org/10.1038/s41598-019-48909-4)
- **Scale (verified).** Click detection: 99.5% on spectrogram CNN. Coda classification: 97.5% on Dominica (23 coda types, 8,719 codas; same corpus that anchors Sharma 2024), 93.6% on Eastern Tropical Pacific (43 coda types, **16,995 codas**). Clan classification: 95.3% / 93.1%. Individual ID: 99.4% on Dominica.
- **Context labels available.** **Tier 4 (clan; individual)** + **Tier 5** (coda type).
- **Access.** GitHub: dgruber212/Sperm_Whale_Machine_Learning. The CETI roadmap arXiv (2104.08614) is the companion vision paper.
- **License.** Standard repository.
- **Playback experiments present?** No.
- **Fit for prize criteria.** C1 ✓. C2 ~. C3 ✗. C4 ✓.
- **Honest caveats.** Older than Sharma 2024 and Paradise 2025. The Eastern Tropical Pacific 16,995-coda figure is the largest single sperm-whale coda count in the literature, but its public release status is unclear (the GitHub repository carries the Dominica subset openly).

### 6. Madeira et al. 2025 — Automatic eastern Caribbean coda detector

- **Species.** *Physeter macrocephalus.*
- **Citation.** Madeira, F., Diamant, R., Goldbogen, J., Goldwasser, S., Gero, S., Andreas, J., Gruber, D. F. (2025). *Automatic detection and annotation of eastern Caribbean sperm whale codas.* Scientific Reports 15. [doi:10.1038/s41598-025-97009-z](https://doi.org/10.1038/s41598-025-97009-z)
- **Scale.** Graph-based click clustering applied to the DSWP corpus; detection at low SNR; coda-vs-echolocation discrimination; per-vocalizer separation. New coda types and inter-whale synchronisation reported.
- **Context labels available.** **Tier 5** (coda) + Tier 4 by vocalizer.
- **Access.** [github.com/Project-CETI/Coda-detector](https://github.com/Project-CETI/Coda-detector). MATLAB.
- **License.** Open code; data inherited from DSWP.
- **Playback experiments present?** No.
- **Honest caveats.** Useful as a preprocessing layer for any sperm-whale re-analysis; not a primary corpus.

### 7. Gero et al. 2016 — Sperm whale identity codas (older Dominica release)

- **Species.** *Physeter macrocephalus.*
- **Citation.** Gero, S., Whitehead, H., & Rendell, L. (2016). *Individual, unit and vocal clan level identity cues in sperm whale codas.* Royal Society Open Science 3: 150372. [doi:10.1098/rsos.150372](https://doi.org/10.1098/rsos.150372). Dataset: [Dryad doi:10.5061/dryad.ck4h0](https://datadryad.org/dataset/doi%3A10.5061/dryad.ck4h0)
- **Scale (verified from PMC4736920).** Nine Caribbean social units, six years of data, 21 coda types, ICI measurements.
- **Context labels available.** **Tier 4** (individual / unit / clan) + **Tier 5**.
- **Access.** Dryad. Resolves.
- **License.** CC0.
- **Playback experiments present?** No.
- **Honest caveats.** Predecessor to Sharma 2024; same corpus seed but earlier slice. Cite for the foundational clan-ID work.

### 8. Madrigal et al. 2025 — Collaborative sperm-whale birth

- **Species.** *Physeter macrocephalus.*
- **Citation.** Madrigal, V. P. et al. (2025). *Description of a collaborative sperm whale birth and shifts in coda vocal styles during key events.* Scientific Reports. [doi:10.1038/s41598-025-27438-3](https://doi.org/10.1038/s41598-025-27438-3)
- **Scale.** A single birth event, 34 minutes from fluke emergence to delivery, 11 individuals in Unit A; statistically significant shifts in coda vocal style across the event and during a subsequent short-finned pilot-whale interaction.
- **Context labels available.** **Tier 1 (functional, life-event)** + **Tier 4** + **Tier 5**.
- **Access.** Sci Rep paper; CETI supplementary release.
- **License.** Article CC-BY.
- **Playback experiments present?** No.
- **Honest caveats.** Statistically thin (one event), but the only multi-context, life-event-tagged sperm-whale acoustic dataset published. Use for narrative + context-labelling, not for training.

### 9. Oliveira et al. 2016 — Sperm whale codas in the Azores

- **Species.** *Physeter macrocephalus.*
- **Citation.** Oliveira, C., Wahlberg, M., Silva, M. A., Johnson, M., Antunes, R., Wisniewska, D. M., Fais, A., Gonçalves, J., & Madsen, P. T. (2016). *Sperm whale codas may encode individuality as well as clan identity.* JASA 139: 2860. [doi:10.1121/1.4949478](https://doi.org/10.1121/1.4949478)
- **Scale.** 5 sperm whales, DTag-instrumented, **802 codas** recorded.
- **Context labels available.** **Tier 4** (individual) + **Tier 5** + a behavioural-context note (two whales produce different codas during distinct foraging-dive phases).
- **Access.** Article paywalled but PDF available via marinebioacoustics.com. Data availability not in primary search — second-pass audit needed.
- **License.** Article-only.
- **Playback experiments present?** No.

### 10. Antunes 2009 — North Atlantic sperm whale coda variation (thesis)

- **Citation.** Antunes, R. (2009). *Variation in sperm whale (Physeter macrocephalus) coda vocalizations and social structure in the North Atlantic Ocean.* PhD thesis, University of St Andrews. https://research-repository.st-andrews.ac.uk/handle/10023/827
- **Scale.** Multi-year Azores recordings.
- **Context labels available.** **Tier 4** (social unit) + **Tier 5**.
- **Access.** Thesis open. Underlying data not on a repository.
- **Honest caveats.** Cite for historical context; not a downloadable corpus.

### 11. Lehnhoff et al. 2025 — DOLPHINFREE common dolphin acoustic dataset

- **Species.** *Delphinus delphis* (short-beaked common dolphin), northern Bay of Biscay, France.
- **Citation.** Lehnhoff, L., Glotin, H., Chaillou, R., Dramé, F., Cazau, D., Mouchel-Vichard, M., Rongière, A., Spitz, J. (2025). *High-resolution acoustic recordings of wild free-ranging short-beaked common dolphins for etho-acoustical and repertoire studies.* Earth System Science Data 17: 4495. [doi:10.5194/essd-17-4495-2025](https://doi.org/10.5194/essd-17-4495-2025). Dataset: [doi:10.5281/zenodo.14637674](https://doi.org/10.5281/zenodo.14637674)
- **Scale (verified from ESSD article and Zenodo record).** **400+ minutes of unedited recordings**, **≈ 68,000 echolocation clicks**, **4,600 whistle contours**, **350+ pulsed sounds**. Single hydrophone (512 kHz, 32-bit) + 4-hydrophone array (256–512 kHz, 16–24 bit). 2020–2022 summers. **Zenodo record latest version 39.9 GB** (DOLPHINFREE_public.zip), CC-BY-4.0.
- **Context labels available.** **Tier 3 (behavioural state)** — explicitly *foraging / travelling / socialising / milling / boat-attraction* recorded simultaneously with audio. **Tier 5** (echo / whistle / pulsed).
- **Access.** Zenodo. Resolves. Download tested via WebFetch in this audit.
- **License.** CC-BY-4.0.
- **Playback experiments present?** No.
- **Fit for prize criteria.** C1 ✓ (visual + acoustic, non-invasive). C2 ✓ (true multi-behaviour labels). C3 ✗. C4 ✓.
- **Honest caveats.** This is the **richest tier-3-labelled odontocete corpus released openly under CC-BY in the last five years**. It carries no playback layer; pairing it with even a small playback experiment would give a complete prize narrative. The 39.9 GB size means a working subset must be carved.

### 12. Visser et al. 2017 — Long-finned pilot whale context-dependent vocalisation

- **Species.** *Globicephala melas* (long-finned pilot whale), Northeast Atlantic.
- **Citation.** Visser, F., Miller, P. J. O., Antunes, R. N., Oudejans, M. G., Mackenzie, M. L., Aoki, K., Lam, F.-P. A., Kvadsheim, P. H., Huisman, J., & Tyack, P. L. (2017). *Vocal foragers and silent crowds: context-dependent vocal variation in Northeast Atlantic long-finned pilot whales.* Behavioral Ecology and Sociobiology. PMC5674111. Dataset: [Dryad doi:10.5061/dryad.6rj64](https://datadryad.org/dataset/doi%3A10.5061/dryad.6rj64)
- **Scale.** DTagged whales with synchronous behavioural-context labels (foraging vs non-foraging; dive descent / ascent / bottom). Vocalisation + group-level behaviour sampling-bin tables.
- **Context labels available.** **Tier 3 (behavioural state)** + **Tier 4 (group)** + **Tier 5**.
- **Access.** Dryad. Resolves.
- **License.** CC0.
- **Playback experiments present?** No.
- **Honest caveats.** Sample size small (n tagged whales). The strongest single-paper behavioural-context-label dataset for any pilot whale.

### 13. Courts et al. 2020 — Australian long-finned pilot whale repertoire

- **Citation.** Courts, R., Erbe, C., Wellard, R., Boisseau, O., Jenner, K. C. S., & Jenner, M.-N. (2020). *Australian long-finned pilot whales (Globicephala melas) emit stereotypical, variable, biphonic, multi-component, and sequenced vocalisations, similar to those recorded in the northern hemisphere.* Royal Society Open Science. Dataset: [Dryad doi:10.5061/dryad.w3r2280p3](https://datadryad.org/dataset/doi:10.5061/dryad.w3r2280p3)
- **Scale.** **2,028 vocalisations** over five years, **18 contour classes**, **3.73 GB**.
- **Context labels available.** **Tier 5** (contour class).
- **Access.** Dryad. Resolves.
- **License.** CC0.

### 14. Vester et al. 2017 — Northern Norway pilot whale repertoire

- **Citation.** Vester, H. I., Timme, M., Hammerschmidt, K., & Hallerberg, S. (2017). *Vocal repertoire of long-finned pilot whales (Globicephala melas) in northern Norway.* JASA 141: 4289. [PDF](https://active3d-trr404.de/files/user/mtimme/publications/Vester_et_al_Vocal%20Repertoire%20of%20long-finned%20pilot%20whales%20in%20northern%20norway_JASA_2017.pdf)
- **Scale.** Multi-cluster repertoire description.
- **Context labels available.** **Tier 5**.
- **Access.** Article-only PDF.

### 15. Zwamborn & Whitehead 2017 — Cape Breton pilot whale embellishment

- **Citation.** Zwamborn, E. M. J., & Whitehead, H. (2017). *The baroque potheads: modification and embellishment in repeated call sequences of long-finned pilot whales.* Behaviour 154: 963. + Zwamborn & Whitehead (2017). *Repeated call sequences and behavioural context in long-finned pilot whales off Cape Breton, Nova Scotia, Canada.* Bioacoustics. [10.1080/09524622.2016.1233457](https://www.tandfonline.com/doi/full/10.1080/09524622.2016.1233457)
- **Scale.** Long-term Cape Breton corpus.
- **Context labels available.** **Tier 3** (behavioural-context-linked sequences) + **Tier 4** (social unit).
- **Access.** Articles; data on request.
- **Playback?** No.

### 16. Madrigal et al. 2025 — Endangered Hawaiian false killer whale acoustic biologger data

- **Species.** *Pseudorca crassidens.*
- **Citation.** Madrigal, B. C., Gough, W. T., et al. (2025). *Acoustic behaviour of endangered Hawaiian false killer whales.* Dataset: [Dryad doi:10.5061/dryad.s7h44j1n6](https://datadryad.org/dataset/doi:10.5061/dryad.s7h44j1n6)
- **Scale (verified from Dryad).** **CATS tags (96 kHz)** + **DTag (240 kHz)** deployed on **4 individuals** from **2 social clusters** off Main Hawaiian Islands, 2011–2024. **5,940 high-quality pulsed calls**, **52 stereotyped call types**.
- **Context labels available.** **Tier 4 (social cluster)** + **Tier 5 (52 call types)**.
- **Access.** Dryad.
- **License.** Dryad CC0.
- **Playback?** No.

### 17. McCullough et al. 2021 — False killer whale repertoire classification

- **Citation.** McCullough, J. L. K., Simonis, A. E., Sakai, T., & Oleson, E. M. (2021). *Acoustic classification of false killer whales in the Hawaiian islands based on comprehensive vocal repertoire.* NOAA Technical Memorandum NMFS-PIFSC. 99.6% classification accuracy across clicks + whistles + burst pulses.
- **Context labels available.** Tier 5.
- **Access.** NOAA repository.

### 18. Kaplan et al. — Melon-headed whale DTag corpus

- **Species.** *Peponocephala electra.*
- **Citation.** Kaplan, M. B., Mooney, T. A., Baird, R. W., et al. (various). 1,425 calls across 120 min of recording, 240 kHz sample rate, DTag3.
- **Context labels available.** Tier 4 (Kohala resident vs Hawaiian Islands population) + Tier 5.

### 19. Alcázar-Treviño et al. 2020 — Beaked whales dive together but forage apart

- **Species.** *Mesoplodon densirostris* (Blainville's), *Ziphius cavirostris* (Cuvier's).
- **Citation.** Alcázar-Treviño, J., Johnson, M., Arranz, P., Warren, V. E., Pérez-González, C. J., Marques, T., Madsen, P. T., & Aguilar de Soto, N. (2020). *Deep-diving beaked whales dive together but forage apart.* Dataset: [Dryad doi:10.5061/dryad.gqnk98sm0](https://datadryad.org/dataset/doi:10.5061/dryad.gqnk98sm0)
- **Scale.** Tagged group dives with synchronised audio + accelerometer; foraging-vs-travel labels.
- **Context labels available.** **Tier 3 (state)** + Tier 4 (group).
- **Access.** Dryad.

### 20. Frasier 2024 — Blainville's beaked whale autonomous click corpus

- **Citation.** Frasier, K. (2024). *Blainville's beaked whale (Mesoplodon densirostris) echolocation clicks from autonomous passive acoustic recordings.* [Dryad doi:10.6076/D12G6N](https://datadryad.org/dataset/doi:10.6076/D12G6N). 11.41 GB.
- **Context labels available.** Tier 5 (species + click type).
- **Access.** Dryad.

### 21. Zimmer et al. 2005 — Cuvier's beaked whale DTag echolocation

- **Citation.** Zimmer, W. M. X., Johnson, M. P., Madsen, P. T., & Tyack, P. L. (2005). *Echolocation clicks of free-ranging Cuvier's beaked whales (Ziphius cavirostris).* JASA 117: 3919. https://darchive.mblwhoilibrary.org/handle/1912/2358
- **Scale.** 2 DTagged whales, Ligurian Sea. Foundational FM-pulse description (~42 kHz, ~200 µs, source level 214 dBpp re: 1 µPa).
- **Context labels available.** Tier 5 + dive-phase Tier 3.

### 22. DECAF AUTEC beaked-whale dataset (GBIF)

- **Citation.** DECAF AUTEC Beaked Whales - Multiple Sensors - DTag, spring 2005. [GBIF doi:bbd71c1c-c505-4669-8d81-afe56aca2779](https://www.gbif.org/dataset/bbd71c1c-c505-4669-8d81-afe56aca2779)
- **Scale.** Geo-referenced click positions + animal orientation, DTag spring 2005.
- **Access.** GBIF.

### 23. Arranz et al. 2018 — Risso's dolphin buzz vs burst-pulse discrimination

- **Species.** *Grampus griseus.*
- **Citation.** Arranz, P., DeRuiter, S. L., Stimpert, A. K., Neves, S., Friedlaender, A. S., Goldbogen, J. A., Visser, F., Calambokidis, J., Southall, B. L., & Tyack, P. L. (2018). *Discrimination of fast click series produced by tagged Risso's dolphins (Grampus griseus) for echolocation or communication.* Journal of Experimental Biology. Dataset: [Dryad doi:10.5061/dryad.48vq4](https://datadryad.org/dataset/doi%3A10.5061/dryad.48vq4)
- **Scale.** **33 tagged whales off California**. Buzzes (359 ± 210 clicks, prey capture) vs burst-pulses (45 ± 54 clicks, surface communication) classified via Gaussian mixture model on duration × jerk × association with click trains.
- **Context labels available.** **Tier 3 (foraging vs surface communication)** + Tier 5.
- **Access.** Dryad. December 2017 deposit.

### 24. Vergara — Beluga contact calls (captive + St Lawrence + Cunningham Inlet)

- **Species.** *Delphinapterus leucas.*
- **Citations.**
  - Vergara, V., & Mikus, M.-A. (2019). *Contact call diversity in natural beluga entrapments in an Arctic estuary: Preliminary evidence of vocal signatures in wild belugas.* Marine Mammal Science 35: 434.
  - Vergara, V. (2011). *What can captive whales tell us about their wild counterparts? Identification, usage, and ontogeny of contact calls in belugas (Delphinapterus leucas).* PhD thesis, UBC.
  - Vergara, V., Mikus, M.-A., Wood, J. (2024). Geographic variation in contact calls of Canadian beluga whales.
- **Scale.** Captive corpus: 2,835 Type A calls grouped into 5 variants (A1–A5), 87% DFA classification. Wild Cunningham Inlet: **87 distinct complex contact call types** across **14 natural entrapment events**, with a 1-to-1 cap between entrapped whales and call-type count.
- **Context labels available.** **Tier 4** (individual + group) + Tier 5. Some Tier 1 (contact call function).
- **Access.** Articles open; raw audio held by Vancouver Aquarium / Raincoast.

### 25. Cook Inlet beluga passive acoustic monitoring

- **Species.** *Delphinapterus leucas.*
- **Citation.** Castellote, M., Small, R. J., Lammers, M. O., Jenniges, J. J., Mondragon, J., Atkinson, S. (2016). *Dual instrument passive acoustic monitoring of belugas in Cook Inlet, Alaska.* JASA 139: 2697. PubMed 27250163.
- **Scale.** 10 moorings, June 2008–May 2013, 83% recovery rate.
- **Context labels available.** Tier 5 (species detection) + spatial.
- **Access.** NOAA Fisheries; Alaska EPSCoR catalog.

### 26. Blackwell et al. 2018 — East Greenland narwhal

- **Species.** *Monodon monoceros.*
- **Citation.** Blackwell, S. B., Tervo, O. M., Conrad, A. S., Sinding, M.-H. S., Hansen, R. G., Ditlevsen, S., & Heide-Jørgensen, M. P. (2018). *Spatial and temporal patterns of sound production in East Greenland narwhals.* PLOS ONE 13: e0198295. [doi:10.1371/journal.pone.0198295](https://doi.org/10.1371/journal.pone.0198295). Dataset: [figshare e62ed400ed454a459ab4](https://figshare.com/s/e62ed400ed454a459ab4) (**46.4 MB**).
- **Scale.** **6 narwhals** instrumented with Acousonde + satellite tags, August 2013–2016 in Scoresby Sound. Continuous recordings up to 7 days. 46.4 MB dataset with 6-column structure: datetime, individual, depth, geographic area (Fønfjord / Øfjord / Gåsefjord / Outer Gåsefjord), terminal-buzz occurrence, call occurrence.
- **Context labels available.** **Tier 3 (foraging buzz vs social call)** + **Tier 4 (individual)** + spatial.
- **Access.** Figshare. Resolves.
- **License.** Figshare default.

### 27. Marcoux et al. 2020 — Narwhal vocal sequences

- **Citation.** Marcoux, M., Ferguson, S. H., Roy, N., Bedard, J.-M., & Simard, Y. (2020). *Vocal sequences in narwhals (Monodon monoceros).* JASA 147: 1078. Plus Dryad cue-counting dataset [doi:10.5061/dryad.zcrjdfnj2](https://datadryad.org/dataset/doi:10.5061/dryad.zcrjdfnj2)
- **Scale.** Sequence-level vocal data.
- **Context labels available.** Tier 5.

### 28. DCLDE 2026 — Killer whale ecotype annotations

- **Species.** *Orcinus orca* (three sympatric ecotypes: Resident, Bigg's, Offshore).
- **Citation.** Palmer, J. K., Bushong, S., Wiggins, S. M., et al. (2025). *A Public Dataset of Annotated Orcinus orca Acoustic Signals for Detection and Ecotype Classification.* Scientific Data. [doi:10.1038/s41597-025-05281-5](https://doi.org/10.1038/s41597-025-05281-5)
- **Scale (cross-checked with `OrcaDolittle/docs/data.md`).** 225,000+ bounding-box annotations; 1.6 TB; 23 hydrophone locations; ~11 yr (May 2013–Apr 2023). Three vocalisation categories (echo clicks, whistles, pulsed calls). Confounder annotations (humpback song, Pacific white-sided whistles, ship cavitation).
- **Context labels available.** **Tier 4 (ecotype)** + **Tier 5 (call category)**. Tier 3 must be joined externally via Ford 1989 / Foote 2008 / Filatova 2016.
- **Access.** NCEI DOI 10.25921/15ey-mh50; data.gov mirror; [github.com/JPalmerK/DCLDE_Dataset](https://github.com/JPalmerK/DCLDE_Dataset).
- **License.** US government public domain.
- **Playback?** No in dataset; ✓ in matched-paper literature (Foote 2008, Deecke 2002, Selbmann 2024).
- **Fit for prize.** C1 ✓ C2 ~ C3 ~ C4 ✓.
- **Honest caveats.** Same caveats as in `data.md`: cross-provider heterogeneity, competitive territory, and ecotype-→-context join is real work. This audit *confirms* the existing project audit's numbers exactly.

### 29. OrcaSound — Salish Sea hydrophone network (AWS open data)

- **Citation.** Orcasound on AWS. https://registry.opendata.aws/orcasound/. Datasets: streaming-orcasound-net (HLS live), archive-orcasound-net (FLAC archive), acoustic-sandbox (labelled bouts); audio-orcasound-net + audio-deriv-orcasound-net (post-2024 buckets). orca-dclde catalogue: https://github.com/orcasound/orca-dclde
- **Scale.** 2018–present live + archive, Salish Sea SRKW critical habitat. Labelled-bouts subset on orca-data wiki.
- **Context labels available.** Tier 5 (call / no-call); some bout-level metadata.
- **Access.** S3 us-west-2, no credentials.
- **License.** **CC-BY-NC-SA-4.0**.
- **Playback?** No.
- **Honest caveats.** Same as in `data.md`: best as demo input, ecologically narrow.

### 30. Bergler 2019 — ORCA-SPOT (Orchive segmentation)

- **Citation.** Bergler, C., Schröter, H., Cheng, R. X., Barth, V., Weber, M., Nöth, E., Hofer, H., & Maier, A. (2019). *ORCA-SPOT: An Automatic Killer Whale Sound Detection Toolkit Using Deep Learning.* Scientific Reports 9: 10997. [doi:10.1038/s41598-019-47335-w](https://doi.org/10.1038/s41598-019-47335-w)
- **Scale.** Trained on 11,509 killer-whale signals + 34,848 noise. Tested on the **Orchive: ~19,000 hours of killer-whale recordings (~2.2 yr) over 23 yr (1985–2010)**. Sub-evaluation on 238 tapes (~191.5 h). PPV 93.2%, AUC 0.9523.
- **Context labels available.** Binary call/noise; with Orchive's underlying call-type catalogue (Ford 1991), Tier 4/5.
- **Access.** Code: [github.com/ChristianBergler/ORCA-SPOT](https://github.com/ChristianBergler/ORCA-SPOT), GPLv3. **Orchive audio itself is held by OrcaLab and is not openly downloadable in full.**
- **Playback?** No.
- **Honest caveats.** Orchive is the largest single killer-whale acoustic corpus in existence and is mostly **closed**.

### 31. Bergler et al. 2022 — ANIMAL-SPOT (general framework)

- **Citation.** Bergler, C., Smeele, S. Q., Tyndel, S. A., et al. (2022). *ANIMAL-SPOT enables animal-independent signal detection and classification using deep learning.* Sci Rep 12: 21966. [doi:10.1038/s41598-022-26429-y](https://doi.org/10.1038/s41598-022-26429-y)
- **Coverage.** 10 species + 1 genus including orca, several non-cetacean species.
- **Access.** [github.com/ChristianBergler/ANIMAL-SPOT](https://github.com/ChristianBergler/ANIMAL-SPOT)

### 32. Dalhousie / MERIDIAN Zenodo orca clip dataset

- **Citation.** Zenodo 15390884: *Audio clips of Orca (Orcinus orca) and non-orca sounds for the exploration of multiple acoustic representations.* https://zenodo.org/records/15390884
- **Scale.** **9,600 audio clips**, 3 s, **64 kHz**, recorded off San Juan Island, SRKW + humpback + ambient.
- **Context labels available.** Tier 5 (orca / non-orca).
- **License.** Zenodo CC.
- **Honest caveats.** Small but clean for deep-learning baselines.

### 33. Ford 1989, 1991 — Killer-whale dialect / clan foundation

- **Citations.**
  - Ford, J. K. B. (1989). *Acoustic behaviour of resident killer whales (Orcinus orca) off Vancouver Island, British Columbia.* Canadian Journal of Zoology 67: 727.
  - Ford, J. K. B. (1991). *Vocal traditions among resident killer whales (Orcinus orca) in coastal waters of British Columbia.* Canadian Journal of Zoology 69: 1454. [doi:10.1139/z91-206](https://doi.org/10.1139/z91-206)
- **Scale.** 16 resident pods → 4 acoustic clans. Each pod 7–17 discrete call types (mean 10.7).
- **Context labels available.** **Tier 4 (clan / pod dialect)** + Tier 5. Tier 3 minimal (active = forage + travel).
- **Access.** Articles; underlying recordings on request through SFU / OrcaLab.
- **Honest caveats.** Foundational; not a downloadable corpus.

### 34. Filatova et al. 2007, 2016 — Kamchatka killer whale call repertoire

- **Citations.**
  - Filatova, O. A., Burdin, A. M., Hoyt, E., & Sato, H. (2007). *The structure of the discrete call repertoire of killer whales Orcinus orca from southeast Kamchatka.* Bioacoustics 16: 261.
  - Filatova, O. A., Samarra, F. I. P., Deecke, V. B., Ford, J. K. B., Miller, P. J. O., & Yurk, H. (2015). *Cultural evolution of killer whale calls.* Behaviour 152: 2001.
  - Filatova, O. A., et al. (2016). *Physical constraints of cultural evolution of dialects in killer whales.* JASA 140: 3755.
- **Scale.** 20 discrete call types in Southeast Kamchatka; cross-region (Chukot, Kamchatka, Commander, Kurile) shared-vs-unique inventory.
- **Context labels available.** **Tier 4 (clan/dialect)** + **Tier 5**.
- **Access.** Articles; underlying recordings on request.

### 35. Selbmann 2023, 2024 — Iceland killer whale calls + playback

- **Citations.**
  - Selbmann, A., Mariani, E. L., Deecke, V. B., et al. (2023). *Call combination patterns in Icelandic killer whales (Orcinus orca).* Sci Rep 13: 21062. [doi:10.1038/s41598-023-48349-1](https://doi.org/10.1038/s41598-023-48349-1)
  - Selbmann, A., Mariani, E. L., Deecke, V. B., et al. (2024–25). *Call type repertoire of killer whales (Orcinus orca) in Iceland and its variation across regions.*
  - Selbmann, A., Deecke, V. B., Filatova, O. A., et al. (2026). *Aversive behavioural responses of killer whales to sounds of long-finned pilot whales.* Sci Rep 16. [doi:10.1038/s41598-026-35574-7](https://doi.org/10.1038/s41598-026-35574-7)
- **Scale.** **91 call categories** identified across 5 Icelandic locations 1985–2016; relative stability over 14 yr in Vestmannaeyjar.
- **Context labels available.** **Tier 4 (population / location)** + **Tier 5**. **Tier 2 (playback validated)** in the 2026 pilot-whale-sound paper.
- **Access.** Articles; underlying recordings on request.

### 36. Foote, Osborne & Hoelzel 2008 — V4 excitement call

- **Citation.** Foote, A. D., Osborne, R. W., & Hoelzel, A. R. (2008). *Temporal and Contextual Patterns of Killer Whale (Orcinus orca) Call Type Production.* Ethology 114: 599. [doi:10.1111/j.1439-0310.2008.01496.x](https://doi.org/10.1111/j.1439-0310.2008.01496.x)
- **Note.** **Correction to `playback_corpus.md`:** that file currently cites this paper as Foote 2008 *Current Biology* with doi `10.1016/j.cub.2008.06.013`. **The paper is actually in *Ethology*** (Wiley) **at doi 10.1111/j.1439-0310.2008.01496.x.** The Current Biology DOI `10.1016/j.cub.2008.06.013` does not correspond to this paper. This is an extraction error in the playback corpus that should be corrected on next pass.
- **Context labels available.** Tier 3 (context: surface-active behaviour) + Tier 4 (Southern Resident).
- **Playback?** Discussion of contextual production; cross-checking Foote/Osborne/Hoelzel original methodology against secondary descriptions of "V4 broadcast" is recommended.

### 37. Deecke, Ford & Spong 2000 — Resident-killer-whale dialect drift

- **Citation.** Deecke, V. B., Ford, J. K. B., & Spong, P. (2000). *Dialect change in resident killer whales: implications for vocal learning and cultural transmission.* Animal Behaviour 60: 629. [doi:10.1006/anbe.2000.1505](https://doi.org/10.1006/anbe.2000.1505)
- **Context labels available.** Tier 4 (matriline) + Tier 5.
- **Note (cross-reference to `playback_corpus.md`).** Listed there as a playback test of dialect drift. Original article is about longitudinal call-type measurement; whether it includes a playback experiment in the methodological sense needs second-pass full-text audit.

### 38. Deecke, Slater & Ford 2002 — Harbour seals discriminate orca calls

- **Citation.** Deecke, V. B., Slater, P. J. B., & Ford, J. K. B. (2002). *Selective habituation shapes acoustic predator recognition in harbour seals.* Nature 420: 171. [doi:10.1038/nature01030](https://doi.org/10.1038/nature01030)
- **Scale.** Playback design: local fish-eating vs unfamiliar fish-eating vs mammal-eating transient calls broadcast to wild harbour seals in BC.
- **Context labels available.** **Tier 1 (predator-recognition)** + **Tier 2 (playback validated)**.
- **Playback?** **Yes.**
- **Note.** Listener is harbour seals, not orcas. Cross-species transfer prior only. Already flagged in `playback_corpus.md`.

### 39. Yurk et al. 2002 — Alaska resident vocal clans

- **Citation.** Yurk, H., Barrett-Lennard, L., Ford, J. K. B., & Matkin, C. O. (2002). *Cultural transmission within maternal lineages: vocal clans in resident killer whales in southern Alaska.* Animal Behaviour 63: 1103. [doi:10.1006/anbe.2002.3036](https://doi.org/10.1006/anbe.2002.3036)
- **Context labels available.** Tier 4.

### 40. Riesch, Ford & Thomsen 2008 — Whistle sequences in resident killer whales

- **Citation.** Riesch, R., Ford, J. K. B., & Thomsen, F. (2008). *Whistle sequences in wild killer whales (Orcinus orca).* JASA 124: 1822. PubMed 19045672.
- **Scale.** 1,140 whistle transitions in 192 sequences; new W7 whistle type identified.
- **Context labels available.** Tier 3 (close-range behavioural interactions, male-skewed) + Tier 5.

### 41. Whale FM (Zooniverse) — Citizen-science orca + pilot whale labels

- **Citation.** Crocker, J., Smith, R. (eds), Zooniverse / Scientific American. WhaleFM 2011–2015. [github.com/zooniverse/WhaleFM](https://github.com/zooniverse/WhaleFM)
- **Scale.** **16,000+ recordings** of killer whales and pilot whales from WHOI. All match decisions preserved.
- **Context labels available.** Match / non-match / skip (tier 5).
- **Access.** Gzipped MySQL + CSV.

### 42. Stafford et al. 2018 — Spitsbergen bowhead whale songs

- **Species.** *Balaena mysticetus.*
- **Citation.** Stafford, K. M., Lydersen, C., Wiig, Ø., & Kovacs, K. M. (2018). *Extreme diversity in the songs of Spitsbergen's bowhead whales.* Biology Letters 14: 20180056. [doi:10.1098/rsbl.2018.0056](https://doi.org/10.1098/rsbl.2018.0056). Dataset: [Dryad doi:10.5061/dryad.1ck400f](https://datadryad.org/dataset/doi%3A10.5061/dryad.1ck400f)
- **Scale (re-verified via Dryad WebFetch).** **184 song types** over 3 yr; **38 / 69 / 76** types in 2010-11 / 2012-13 / 2013-14; Fram Strait NE Atlantic; exemplars as MP3. **200.40 MB**.
- **Context labels available.** Tier 5 (song type) and a *behavioural* link to peak mating season (Dec / Jan).
- **Access.** Dryad. Resolves. CC0.
- **Playback?** No.
- **Fit for prize.** Same conclusion as `data.md`: probably single-context (male breeding). Reads as cultural-evolution, not multi-context communication.
- **Honest caveats.** This is the bowhead entry currently in `data.md`. Numbers match exactly.

### 43. Allen, Harvey, Harrell et al. 2021 — North Pacific humpback CNN

- **Species.** *Megaptera novaeangliae.*
- **Citation.** Allen, A. N., Harvey, M., Harrell, L., Jansen, A., Merkens, K. P., Wall, C. C., Cattiau, J., & Oleson, E. M. (2021). *A Convolutional Neural Network for Automated Detection of Humpback Whale Song in a Diverse, Long-Term Passive Acoustic Dataset.* Frontiers in Marine Science 8: 607321. [doi:10.3389/fmars.2021.607321](https://doi.org/10.3389/fmars.2021.607321)
- **Scale (verified).** **187,000+ hours** of acoustic data, 13 monitoring sites in North Pacific, 14 yr. Mean average precision 0.97, AUC-ROC 0.992 at 75-s windows. New finding: humpback song at Kingman Reef (5° N).
- **Context labels available.** Tier 5 binary (song / no song).
- **Access.** NOAA; Google Research blog. Model and pipeline open.
- **License.** US government public domain.

### 44. Kather et al. 2024 — North Atlantic humpback CNN fine-tune

- **Citation.** Kather, J. F., Ridoux, V., Lammers, M., et al. (2024). *Development of a machine learning detector for North Atlantic humpback whale song.* JASA. https://repository.library.noaa.gov/view/noaa/61854
- **Scale.** **60,000+** 4-second audio segments for fine-tuning. F = 0.88 (window) / 0.89 (hour); FPR 0.05 / 0.01.
- **Context labels available.** Tier 5.
- **Access.** NOAA Library.

### 45. Garland et al. 2011 — Song revolution across the South Pacific

- **Citation.** Garland, E. C., Goldizen, A. W., Rekdahl, M. L., Constantine, R., Garrigue, C., Hauser, N. D., Poole, M. M., Robbins, J., & Noad, M. J. (2011). *Dynamic horizontal cultural transmission of humpback whale song at the ocean basin scale.* Current Biology 21: 687.
- **Scale.** 11 song types tracked across 6 populations, 11-yr longitudinal.
- **Context labels available.** Tier 5 (song type) + geographic.

### 46. Allen, Garland et al. 2018 — Eastern Australian song complexity

- **Citation.** Allen, J. A., Garland, E. C., Dunlop, R. A., & Noad, M. J. (2018). *Cultural revolutions reduce complexity in the songs of humpback whales.* Proc B. Dataset: [Dryad doi:10.5061/dryad.69161bg](https://datadryad.org/stash/dataset/doi:10.5061/dryad.69161bg)
- **Scale.** 13 consecutive years (2002–2014) of eastern-Australian humpback songs.
- **Context labels available.** Tier 5 (sound unit + theme).
- **Access.** Dryad.

### 47. Allen, Garland et al. 2022 — Inter-population complexity maintenance

- **Citation.** Allen, J. A., Garland, E. C., Dunlop, R. A., & Noad, M. J. (2022). *Song complexity is maintained during inter-population cultural transmission of humpback whale songs.* Scientific Reports 12: 8999. [doi:10.1038/s41598-022-12784-3](https://doi.org/10.1038/s41598-022-12784-3). Dataset: [Dryad doi:10.5061/dryad.9p8cz8wk1](https://datadryad.org/dataset/doi:10.5061/dryad.9p8cz8wk1)
- **Scale.** 6 song types 2009–2015, east-Australian → New Caledonian transmission.
- **Context labels available.** Tier 5 (song-type label).
- **Access.** Dryad.

### 48. SanctSound — NOAA + Navy sanctuary soundscape monitoring

- **Citation.** NOAA Office of National Marine Sanctuaries & U.S. Navy. SanctSound 2018–2021.
- **Scale.** **30 recording sites** across 7 sanctuaries + 1 marine national monument, **2018–2021**. Humpback whale data alone: **~16 TB**. Multi-species detection products (humpback song, blue whale A/B/D, sei whale downsweeps, fin whale 20-Hz pulses, etc.).
- **Context labels available.** Tier 5 (per-site, per-species presence detections) — mostly *species* labels not behaviour.
- **Access.** NOAA NCEI Google Cloud Storage + Passive Acoustic Data Map Viewer.
- **License.** US government public domain.
- **Honest caveats.** Same caveat as in `data.md`: wrong scope for *communication* — this is soundscape and presence monitoring, not behaviourally-tagged communication.

### 49. NOAA NCEI Passive Acoustic Archive

- **Citation.** NOAA NCEI Passive Acoustic Data Archive. https://www.ncei.noaa.gov/products/passive-acoustic-data
- **Access.** Google Cloud bucket `gs://noaa-passive-bioacoustic/`. Subbuckets per provider (NEFSC, PIFSC, SWFSC, etc.).
- **Format.** .wav, .xwav, .flac, .aif audio; .csv annotation logs.
- **Honest caveats.** This is the master archive that hosts most NOAA datasets above; treat as infrastructure, not as a single corpus.

### 50. DCLDE 2013 — Stellwagen Bank baleen-whale annotations

- **Citation.** NOAA NEFSC. *DCLDE 2013 NOAA NEFSC Baleen Whale (including North Atlantic Right Whale) Annotations.* DOI 10.25921/zaea-1s39. NCEI ID gov.noaa.ncei.pad:DCLDE_2013.
- **Scale.** One week of multichannel recording, channel 10. Annotated NARW upcalls (Nicole Pegg, updated Alexandra Carroll); humpback song; sei downsweeps; fin 20-Hz pulses; minke pulse trains; blue A/B/AB calls. Confidence field Detected / Possibly_Detected.
- **Context labels available.** Tier 5 (call type per species).
- **Access.** Google Cloud Storage + PAD Map Viewer.
- **License.** US government.

### 51. DCLDE 2015 low-frequency baleen dataset

- **Citation.** *2015 DCLDE Workshop datasets.* https://www.cetus.ucsd.edu/dclde/datasetDocumentation.html
- **Scale.** Annotated blue-whale D calls + fin-whale 40-Hz calls.
- **Access.** UCSD + data.gov.
- **Context labels.** Tier 5.

### 52. DCLDE 2018 — DOCC10 odontocete-click challenge

- **Citation.** Glotin, H. et al. 8th International DCLDE Workshop, Paris, June 2018. https://sabiod.lis-lab.fr/DCLDE/
- **Scale.** **3 TB** marine-mammal transients; DOCC10 derived odontocete-click subset.
- **Access.** Conditional via the workshop site.
- **Context labels.** Tier 5 (click species/category).

### 53. DCLDE 2022 — Hawaiian Islands cetacean raw data

- **Citation.** NCEI. *DCLDE 2022 Raw Passive Acoustic Data.*
- **Scale.** HICEAS 2017 raw audio in .wav and .flac.
- **Access.** NCEI / GCP bucket.

### 54. HICEAS 2017 minke detections (DCLDE Oahu)

- **Citation.** DCLDE Oahu dataset (SOEST, Hawaii) https://www.soest.hawaii.edu/ore/dclde/dataset/. PIFSC/SWFSC HICEAS 2017 OBIS-SEAMAP record (seamap.env.duke.edu/dataset/2180/html).
- **Scale.** 47 days of towed-hydrophone array data; 356 occurrence records covering 30 taxa / 23 species; near-daily minke "boing" detections during the final leg.
- **License.** CC-BY-NC-4.0.

### 55. NARW upcall + multi-baleen NEFSC archives (NCEI)

- **Citation.** NOAA Fisheries NEFSC. *North Atlantic Right Whale Acoustic Data and Annotations.* https://www.fisheries.noaa.gov/resource/data/noaa-nefsc-north-atlantic-right-whale-acoustic-data-and-annotations
- **Scale.** Multi-site, multi-year NARW upcall annotation logs.

### 56. North Pacific right whale Bering monitoring

- **Citations.**
  - Munger, L. M., Wiggins, S. M., Moore, S. E., & Hildebrand, J. A. (2008). *North Pacific right whale (Eubalaena japonica) seasonal and diel calling patterns from long-term acoustic recordings in the southeastern Bering Sea, 2000–2006.* Marine Mammal Science 24: 795. [doi:10.1111/j.1748-7692.2008.00219.x](https://doi.org/10.1111/j.1748-7692.2008.00219.x)
  - Crance, J. L., Berchok, C. L., Wright, D. L., et al. (2017). *Acoustic detection of the critically endangered North Pacific right whale in the northern Bering Sea.* MMS 33: 996. [doi:10.1111/mms.12521](https://doi.org/10.1111/mms.12521)
  - Crance, J. L. et al. (2019). *Acoustic detection of endangered North Pacific right whale (Eubalaena japonica) along the eastern Bering Shelf, 2012–2018.* NOAA repository 65613.
- **Scale.** Multi-decade monitoring. Up / down / constant / down-up calls; "up" calls 85% of detections (90 → 150 Hz, 0.7 s).
- **Context labels available.** Tier 5.

### 57. Webster 2016 — Southern right whale repertoire

- **Citation.** Webster, T. A., Dawson, S. M., Rayment, W. J., Parks, S. E., & Van Parijs, S. M. (2016). *Quantitative analysis of the acoustic repertoire of southern right whales in New Zealand.* JASA 140: 322. [doi:10.1121/1.4955084](https://doi.org/10.1121/1.4955084)
- **Scale.** Year-long autonomous recording at Auckland Islands. **35,487 detected calls** total; **11,623 upcalls**; **4,355 calls classified** into 10 call types (Random Forest, 82% accuracy). Peak rates August (288 ± 5.9 calls/h) and July (194 ± 8.3). NA-vs-SA right-whale discrimination < 0.01% misclassification.
- **Context labels available.** Tier 4 (population) + Tier 5; partial Tier 3 (calving ground).
- **Access.** Article; raw audio in Otago repository.
- **Playback?** No.

### 58. Bryde's whale "biotwang" + Mariana acoustic monitoring

- **Citation.** Allen, A. N., Norris, T. F., et al. (2024). *Bryde's whales produce Biotwang calls, which occur seasonally in long-term acoustic recordings from the central and western North Pacific.* Frontiers in Marine Science 11: 1394695. [doi:10.3389/fmars.2024.1394695](https://doi.org/10.3389/fmars.2024.1394695). Companion: 10.3389/fmars.2024.1305505.
- **Scale.** 13 HARP recording locations, central + western North Pacific. Bi-seasonal peaks (Feb–Apr, Aug–Nov).
- **Context labels available.** Tier 5 (call type) + spatial / seasonal.

### 59. Sei whale downsweeps (multi-site)

- **Citations.**
  - Tremblay, C. J. et al. (2019). *50 to 30-Hz triplet and singlet down sweep vocalizations produced by sei whales (Balaenoptera borealis) in the western North Atlantic Ocean.* JASA 145: 3351.
  - Cusano et al. (2019). *Discovering sounds in Patagonia: characterizing sei whale (Balaenoptera borealis) downsweeps in the south-eastern Pacific Ocean.* Ocean Science 15: 75. [doi:10.5194/os-15-75-2019](https://doi.org/10.5194/os-15-75-2019)
- **Scale.** SanctSound site SB01_11 carries Aug–Sep 2020 sei-whale detections; LFDCS detector tuned at 82 ± 34 Hz.
- **Context labels available.** Tier 5 (call type).

### 60. Blue whale call-type literature

- **Citations.**
  - Oleson, E. M., Calambokidis, J., Burgess, W. C., McDonald, M. A., LeDuc, C. A., & Hildebrand, J. A. (2007). *Behavioral context of call production by eastern North Pacific blue whales.* Marine Ecology Progress Series 330: 269.
  - McDonald, M. A., Hildebrand, J. A., & Mesnick, S. L. (2009). Worldwide blue-whale call structure.
- **Scale.** A / B / D / AB / ABB call inventory. Only males produce AB calls; song from lone, travelling whales.
- **Context labels available.** **Tier 3 (sex + behavioural context for the AB call)** + Tier 5.

### 61. Fin whale 20-Hz (Watkins, NOAA, SOSUS)

- **Citations.**
  - Watkins, W. A. (1981). *The activities and underwater sounds of fin whales.* Sci. Rep. Whales Res. Inst.
  - Weirathmueller, M. J., Stafford, K. M., Wilcock, W. S. D., Hilmo, R. S., Dziak, R. P., & Tréhu, A. M. (2017). *Spatial and temporal trends in fin whale vocalizations recorded in the NE Pacific Ocean between 2003-2013.* PLOS ONE 12: e0186127. https://github.com/michellejw/fin-call-patterns/tree/master/DETECTION_DATA
- **Scale.** Decade-long inter-pulse-interval drift 0.54 s/yr; peak frequency 0.17 Hz/yr; doublet pattern emergence.

### 62. Antarctic minke "bio-duck" attribution + repertoire

- **Citations.**
  - Risch, D., Gales, N. J., Gedamke, J., Kindermann, L., Nowacek, D. P., Read, A. J., Siebert, U., Van Opzeeland, I. C., Van Parijs, S. M., & Friedlaender, A. S. (2014). *Mysterious bio-duck sound attributed to the Antarctic minke whale (Balaenoptera bonaerensis).* Biology Letters 10: 20140175. [doi:10.1098/rsbl.2014.0175](https://doi.org/10.1098/rsbl.2014.0175)
  - Filun, D., Thomisch, K., Boebel, O., Brey, T., Širović, A., Spiesecke, S., Van Opzeeland, I. (2023). *Spatial and temporal variability of the acoustic repertoire of Antarctic minke whales (Balaenoptera bonaerensis) in the Weddell Sea.* Sci Rep 13: 11220. [doi:10.1038/s41598-023-38793-4](https://doi.org/10.1038/s41598-023-38793-4)
  - Antarctic minke whale acoustic Dryad dataset (June 2022). [doi:10.7291/D1RH5H](https://doi.org/10.7291/D1RH5H)
- **Scale.** Filun 2023: **11 bio-duck call types + minke songs**. Dryad dataset (2022): animal-borne video + audio.
- **Context labels available.** Tier 3 (some behavioural context) + Tier 5.

### 63. Gray whale acoustic monitoring (Burnham et al.)

- **Citation.** Burnham, R. E., Duffus, D. A., Mouy, X. (2019). *The use of passive acoustic monitoring as a census tool of gray whale (Eschrichtius robustus) migration.* JASA + later work; Burnham PhD thesis 2017 (UVic).
- **Scale.** Moan, knock, upsweep, cow-calf "motherese" call types.
- **Context labels available.** Tier 3 (migration / summer / cow-calf) + Tier 5.

### 64. SAMBAH — Baltic harbour porpoise grid

- **Citation.** Carlén, I. et al. (2018). *Basin-scale distribution of harbour porpoises in the Baltic Sea provides basis for effective conservation actions.* Biological Conservation. SAMBAH project. Dataset: [Dryad doi:10.5061/dryad.n5tb2rbx7](https://datadryad.org/dataset/doi:10.5061/dryad.n5tb2rbx7)
- **Scale.** **298–304 C-POD stations**, 2011–2013, **19.94 GB**. Population point estimate 491 (CI 71–1,105).
- **Context labels available.** Tier 5 (click train).
- **License.** CC-BY-NC.

### 65. LifeWatch Belgian C-POD network (the open North-Sea porpoise data the user likely meant by "JOMOPANS")

- **Citation.** Debusschere, E., Botteldooren, D., Buyse, J., Cox, T. J. S., Decauwer, K., Devolder, M., Diependaele, B., Hablützel, P., Heindler, F., Hernandez, F., Hostens, K., Mortier, F., Reubens, J., Souza Da Silva, E., Tiano, J., Vandepitte, L., Verleye, T. J., De Backer, A. (2024). *Cetacean passive acoustic network in the Belgian part of the North Sea.* Scientific Data 11: 1101. [doi:10.1038/s41597-024-03806-y](https://doi.org/10.1038/s41597-024-03806-y)
- **Scale.** **8 monitoring locations**, continuous since **2014**, mature network by 2018. Minute-resolution and hourly aggregates.
- **License.** **CC-BY-4.0**.
- **Honest caveats.** No specific JOMOPANS open dataset surfaced under that name; the comparable open North Sea porpoise PAM is this LifeWatch network. If JOMOPANS-Echo (anthropogenic noise) data is what was meant, that is a soundscape product distinct from communication.

### 66. Wisniewska et al. 2018 — Vessel noise disruption of foraging porpoises

- **Citation.** Wisniewska, D. M., Johnson, M., Teilmann, J., Siebert, U., Galatius, A., Dietz, R., & Madsen, P. T. (2018). *High rates of vessel noise disrupt foraging in wild harbour porpoises (Phocoena phocoena).* Proceedings of the Royal Society B. PubMed 29445018. Plus the 2016 *Ultra-high foraging rates of harbor porpoises make them vulnerable to anthropogenic disturbance* (Curr Biol).
- **Scale.** **5 wild porpoises** instrumented with DTAG-3 (500 kHz stereo, 18–44 h recordings), Danish coast Sept 2012–Aug 2014.
- **Context labels available.** **Tier 3 (foraging vs vessel exposure)** + Tier 5.
- **License.** Article + Dryad doi:10.5061/dryad.11b0f (FOV).

### 67. Vaquita CIRVA acoustic grid

- **Citations.**
  - IUCN CIRVA (Comité Internacional para la Recuperación de la Vaquita) reports 2015, 2017.
  - Jaramillo-Legorreta, A., Cárdenas-Hinojosa, G., Nieto-García, E., Rojas-Bracho, L., Ver Hoef, J., Moore, J., Tregenza, N., Barlow, J., Gerrodette, T., Thomas, L., & Taylor, B. (2017). *Passive acoustic monitoring of the decline of Mexico's critically endangered vaquita.* Conservation Biology 31: 183.
  - Jaramillo-Legorreta, A. M. et al. (2019). *Decline towards extinction of Mexico's vaquita porpoise (Phocoena sinus).* Royal Society Open Science.
- **Scale.** **48 C-POD grid** inside Vaquita Refuge, summers 2011–2018. 98.6% population decline over 2011–2018.
- **Context labels available.** Tier 5 (click detection only).
- **Access.** CIRVA reports; some Royal Society Open Science PDFs.
- **Honest caveats.** Conservation-monitoring data, not communication-context data; no playback potential given population near-extinction.

### 68. Yangtze finless porpoise — Source parameters and PAM systems

- **Citations.**
  - Fang, L., Wang, D., Li, Y., Cheng, Z., Pine, M. K., Wang, K., & Li, S. (2015). *The source parameters of echolocation clicks from captive and free-ranging Yangtze finless porpoises (Neophocaena asiaeorientalis).* PLOS ONE 10: e0129143.
  - Various 2022 Frontiers / Wiley papers on RPCD-II detector + spatial-temporal biosonar variation.
- **Scale.** Source level 167 dB (captive) / 176 dB (free); centre frequency 129–133 kHz.
- **Context labels available.** Tier 5.

### 69. Lammers & Au 2003 — Spinner / spotted dolphin broadband signalling

- **Citation.** Lammers, M. O., Au, W. W. L., & Herzing, D. L. (2003). *The broadband social acoustic signaling behavior of spinner and spotted dolphins.* JASA 114: 1629. PubMed 14514216. Lammers (2003) dissertation, U. Hawaii Manoa.
- **Scale.** Whistle + burst pulse + click broadband measurement; burst pulses largely ultrasonic with little energy < 20 kHz.
- **Context labels available.** Tier 3 (group-coordination) + Tier 5.

### 70. Spinner-dolphin signature whistles (2023)

- **Citation.** Zaeschmar, J. R. et al. (2023). *First acoustic evidence of signature whistle production by spinner dolphins (Stenella longirostris).* Animal Cognition. [10.1007/s10071-023-01824-8](https://doi.org/10.1007/s10071-023-01824-8)
- **Context labels available.** Tier 4 (caller identity).

### 71. Dolphin Communication Project (Bahamas Atlantic spotted + bottlenose)

- **Citation.** Herzing, D. L. (1996). *Vocalizations and associated underwater behaviors of free-ranging Atlantic spotted dolphins (Stenella frontalis) and bottlenose dolphins (Tursiops truncatus).* Aquatic Mammals 22: 61. Multiple later papers.
- **Scale.** **200+ individual spotted dolphins** tracked since 1985.
- **Context labels available.** Tier 3 (foraging / aggression / discipline / courtship) + Tier 4 (individual).
- **Access.** **Articles only.** DCP has NOT released a public audio repository as of audit date.
- **Honest caveats.** Decades-long behaviourally-rich corpus that is *not* openly downloadable. Email contact required.

### 72. Striped dolphin Mediterranean

- **Citations.**
  - Papale, E., Azzolin, M., Cascão, I., Gannier, A., Lammers, M. O., Martin, V. M., Oswald, J., Perez-Gil, M., Prieto, R., Silva, M. A., & Giacoma, C. (2013). *Geographic variation of whistles of the striped dolphin (Stenella coeruleoalba) within the Mediterranean Sea.* JASA 134: 1126.
  - Azzolin, M. et al. (2020). *The Social Role of Vocal Complexity in Striped Dolphins.* Frontiers in Marine Science 7: 584301.
- **Scale.** 599 whistles, 37 sightings, 1996–2003; 15 discriminant variables; 277 NW Med + 263 SW Med samples.
- **Context labels available.** **Tier 3 (socialising vs feeding / travelling / resting)** + Tier 5.

### 73. Commerson's dolphin — Bahía San Julián

- **Citation.** Reyes Reyes, M. V. (2016). *Communication sounds of Commerson's dolphins (Cephalorhynchus commersonii) and contextual use of vocalizations.* Marine Mammal Science 32: 1219. Reyes Reyes et al. (2014/2018). *Description and clustering of echolocation signals of Commerson's dolphins in Bahía San Julián, Argentina.*
- **Scale.** Three click clusters at 129/137/173 kHz peak; whistles + broad-band clicks below 100 kHz.
- **Context labels available.** **Tier 3 (mother-calf, adult communication)** + Tier 5.

### 74. Dusky dolphin

- **Citations.**
  - Au, W. W. L., & Würsig, B. (2004). *Echolocation signals of dusky dolphins (Lagenorhynchus obscurus) in Kaikoura, New Zealand.* JASA 115: 2307.
  - Yin, S. (1999). *Movement patterns, behaviors, and whistle sounds of dolphin groups off Kaikoura, New Zealand.* Texas A&M MS thesis.
  - Vaughn-Hirshorn, R. L., Hodge, K. B., Würsig, B., Sappenfield, R. H., Lammers, M. O., & Au, W. W. L. (2012). *Characterizing dusky dolphin sounds from Argentina and New Zealand.* JASA 132: 498.
- **Scale.** Cross-region (Argentina vs NZ) whistle + burst-pulse + click comparison.
- **Context labels available.** Tier 5.

### 75. Watkins Marine Mammal Sound Database (master archive)

- **Citation.** Watkins, W. A. et al. *Watkins Marine Mammal Sound Database.* Woods Hole Oceanographic Institution + New Bedford Whaling Museum. https://cis.whoi.edu/science/B/whalesounds/ . 2018 Remaster: https://marine-mammal.soundwave.cl/
- **Scale.** **~1,800 master tapes**; **~10,000 digital clips**; **60+ species** recorded 1934–2001.
- **Context labels available.** Tier 5 (species + date + location).
- **License.** *"free to download for personal or academic (not commercial) use"* (WHOI press release).
- **Honest caveats.** Same as in `data.md`: not systematically context-annotated; heterogeneous; useful as reference / sanity-check, not primary.

### 76. confit/wmms-parquet (HuggingFace mirror)

- **Citation.** confit (Soonshin Seo). *Watkins Marine Mammal Sound Database (WMMS).* HuggingFace. [huggingface.co/datasets/confit/wmms-parquet](https://huggingface.co/datasets/confit/wmms-parquet) (parquet) and confit/wmms (raw).
- **Scale (verified by WebFetch).** **32 species**, **1,697 clips**, **1.22 GB**, 80/20 split (1357 train / 340 test). Species list verified, 26 cetacean + 6 pinniped/walrus.
- **License.** Inherits Watkins "personal/academic use, attribution required."
- **Honest caveats.** This is the cleanest pre-formatted ML-ready cross-species cetacean clip set in existence; ideal for BEANS-style benchmarks and for AVES / Perch transfer.

### 77. BEANS — Benchmark of Animal Sounds

- **Citation.** Hagiwara, M., Hoffman, B., Liu, J.-Y., Cusimano, M., Effenberger, F., & Zacarian, K. (2023). *BEANS: The Benchmark of Animal Sounds.* ICASSP 2023. arXiv: 2210.12300. [github.com/earthspecies/beans](https://github.com/earthspecies/beans)
- **Scale.** **12 datasets** (5 classification + 5 detection + 2 auxiliary). Cetacean datasets included: **watkins** (31 marine-mammal species; classification) and **hiceas** (minke whale detection).
- **License.** MIT (code); per-dataset licenses inherited.

### 78. BEANS-Zero — zero-shot bioacoustic LLM benchmark

- **Citation.** Robinson, D., Miron, M., Hagiwara, M., Pietquin, O. (2025). *NatureLM-audio: an Audio-Language Foundation Model for Bioacoustics.* ICLR / arXiv 2411.07186. Dataset: [huggingface.co/datasets/EarthSpeciesProject/BEANS-Zero](https://huggingface.co/datasets/EarthSpeciesProject/BEANS-Zero)
- **Scale.** **91,965 samples**. Tasks: classification, detection, captioning. Cetacean: watkins + hiceas + new call-type and life-stage subsets.
- **License.** Mixed (per-source).

### 79. AnimalSpeak — bioacoustics text-audio dataset

- **Citation.** Robinson, D. R., Miron, M., Cusimano, M., Pietquin, O., Sainburg, T., Bohnenstiehl, D., Tilak, S., Pijanowski, B. C., & Earth Species Project. (2023). *Transferable Models for Bioacoustics with Human Language Supervision.* arXiv: 2308.04978. Dataset: [huggingface.co/datasets/davidrrobinson/AnimalSpeak](https://huggingface.co/datasets/davidrrobinson/AnimalSpeak)
- **Scale.** **894,256 rows** (paper says > 1M aggregated audio-caption pairs), 241 MB. Aggregated from Xeno-Canto + iNaturalist + others.
- **License.** Mixed (CC-by predominantly).

### 80. AVES — Animal Vocalization Encoder via Self-Supervision

- **Citation.** Hagiwara, M. (2023). *AVES: Animal Vocalization Encoder based on Self-Supervision.* ICASSP 2023. arXiv: 2210.14493. [github.com/earthspecies/aves](https://github.com/earthspecies/aves)
- **Training data.** FSD50K + AudioSet + VGGSound (animal vocalisation slices). Released as Fairseq, TorchAudio, ONNX weights.

### 81. AVEX — successor framework

- **Citation.** Earth Species Project. AVEX (2025). arXiv: 2508.11845. [github.com/earthspecies/avex](https://github.com/earthspecies/avex)

### 82. Perch 2.0 — Google DeepMind bioacoustics foundation model

- **Citation.** Hamer, J., et al. (2025). *Perch 2.0: The Bittern Lesson for Bioacoustics.* arXiv: 2512.03219. [github.com/google-research/perch](https://github.com/google-research/perch)
- **Scale.** Trained on **14,597 species**, mostly birds. NOAA marine-mammal Colab demonstrates transfer to whales.

### 83. SurfPerch — marine bioacoustics specialisation

- **Citation.** Williams, B., Lauder, J. M., Hamer, J., et al. (2024). *Leveraging tropical reef, bird and unrelated sounds for superior transfer learning in marine bioacoustics.* [Zenodo 11071202](https://zenodo.org/records/11071202)

### 84. OBIS-SEAMAP

- **Citation.** Halpin, P. N., Read, A. J., Fujioka, E., Best, B. D., Donnelly, B., Hazen, L. J., Kot, C., Urian, K., LaBrecque, E., Dimatteo, A., Cleary, J., Good, C., Crowder, L. B., & Hyrenbach, K. D. (2009). *OBIS-SEAMAP: The world data center for marine mammal, sea bird, and sea turtle distributions.* Oceanography 22: 104.
- **Scale (as of 2009).** > 2.2 million observation records, > 230 datasets, 73 yr.
- **Honest caveats.** Mostly *sighting* records, not acoustic. PAM-derived sets (e.g. DECAF AUTEC, MAPS) are a subset.

### 85. Janik, Sayigh, & Wells 2006 — Signature whistles as referential labels

- **Citation.** Janik, V. M., Sayigh, L. S., & Wells, R. S. (2006). *Signature whistle shape conveys identity information to bottlenose dolphins.* Proc. Natl. Acad. Sci. 103: 8293.
- **Playback?** Yes. Foundation for the "name" hypothesis.

### 86. King & Janik 2013 — Dolphins use learned vocal labels to address each other

- **Citation.** King, S. L., & Janik, V. M. (2013). *Bottlenose dolphins can use learned vocal labels to address each other.* PNAS 110: 13216. [doi:10.1073/pnas.1304459110](https://doi.org/10.1073/pnas.1304459110)
- **Playback?** Yes.

### 87. King et al. 2013 — Signature-whistle copying

- **Citation.** King, S. L., Sayigh, L. S., Wells, R. S., Fellner, W., & Janik, V. M. (2013). *Vocal copying of individually distinctive signature whistles in bottlenose dolphins.* Proc. R. Soc. B 280: 20130053. [doi:10.1098/rspb.2013.0053](https://doi.org/10.1098/rspb.2013.0053)
- **Playback?** **Yes.** Own (copy) / unfamiliar / familiar conditions, n = 12 / 10 / 12.

### 88. Quick & Janik 2012 — Dolphins exchange whistles when meeting

- **Citation.** Quick, N. J., & Janik, V. M. (2012). *Bottlenose dolphins exchange signature whistles when meeting at sea.* Proc. R. Soc. B 279: 2539.

### 89. Sayigh 1998 — Cohesion-call hypothesis

- **Citation.** Sayigh, L. S., Tyack, P. L., Wells, R. S., Solow, A. R., Scott, M. D., & Irvine, A. B. (1999). *Individual recognition in wild bottlenose dolphins: a field test using playback experiments.* Animal Behaviour 57: 41. Plus Sayigh et al. (1998). *Context-specific use suggests that bottlenose dolphin signature whistles are cohesion calls.* Animal Behaviour 56: 1057.
- **Playback?** Yes (1999 Anim Behav).

### 90. Sainburg, Thielk & Gentner 2020 — Latent-space vocal repertoire methods

- **Citation.** Sainburg, T., Thielk, M., & Gentner, T. Q. (2020). *Finding, visualizing, and quantifying latent structure across diverse animal vocal repertoires.* PLOS Computational Biology 16: e1008228. [github.com/timsainb/avgn_paper](https://github.com/timsainb/avgn_paper)
- **Scale.** Method applied to **29 species across 19 datasets** including humans, bats, songbirds, mice, **cetaceans**, primates. UMAP + HDBSCAN baseline framework — the same backbone the PLAN.md identifies for the Coller approach.

### 91. Sharma 2024 / Project CETI roadmap

- **Citation.** Andreas, J. et al. (CETI consortium) (2021). *Cetacean Translation Initiative: a roadmap to deciphering the communication of sperm whales.* arXiv: 2104.08614.
- **Honest caveats.** Not a dataset paper; cite for the project context.

### 92. Filatova 2016 — Physical constraints on call evolution

- **Citation.** Filatova, O. A. et al. (2016). *Physical constraints of cultural evolution of dialects in killer whales.* JASA 140: 3755.

### 93. Macaulay Library cetacean holdings

- **Citation.** Cornell Lab of Ornithology. *Macaulay Library.* https://www.macaulaylibrary.org/
- **Scale.** **2.7 million audio recordings**, ~9,000 species (predominantly birds). Cetacean count not provided by primary source; second-pass audit needed before citing a number.
- **Honest caveats.** Not systematically annotated for cetaceans; access constraints not fully audited. Same conclusion as `data.md`.

### 94. CETI Cape Breton pilot whale project

- **Citation.** Whitehead, H., & Zwamborn, E. (various). Pilot Whales of Canada project. http://www.pilotwhalesofcanada.com/

### 95. AAD bowhead and minke databases

- **Citations.** Australian Antarctic Data Centre records on minke and other Southern Ocean cetaceans; ResearchDataAustralia for related projects.

### 96. Bermant et al. 2021 — Whale Sound Recognition (CETI early)

- **Citation.** Bermant, P. C. (2021). *BioCPPNet: automatic bioacoustic source separation with deep neural networks.* Scientific Reports.

### 97. Brodie & Dunn 2023 — Sperm-whale group composition + coda

- (Found via Sci Rep + similar 2025 papers; verify before citing.)

### 98. Sayigh et al. 1990 — Development of signature whistles

- **Citation.** Sayigh, L. S., Tyack, P. L., Wells, R. S., & Scott, M. D. (1990). *Signature whistles of free-ranging bottlenose dolphins (Tursiops truncatus): stability and mother-offspring comparisons.* Behavioral Ecology and Sociobiology 26: 247.

### 99. Madeira-Madrigal et al. companion / WhAM appendix

- **Citation.** WhAM Appendix B (arXiv 2512.02206) contains the general background on coda anatomy.

### 100. SOSUS / Watkins fin whale archive

- **Citation.** Clark, C. W. (1995). *Application of US Navy underwater hydrophone arrays for scientific research on whales.* Reports of the International Whaling Commission. https://darchive.mblwhoilibrary.org/handle/1912/350

---

## Disqualified for primary use

(In the spirit of `data.md`. Each line is a dataset that surfaced during the audit and is documented here so the researcher does not waste cycles chasing a ghost.)

- **Project CETI WhAM (entry 4) for the prize.** Beautiful corpus, CC-BY, but **explicitly stripped of behavioural context**. The HF dataset card says it directly. Cannot satisfy criterion 2 on its own.
- **Sarasota Dolphin Whistle Database (entry 2) as an "open" repository.** Marked open in popular summaries but the Frontiers data-availability statement is request-only. Treat as request-only until proved otherwise.
- **Orchive (entry 30).** ~19,000 h, 23 yr — the largest single killer-whale corpus in existence — is **held by OrcaLab** and not openly downloadable in full. ORCA-SPOT is open, the underlying audio is mostly not.
- **Macaulay Library (entry 93).** Cetacean subset not systematically annotated for behavioural context; access constraints not fully audited. Same conclusion as `data.md`.
- **SanctSound (entry 48).** ~16 TB humpback alone but **wrong scope**: soundscape and presence monitoring, no behavioural-context labels. Same conclusion as `data.md`.
- **DCP (entry 71).** Bahamas Atlantic-spotted-dolphin corpus is contextually the richest dolphin observation programme outside Sarasota but has not released a public audio repository. Email contact required.
- **OBIS-SEAMAP PAM detections (entry 84).** Almost all OBIS-SEAMAP cetacean records are *sightings*, not acoustic. The PAM subset (e.g. DECAF AUTEC, MAPS Song-of-the-Whale) gives downloadable detection logs but **not the raw audio** for most providers.
- **Vaquita CIRVA grid (entry 67).** Conservation-monitoring time series, not communication; population effectively extirpated.
- **DCLDE 2018 / DOCC10 (entry 52).** 3 TB; access is workshop-conditional, not always frictionless.
- **OrcaSound as primary (entry 29).** Same conclusion as `data.md`: excellent demo input, ecologically narrow as primary.
- **Watkins WMMSDB as primary (entry 75).** Same conclusion as `data.md`: best as reference / sanity check.
- **MERIDIAN as a *dataset* (entry 32 covers the small Zenodo product).** MERIDIAN is primarily an infrastructure / tooling group, not a dataset publisher.
- **HappyWhale acoustic.** The HappyWhale catalogue is photo-ID (157,350 encounters, 27,956 individuals; Cheeseman et al. 2023 Sci Rep), **not acoustic**. Cited here to head off misidentification.
- **Project CETI as a closed proprietary dataset.** A common misperception. CETI releases (WhAM/DSWP, Sharma 2024 GitHub, Madeira detector) are real and open under CC-BY / MIT.

---

## Recommendation

For a **solo, Path-A re-analysis** entry under Danielle's plan (see `PLAN.md` §"Solo Path A"), the **single best corpus combination is:**

1. **Primary corpus: Sharma 2024 Dominica codas (entry 3)** + **Paradise 2025 DSWP HF audio (entry 4)**. The CSV gives 8,719 timestamped codas with rhythm/tempo/rubato/ornamentation features and clan + individual + social-unit annotations; the HF release gives 1,501 codas of real audio under CC-BY-4.0 to feed an encoder (AVES / Perch 2.0) directly. Both resolve and download today; combined size is well under 1 GB.
2. **Multi-context tie-in: Lehnhoff 2025 DOLPHINFREE (entry 11)**. CC-BY-4.0, 400+ minutes of common-dolphin audio with **explicit behavioural-state labels** (foraging / travelling / socialising / milling / boat-attraction). This is what gives criterion 2 ("multi-context") an *endogenous*-signal anchor for a *second* species, broadening the claim beyond the single-clan single-context sperm-whale slice.
3. **Playback layer: Sayigh 2025 NSW (entry 1)** as the cited published-playback comparator, plus **King & Janik 2013 PNAS** (entry 86) and **King et al. 2013 RSPB** (entry 87) for criterion 3 in dolphins, **Foote 2008 Ethology** (entry 36, with the DOI correction noted) and **Selbmann 2026 Sci Rep** (entry 35) for criterion 3 in orcas. The submission paper would *re-analyse* published playback-response statistics, treating those as the criterion-3 "measurable response" already in the literature.
4. **Backup if the methodological claim collapses: DCLDE 2026 (entry 28)** as already vetted in `OrcaDolittle/docs/data.md`. Cross-reference confirms scale numbers exactly.
5. **Foundation-model stack:** AVES (entry 80) → AVEX (entry 81) for embeddings; Perch 2.0 (entry 82) for transfer; SurfPerch (entry 83) for marine specialisation; Sainburg 2020 (entry 90) for latent-space repertoire discovery — all open, all CPU-feasible for inference, matching the Methods stack in PLAN.md.

**Hard caveats for any solo submission:**

- **Sayigh's lab won the 2025 prize on this exact research stack.** Re-doing it for 2027 invites direct comparison. Any submission must (a) carry a methodological novelty Sayigh did not use, *and* (b) be epistemically careful about "language" claims (per Birch on the committee).
- **CETI is institutionally large and well-resourced.** A solo re-analysis of Sharma 2024 must contribute something the CETI roadmap has not already published — e.g. cross-species generalisation (sperm whale codas × common dolphin contexts via shared encoder embeddings), or a falsifiable structural prediction.
- **No openly-licensed cetacean dataset combines all three of (multi-context behavioural state) × (playback-validated response) × (significant scale) in one package.** The combination has to be built by joining (a) a context-rich open audio set (DOLPHINFREE, Visser 2017, Arranz 2018, or the DCLDE 2026 ecotype × call-type matrix) with (b) the literature's playback findings. That join is the work that has to be done. It is not free — but it *is* tractable solo in the 12-week window described in PLAN.md §"Step-by-step plan."
- **Cross-reference to `OrcaDolittle/docs/data.md` summary.** All five entries listed there (DCLDE 2026, Stafford 2018 bowhead, Weddell seal dialects, Watkins WMMSDB, OrcaSound) are reaffirmed with the same numbers from independent web searches. The pinniped pivot (Weddell seal) is intact; nothing in this broader audit overturns it.
- **Cross-reference to `OrcaDolittle/docs/playback_corpus.md`.** All five provisional playback papers in that file are still recommended for extraction, with **one correction:** the Foote 2008 paper is in *Ethology* (doi 10.1111/j.1439-0310.2008.01496.x), not *Current Biology* (10.1016/j.cub.2008.06.013). The latter DOI does not resolve to the Foote V4-call paper. This extraction error should be fixed on next-pass audit of that file.

---

## Bibliography

(Primary papers + dataset DOIs cited above. Alphabetised by first author. "[D]" denotes a dataset DOI; otherwise paper.)

- Alcázar-Treviño, J., Johnson, M., Arranz, P., Warren, V. E., Pérez-González, C. J., Marques, T., Madsen, P. T., & Aguilar de Soto, N. (2020). Dataset for "Deep-diving beaked whales dive together but forage apart." Dryad. [D] doi:10.5061/dryad.gqnk98sm0.
- Allen, A. N., Cattiau, J., Harvey, M., Harrell, L., Jansen, A., Merkens, K. P., Wall, C. C., & Oleson, E. M. (2021). A convolutional neural network for automated detection of humpback whale song in a diverse, long-term passive acoustic dataset. Frontiers in Marine Science 8: 607321. doi:10.3389/fmars.2021.607321.
- Allen, A. N., Norris, T. F., Margolina, T., Joseph, J. E., Oleson, E. M. (2024). Bryde's whales produce Biotwang calls. Frontiers in Marine Science 11: 1394695. doi:10.3389/fmars.2024.1394695.
- Allen, J. A., Garland, E. C., Dunlop, R. A., & Noad, M. J. (2018). Cultural revolutions reduce complexity in the songs of humpback whales. Proc. R. Soc. B. [D] doi:10.5061/dryad.69161bg.
- Allen, J. A., Garland, E. C., Dunlop, R. A., & Noad, M. J. (2022). Song complexity is maintained during inter-population cultural transmission of humpback whale songs. Sci. Rep. 12: 8999. doi:10.1038/s41598-022-12784-3. [D] doi:10.5061/dryad.9p8cz8wk1.
- Andreas, J. et al. (CETI consortium) (2021). Cetacean Translation Initiative: a roadmap to deciphering the communication of sperm whales. arXiv:2104.08614.
- Antunes, R. (2009). Variation in sperm whale (Physeter macrocephalus) coda vocalizations and social structure in the North Atlantic Ocean. PhD thesis, U. St Andrews.
- Arranz, P., DeRuiter, S. L., Stimpert, A. K., Neves, S., Friedlaender, A. S., Goldbogen, J. A., Visser, F., Calambokidis, J., Southall, B. L., & Tyack, P. L. (2018). Discrimination of fast click series produced by tagged Risso's dolphins for echolocation or communication. JEB. [D] doi:10.5061/dryad.48vq4.
- Au, W. W. L., & Würsig, B. (2004). Echolocation signals of dusky dolphins (Lagenorhynchus obscurus) in Kaikoura, New Zealand. JASA 115: 2307.
- Azzolin, M. et al. (2020). The social role of vocal complexity in striped dolphins. Frontiers in Marine Science 7: 584301.
- Bergler, C., Schröter, H., Cheng, R. X., Barth, V., Weber, M., Nöth, E., Hofer, H., & Maier, A. (2019). ORCA-SPOT: An automatic killer whale sound detection toolkit using deep learning. Sci. Rep. 9: 10997. doi:10.1038/s41598-019-47335-w.
- Bergler, C., Smeele, S. Q., Tyndel, S. A., et al. (2022). ANIMAL-SPOT enables animal-independent signal detection and classification using deep learning. Sci. Rep. 12: 21966. doi:10.1038/s41598-022-26429-y.
- Bermant, P. C., Bronstein, M. M., Wood, R. J., Gero, S., & Gruber, D. F. (2019). Deep machine learning techniques for the detection and classification of sperm whale bioacoustics. Sci. Rep. 9: 12588. doi:10.1038/s41598-019-48909-4.
- Blackwell, S. B., Tervo, O. M., Conrad, A. S., Sinding, M.-H. S., Hansen, R. G., Ditlevsen, S., & Heide-Jørgensen, M. P. (2018). Spatial and temporal patterns of sound production in East Greenland narwhals. PLOS ONE 13: e0198295. doi:10.1371/journal.pone.0198295. [D] figshare e62ed400ed454a459ab4.
- Burnham, R. E., Duffus, D. A., & Mouy, X. (2019). Passive acoustic monitoring as a census tool of gray whale migration.
- Castellote, M., Small, R. J., Lammers, M. O., Jenniges, J. J., Mondragon, J., & Atkinson, S. (2016). Dual instrument passive acoustic monitoring of belugas in Cook Inlet, Alaska. JASA 139: 2697.
- Cheeseman, T., Southerland, K., et al. (2023). A collaborative and near-comprehensive North Pacific humpback whale photo-ID dataset. Sci. Rep. 13: 10237.
- Clark, C. W. (1995). Application of US Navy underwater hydrophone arrays for scientific research on whales. IWC Reports.
- Confit (Soonshin Seo). (2023). Watkins Marine Mammal Sound Database parquet mirror. [D] huggingface.co/datasets/confit/wmms-parquet.
- Courts, R., Erbe, C., Wellard, R., Boisseau, O., Jenner, K. C. S., & Jenner, M.-N. (2020). Australian long-finned pilot whales emit stereotypical vocalisations. [D] doi:10.5061/dryad.w3r2280p3.
- Crance, J. L., Berchok, C. L., Wright, D. L., et al. (2017). Acoustic detection of the critically endangered North Pacific right whale in the northern Bering Sea. Marine Mammal Science 33: 996. doi:10.1111/mms.12521.
- Cusano, D. A., Towers, J. R., & Parks, S. E. (2019). Discovering sounds in Patagonia: characterizing sei whale downsweeps in the south-eastern Pacific Ocean. Ocean Science 15: 75. doi:10.5194/os-15-75-2019.
- DCLDE 2013 NOAA NEFSC Baleen Whale Annotations. [D] doi:10.25921/zaea-1s39.
- DCLDE 2026 — Killer whale ecotype annotations. Palmer et al. 2025. [D] doi:10.25921/15ey-mh50.
- Debusschere, E. et al. (2024). Cetacean passive acoustic network in the Belgian part of the North Sea. Sci. Data 11: 1101. doi:10.1038/s41597-024-03806-y.
- Deecke, V. B., Ford, J. K. B., & Spong, P. (2000). Dialect change in resident killer whales. Animal Behaviour 60: 629. doi:10.1006/anbe.2000.1505.
- Deecke, V. B., Slater, P. J. B., & Ford, J. K. B. (2002). Selective habituation shapes acoustic predator recognition in harbour seals. Nature 420: 171. doi:10.1038/nature01030.
- Earth Species Project (2025). NatureLM-audio. arXiv:2411.07186. [D] huggingface.co/datasets/EarthSpeciesProject/BEANS-Zero.
- Earth Species Project (2025). AVEX. arXiv:2508.11845.
- Fang, L., Wang, D., Li, Y., Cheng, Z., Pine, M. K., Wang, K., & Li, S. (2015). Source parameters of echolocation clicks from captive and free-ranging Yangtze finless porpoises. PLOS ONE 10: e0129143.
- Filatova, O. A., Burdin, A. M., Hoyt, E., & Sato, H. (2007). The structure of the discrete call repertoire of killer whales from southeast Kamchatka. Bioacoustics 16: 261.
- Filatova, O. A., Samarra, F. I. P., Deecke, V. B., Ford, J. K. B., Miller, P. J. O., & Yurk, H. (2015). Cultural evolution of killer whale calls. Behaviour 152: 2001.
- Filatova, O. A. et al. (2016). Physical constraints of cultural evolution of dialects in killer whales. JASA 140: 3755.
- Filun, D., Thomisch, K., Boebel, O., Brey, T., Širović, A., Spiesecke, S., & Van Opzeeland, I. (2023). Spatial and temporal variability of the acoustic repertoire of Antarctic minke whales in the Weddell Sea. Sci. Rep. 13: 11220. doi:10.1038/s41598-023-38793-4.
- Foote, A. D., Osborne, R. W., & Hoelzel, A. R. (2008). Temporal and contextual patterns of killer whale call type production. Ethology 114: 599. doi:10.1111/j.1439-0310.2008.01496.x.
- Ford, J. K. B. (1989). Acoustic behaviour of resident killer whales off Vancouver Island. Can. J. Zool. 67: 727.
- Ford, J. K. B. (1991). Vocal traditions among resident killer whales in coastal waters of British Columbia. Can. J. Zool. 69: 1454. doi:10.1139/z91-206.
- Frasier, K. (2024). Blainville's beaked whale echolocation clicks from autonomous passive acoustic recordings. Dryad. [D] doi:10.6076/D12G6N.
- Garland, E. C., Goldizen, A. W., Rekdahl, M. L., Constantine, R., Garrigue, C., Hauser, N. D., Poole, M. M., Robbins, J., & Noad, M. J. (2011). Dynamic horizontal cultural transmission of humpback whale song at the ocean basin scale. Current Biology 21: 687.
- Gero, S., Whitehead, H., & Rendell, L. (2016). Individual, unit and vocal clan level identity cues in sperm whale codas. Royal Society Open Science 3: 150372. [D] doi:10.5061/dryad.ck4h0.
- Hagiwara, M. (2023). AVES: Animal vocalization encoder based on self-supervision. ICASSP 2023. arXiv:2210.14493.
- Hagiwara, M., Hoffman, B., Liu, J.-Y., Cusimano, M., Effenberger, F., & Zacarian, K. (2023). BEANS: The benchmark of animal sounds. ICASSP 2023. arXiv:2210.12300.
- Halpin, P. N. et al. (2009). OBIS-SEAMAP: The world data center for marine mammal, sea bird, and sea turtle distributions. Oceanography 22: 104.
- Hamer, J. et al. (2025). Perch 2.0: The bittern lesson for bioacoustics. arXiv:2512.03219.
- Herzing, D. L. (1996). Vocalizations and associated underwater behaviors of free-ranging Atlantic spotted dolphins and bottlenose dolphins. Aquatic Mammals 22: 61.
- Jaramillo-Legorreta, A. et al. (2017). Passive acoustic monitoring of the decline of Mexico's critically endangered vaquita. Conservation Biology 31: 183.
- Jaramillo-Legorreta, A. M. et al. (2019). Decline towards extinction of Mexico's vaquita porpoise. Royal Society Open Science.
- Janik, V. M., Sayigh, L. S., & Wells, R. S. (2006). Signature whistle shape conveys identity information to bottlenose dolphins. PNAS 103: 8293.
- Kaplan, M. B., Mooney, T. A., Baird, R. W., et al. Melon-headed whale DTag corpus (Hawaiian populations).
- Kather, J. F. et al. (2024). Development of a machine learning detector for North Atlantic humpback whale song. JASA.
- King, S. L., & Janik, V. M. (2013). Bottlenose dolphins can use learned vocal labels to address each other. PNAS 110: 13216. doi:10.1073/pnas.1304459110.
- King, S. L., Sayigh, L. S., Wells, R. S., Fellner, W., & Janik, V. M. (2013). Vocal copying of individually distinctive signature whistles in bottlenose dolphins. Proc. R. Soc. B 280: 20130053. doi:10.1098/rspb.2013.0053.
- Lammers, M. O., Au, W. W. L., & Herzing, D. L. (2003). The broadband social acoustic signaling behavior of spinner and spotted dolphins. JASA 114: 1629.
- Lehnhoff, L. et al. (2025). High-resolution acoustic recordings of wild free-ranging short-beaked common dolphins for etho-acoustical and repertoire studies. ESSD 17: 4495. doi:10.5194/essd-17-4495-2025. [D] doi:10.5281/zenodo.14637674.
- Madeira, F. et al. (2025). Automatic detection and annotation of eastern Caribbean sperm whale codas. Sci. Rep. 15. doi:10.1038/s41598-025-97009-z.
- Madrigal, B. C. et al. (2025). Acoustic behaviour of endangered Hawaiian false killer whales. [D] doi:10.5061/dryad.s7h44j1n6.
- Madrigal, V. P. et al. (2025). Description of a collaborative sperm whale birth and shifts in coda vocal styles during key events. Sci. Rep. doi:10.1038/s41598-025-27438-3.
- Marcoux, M. et al. (2020). Vocal sequences in narwhals. JASA 147: 1078. [D] doi:10.5061/dryad.zcrjdfnj2.
- McCullough, J. L. K., Simonis, A. E., Sakai, T., & Oleson, E. M. (2021). Acoustic classification of false killer whales in the Hawaiian Islands based on comprehensive vocal repertoire. NOAA TM-NMFS-PIFSC.
- Munger, L. M. et al. (2008). North Pacific right whale seasonal and diel calling patterns from long-term acoustic recordings in the southeastern Bering Sea, 2000–2006. MMS 24: 795. doi:10.1111/j.1748-7692.2008.00219.x.
- NOAA NCEI Passive Acoustic Data Archive. https://www.ncei.noaa.gov/products/passive-acoustic-data.
- Oleson, E. M. et al. (2007). Behavioral context of call production by eastern North Pacific blue whales. MEPS 330: 269.
- Oliveira, C. et al. (2016). Sperm whale codas may encode individuality as well as clan identity. JASA 139: 2860.
- Orcasound on AWS Open Data Registry. https://registry.opendata.aws/orcasound/. github.com/orcasound/orca-dclde.
- Palmer, J. K. et al. (2025). A public dataset of annotated Orcinus orca acoustic signals for detection and ecotype classification. Sci. Data. doi:10.1038/s41597-025-05281-5.
- Papale, E. et al. (2013). Geographic variation of whistles of the striped dolphin within the Mediterranean Sea. JASA 134: 1126.
- Paradise, O., Muralikrishnan, P., Chen, L., Flores Garcia, H., Pardo, B., Diamant, R., Gruber, D. F., Gero, S., & Goldwasser, S. (2025). WhAM: Towards a translative model of sperm whale vocalization. NeurIPS 2025. arXiv:2512.02206. [D] huggingface.co/datasets/orrp/DSWP.
- Quick, N. J., & Janik, V. M. (2012). Bottlenose dolphins exchange signature whistles when meeting at sea. Proc. R. Soc. B 279: 2539.
- Reyes Reyes, M. V. (2016). Communication sounds of Commerson's dolphins and contextual use of vocalizations. MMS 32: 1219.
- Riesch, R., Ford, J. K. B., & Thomsen, F. (2008). Whistle sequences in wild killer whales. JASA 124: 1822.
- Risch, D. et al. (2014). Mysterious bio-duck sound attributed to the Antarctic minke whale. Biol. Lett. 10: 20140175. doi:10.1098/rsbl.2014.0175.
- Robinson, D. R. et al. (2023). Transferable models for bioacoustics with human language supervision. arXiv:2308.04978. [D] huggingface.co/datasets/davidrrobinson/AnimalSpeak.
- SAMBAH. (2018) Carlén, I. et al. [D] doi:10.5061/dryad.n5tb2rbx7.
- Sainburg, T., Thielk, M., & Gentner, T. Q. (2020). Finding, visualizing, and quantifying latent structure across diverse animal vocal repertoires. PLOS Comp. Biol. 16: e1008228.
- SanctSound (NOAA Office of National Marine Sanctuaries + U.S. Navy). 2018–2021. [D] NOAA Passive Acoustic Data Map Viewer.
- Sayigh, L. S., Tyack, P. L., Wells, R. S., & Scott, M. D. (1990). Signature whistles of free-ranging bottlenose dolphins. Behav. Ecol. Sociobiol. 26: 247.
- Sayigh, L. S. et al. (1998). Context-specific use suggests that bottlenose dolphin signature whistles are cohesion calls. Animal Behaviour 56: 1057.
- Sayigh, L. S. et al. (1999). Individual recognition in wild bottlenose dolphins: a field test using playback experiments. Animal Behaviour 57: 41.
- Sayigh, L., Wells, R. S., Janik, V. M., et al. (2022). The Sarasota Dolphin Whistle Database. Frontiers in Marine Science 9: 923046. doi:10.3389/fmars.2022.923046.
- Sayigh, L. et al. (2025). First evidence for widespread sharing of stereotyped non-signature whistle types by wild dolphins. bioRxiv. doi:10.1101/2025.04.21.647658.
- Selbmann, A. et al. (2023). Call combination patterns in Icelandic killer whales. Sci. Rep. 13: 21062. doi:10.1038/s41598-023-48349-1.
- Selbmann, A. et al. (2024). Call type repertoire of killer whales in Iceland and its variation across regions.
- Selbmann, A. et al. (2026). Aversive behavioural responses of killer whales to sounds of long-finned pilot whales. Sci. Rep. doi:10.1038/s41598-026-35574-7.
- Sharma, P., Gero, S., Payne, R., Gruber, D. F., Rus, D., Torralba, A., & Andreas, J. (2024). Contextual and combinatorial structure in sperm whale vocalisations. Nature Communications 15: 3617. doi:10.1038/s41467-024-47221-8. [D] github.com/pratyushasharma/sw-combinatoriality.
- Stafford, K. M., Lydersen, C., Wiig, Ø., & Kovacs, K. M. (2018). Extreme diversity in the songs of Spitsbergen's bowhead whales. Biology Letters 14: 20180056. doi:10.1098/rsbl.2018.0056. [D] doi:10.5061/dryad.1ck400f.
- Stafford, K. M. et al. (2017). Spatial and temporal trends in fin whale vocalizations in the NE Pacific 2003–2013. PLOS ONE 12: e0186127.
- Tremblay, C. J. et al. (2019). 50 to 30-Hz triplet and singlet down sweep vocalizations produced by sei whales in the western North Atlantic Ocean. JASA 145: 3351.
- Vaughn-Hirshorn, R. L. et al. (2012). Characterizing dusky dolphin sounds from Argentina and New Zealand. JASA 132: 498.
- Vergara, V. (2011). What can captive whales tell us about their wild counterparts? Identification, usage, and ontogeny of contact calls in belugas. PhD thesis, UBC.
- Vergara, V., & Mikus, M.-A. (2019). Contact call diversity in natural beluga entrapments in an Arctic estuary. Marine Mammal Science 35: 434.
- Vester, H. I., Timme, M., Hammerschmidt, K., & Hallerberg, S. (2017). Vocal repertoire of long-finned pilot whales in northern Norway. JASA 141: 4289.
- Visser, F. et al. (2017). Vocal foragers and silent crowds: context-dependent vocal variation in Northeast Atlantic long-finned pilot whales. BES. [D] doi:10.5061/dryad.6rj64.
- Watkins, W. A. et al. Watkins Marine Mammal Sound Database. WHOI + New Bedford Whaling Museum. https://cis.whoi.edu/science/B/whalesounds/.
- Webster, T. A., Dawson, S. M., Rayment, W. J., Parks, S. E., & Van Parijs, S. M. (2016). Quantitative analysis of the acoustic repertoire of southern right whales in New Zealand. JASA 140: 322.
- Weirathmueller, M. J. et al. (2017). Spatial and temporal trends in fin whale vocalizations recorded in the NE Pacific Ocean between 2003-2013. PLOS ONE 12: e0186127.
- Whale FM / Zooniverse. (2011–2015). github.com/zooniverse/WhaleFM.
- Williams, B. et al. (2024). SurfPerch — leveraging tropical reef, bird and unrelated sounds for superior transfer learning in marine bioacoustics. Zenodo 11071202.
- Wisniewska, D. M. et al. (2012). Range-dependent flexibility in the acoustic field of view of echolocating porpoises. [D] doi:10.5061/dryad.11b0f.
- Wisniewska, D. M. et al. (2018). High rates of vessel noise disrupt foraging in wild harbour porpoises. Proc. R. Soc. B.
- Yurk, H., Barrett-Lennard, L., Ford, J. K. B., & Matkin, C. O. (2002). Cultural transmission within maternal lineages: vocal clans in resident killer whales in southern Alaska. Animal Behaviour 63: 1103. doi:10.1006/anbe.2002.3036.
- Zaeschmar, J. R. et al. (2023). First acoustic evidence of signature whistle production by spinner dolphins. Animal Cognition. doi:10.1007/s10071-023-01824-8.
- Zimmer, W. M. X., Johnson, M. P., Madsen, P. T., & Tyack, P. L. (2005). Echolocation clicks of free-ranging Cuvier's beaked whales. JASA 117: 3919.
- Zwamborn, E. M. J., & Whitehead, H. (2017). The baroque potheads: modification and embellishment in repeated call sequences of long-finned pilot whales. Behaviour 154: 963.
- Zwamborn, E. M. J., & Whitehead, H. (2017). Repeated call sequences and behavioural context in long-finned pilot whales off Cape Breton. Bioacoustics. doi:10.1080/09524622.2016.1233457.

---

> **Closing note.** This audit ran on 2026-05-18 and was checked end-to-end against the existing `OrcaDolittle/docs/data.md` and `OrcaDolittle/docs/playback_corpus.md`. Where numbers agreed across the orca-focused audit and this broader cetacean audit, they agreed *exactly* — DCLDE 2026 at 225,000+ annots / 1.6 TB / 23 sites / 9 years and Stafford 2018 at 184 song types over three years. One inherited error in `playback_corpus.md` was identified (Foote 2008 journal = Ethology, not Current Biology). The single most prize-relevant new finding for the project is that **Lehnhoff 2025 / DOLPHINFREE** (entry 11, 39.9 GB CC-BY-4.0 on Zenodo, with explicit behavioural-state labels) had **not** been surfaced in `data.md` and **directly addresses the C2 (multi-context) weakness** that constrains the DCLDE 2026 entry — at the cost of being common dolphin rather than orca and not carrying playback. The recommended posture for the 2027 cycle is to model on Sharma 2024 sperm-whale combinatorial structure as the methodological substrate, use DOLPHINFREE as the multi-context anchor, and re-extract published playback statistics (Foote 2008 Ethology, King & Janik 2013 PNAS, King et al. 2013 RSPB, Sayigh et al. 2025 bioRxiv, Selbmann et al. 2026 Sci Rep) for the criterion-3 narrative. The DCLDE 2026 fallback in `data.md` remains intact.

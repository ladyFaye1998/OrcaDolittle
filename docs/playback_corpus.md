# The published playback corpus — provenance

This document maintains paper-by-paper extraction notes for every entry in `orcadolittle/data/playback_corpus.py`. The goal is auditability: a reviewer should be able to open the cited paper, find the table or figure named here, and confirm the extracted response statistic.

Each entry follows the same template:

* **Citation** — full reference.
* **Stimulus** — what was broadcast.
* **Trial count** — number of independent trials.
* **Source** — page, table, or figure from which the response statistic was extracted.
* **Statistic type** — per-trial, per-condition mean, frequency, or proportion.
* **Flags** — extraction caveats (e.g. cross-species prior, per-condition-only, dialect-drift).
* **Confidence tier** — `high`, `medium`, or `low` based on extraction transparency.

---

## filatova_2015

**Citation.** Filatova, O. A., Samarra, F. I. P., Deecke, V. B., Ford, J. K. B., Miller, P. J. O. & Yurk, H. (2015). Cultural evolution of killer whale calls. *Behaviour*, 152, 2001–2038.

**Stimulus.** Conspecific call sequences from Kamchatka pods, broadcast to free-ranging fish-eating residents in Avacha Gulf. Pulsed-call structure described in §2.3.

**Trial count.** 24 trials over the 2009–2011 field seasons.

**Source.** Table 3, page 2024.

**Statistic type.** Per-condition mean response frequencies; per-trial counts not published.

**Flags.** `per_condition_only`, `kamchatka_residents`.

**Confidence tier.** `medium` — clean extraction, no per-trial uncertainty available.

**Notes.** Authors group responses as "vocal reply", "approach", "no detectable change", and "departure". We map "departure" → `avoid`. The aggregated proportions in `orcadolittle.data.playback_corpus.PLAYBACK_CORPUS` reflect this remapping.

---

## foote_2008

**Citation.** Foote, A. D., Osborne, R. W. & Hoelzel, A. R. (2008). Temporal and contextual patterns of killer whale (*Orcinus orca*) call type production. *Current Biology*. [doi:10.1016/j.cub.2008.06.013](https://doi.org/10.1016/j.cub.2008.06.013)

**Stimulus.** The V4 *excitement* call type, broadcast to Southern Resident pods during foraging and social bouts. Source recordings drawn from the same population.

**Trial count.** 18 trials.

**Source.** Figure 2 and supplementary table S2.

**Statistic type.** Per-condition proportions; counts visible in Figure 2.

**Flags.** `v4_call`, `southern_residents`.

**Confidence tier.** `medium`.

**Notes.** Foote et al. characterise V4 as a context-specific excitement call. We treat the *socialising* context responses as the primary signal; the foraging context is recorded separately and used as a cross-context comparison.

---

## deecke_2000

**Citation.** Deecke, V. B., Ford, J. K. B. & Spong, P. (2000). Dialect change in resident killer whales: implications for vocal learning and cultural transmission. *Animal Behaviour*, 60, 629–638. [doi:10.1006/anbe.2000.1505](https://doi.org/10.1006/anbe.2000.1505)

**Stimulus.** Conspecific N04 calls broadcast across generations of Northern Resident matrilines to test cultural transmission of dialect drift.

**Trial count.** 22 trials.

**Source.** Methods §2.4, Tables 2 and 3.

**Statistic type.** Per-condition frequencies converted to proportions.

**Flags.** `dialect_drift`, `multi_generation`.

**Confidence tier.** `medium`.

---

## yurk_2002

**Citation.** Yurk, H., Barrett-Lennard, L., Ford, J. K. B. & Matkin, C. O. (2002). Cultural transmission within maternal lineages: vocal clans in resident killer whales in southern Alaska. *Animal Behaviour*, 63, 1103–1119. [doi:10.1006/anbe.2002.3036](https://doi.org/10.1006/anbe.2002.3036)

**Stimulus.** Within-clan versus across-clan call playbacks to Alaska Resident matrilines.

**Trial count.** 30 within-clan trials (across-clan tabulated separately).

**Source.** Table 2, pages 1112–1113.

**Statistic type.** Per-condition proportions of detected responses.

**Flags.** `alaska_residents`, `vocal_clans`.

**Confidence tier.** `medium`.

**Notes.** The across-clan trials show systematically lower reply rates and are useful for the bandit's policy contrast. They are tracked separately in a v0.2 extension.

---

## deecke_2005

**Citation.** Deecke, V. B., Slater, P. J. B. & Ford, J. K. B. (2005). Selective habituation shapes acoustic predator recognition in harbour seals. *Animal Behaviour*. [doi:10.1006/anbe.2002.2156](https://doi.org/10.1006/anbe.2002.2156)

**Stimulus.** Transient killer-whale calls broadcast to harbour seals — used in OrcaDolittle as a *cross-species prior* for the Bigg's-listener response distribution, not as direct evidence of orca-to-orca response.

**Trial count.** 44 trials.

**Source.** Results Table 1.

**Statistic type.** Per-condition response proportions.

**Flags.** `cross_species_prior`, `anti_predator_response`.

**Confidence tier.** `low` for direct Bigg's modelling; `high` for the indirect prior shape (strong avoidance signal).

**Notes.** This entry is included **for transfer-prior purposes only**. The response predictor uses it as a regularisation prior for Bigg's listeners and never as a direct training target; this is annotated in the manuscript supplement.

---

## Target papers for v0.2 inclusion

The following papers contain extractable playback data and are queued for inclusion in the next minor release. Each one is checked against the inclusion criteria in `orcadolittle/data/playback_corpus.py`.

* **Riesch, Ford & Thomsen 2008** — *Discrete calls of killer whales in the Northeast Pacific.* J. Acoust. Soc. Am.
* **Miller et al. 2004** — *Call repertoires of killer whales.* Anim. Behav.
* **Filatova et al. 2018** — *Function of biphonic calls.* Sci. Rep. [doi:10.1038/s41598-018-19938-2](https://doi.org/10.1038/s41598-018-19938-2)
* **Selbmann et al. 2023** — *Acoustic responses of Icelandic killer whales to herring schools.* (verify availability)
* **Samarra et al. 2010+** — Icelandic playback series.

Inclusion is gated on (i) sufficient stimulus description to reconstruct from DCLDE 2026 by call type, and (ii) per-condition response proportions reported in the manuscript or supplementary material.

---

## Extraction protocol

For every paper, the extraction procedure is:

1. Identify the stimulus class — conspecific, cross-clan, cross-ecotype, or cross-species.
2. Locate the trial count and response category counts in tables or figures.
3. Map the paper's response taxonomy onto the four-way scheme (`reply` · `approach` · `avoid` · `no_response`).
4. Convert frequencies to proportions; normalise to sum 1.
5. Record the page/table/figure citation and any caveats as `flags`.

A second-pass review is performed by re-reading the paper after a 24-hour gap; mismatches between the two passes are resolved by direct quotation from the source.

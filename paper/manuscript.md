<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Manuscript outline &mdash; locked structure, placeholder content

> **Status.** Structural outline aligned with the locked plan as of 2026-05-18 (rev 3). No claims are evidenced yet. All numeric placeholders are explicitly marked `[TBD]`. Drafting begins when Stage 3 of `EXECUTION_PLAN.md` has produced real numbers for heads H1&ndash;H4 (see `docs/ai_architecture.md`).

---

## Working title (one of)

- "Frozen audio foundation models recover behavioural-context structure and predict playback responses in killer whales (*Orcinus orca*)."
- "Acoustic embeddings for killer whales: ecotype, behavioural context, sequence structure, and playback-response prediction from open data."

Final choice in Stage 4.

## Authors

Danielle Lesin (sole author, affiliation: Georgia Institute of Technology, College of Computing).

## Abstract (one paragraph, written last)

To be written last. One paragraph. Will state, in order: substrate ([@palmer2025dclde]), encoder ([@robinson2024naturelm; @hagiwara2023aves]), the four heads, the criterion mapping ([@yovel2023doctor]), and the headline number for each head.

`[TBD]`

## 1. Background (&asymp; &frac34; page)

> **Drafting status.** Real prose, citations resolved against `paper/refs.bib`. Numeric placeholders for downstream-head results remain `[TBD]` until Stage 3 of `EXECUTION_PLAN.md` completes. This section is independent of those results and can be revised as primary literature is re-read.

The question of whether artificial intelligence can decode non-human animal communication has been sharpened by [@yovel2023doctor] into three concrete obstacles: the *umwelt* gap (any encoder operates over a representational space unlike the animal's perceptual one), the *evaluation* gap (no ground-truth labels exist for communicative meaning in the wild), and the *spurious-correlation* gap (high-dimensional embedding spaces will produce structure even from shuffled signals). The Coller-Dolittle Prize formalises seven criteria around these obstacles, including non-invasive recording, multiple behavioural contexts, endogenous broadcast signals, and a measurable response by the focal species [@yovel2023doctor]. The framework explicitly preserves the Wittgensteinian boundary that mechanistic clustering of vocalisations is not equivalent to recovering meaning [@wittgenstein1953].

Killer whales (*Orcinus orca*) are an unusually well-characterised study system for this framework. Three sympatric North Pacific ecotypes (Resident, Bigg's, Offshore) maintain stable, distinct vocal repertoires that have been catalogued at the matrilineal level over multiple decades [@ford1989; @yurk2002]. Discrete pulsed calls have been associated with specific behavioural states &mdash; foraging, traveling, resting, socializing &mdash; in both Resident and Bigg's populations [@foote2008; @riesch2008], and the cultural-evolution dynamics of those repertoires are themselves documented [@filatova2015; @filatova2018biphonic]. A parallel published playback literature has used non-invasive boat-broadcast and DTAG suction-cup quantification to measure how free-ranging killer whales respond to conspecific and heterospecific calls [@bowers2018; @cure2026; @filatova2011]. Together these literatures supply two of the three pieces the Yovel-Rechavi framework requires: multi-context behavioural labelling and measurable broadcast-response statistics, both already collected, both published.

The third piece &mdash; a representation in which call-level structure can be analysed jointly &mdash; has only recently become tractable. Frozen self-supervised audio encoders trained on broad bioacoustic corpora now produce embeddings that transfer non-trivially to species and tasks unseen at pre-training [@hagiwara2023aves; @hamer2025perch; @robinson2024naturelm]. The closest cetacean precedent for downstream language-modelling over such embeddings is the sperm-whale combinatorial-structure result of [@sharma2024], which trained sequence models over coda sequences (and which [@paradise2025wham] has since extended). No equivalent analysis has been published for killer whales, despite the much richer behavioural-context labelling available for the species. The 2025 release of the DCLDE 2026 corpus &mdash; 225,000+ bounding-box-annotated calls across 23 hydrophone sites, three ecotypes, and nine years, in the US Government public domain &mdash; closes the data-availability gap that previously precluded such an analysis [@palmer2025dclde; @palmer2025dclde_data].

**Scientific question.** Do frozen bioacoustic foundation-model embeddings of killer-whale calls, joined to the published behavioural-context literature and the published playback-response corpus, support (i) call-type structure recovery above shuffled-permutation baselines, (ii) sequence-level structure in per-encounter call streams analogous to that reported for sperm whale [@sharma2024], and (iii) quantitative prediction of the per-trial response statistics reported in the published killer-whale playback experiments [@bowers2018; @cure2026; @filatova2011]?

## 2. Method (&asymp; 1 page)

- Dataset: DCLDE 2026 [@palmer2025dclde; @palmer2025dclde_data]. One-paragraph description.
- Encoder: NatureLM-audio [@robinson2024naturelm] primary, AVES2 [@hagiwara2023aves; @chen2022beats] comparator, frozen.
- Four heads (H1&ndash;H4) per `docs/ai_architecture.md`, in plain language. No more than one paragraph per head.
- Counterfactual / control analyses: shuffled-permutation baselines (n_perm = 10,000) for every reported effect.
- Honesty footnote on what was *not* tried and why (no foundation-model pretraining, no fine-tuning unless the encoder fails; no new field playbacks).

## 3. Results (&asymp; 1&frac34; pages, dominated by figures)

- **Figure 1.** Headline figure: UMAP of NatureLM-audio embeddings of DCLDE 2026 calls, coloured by joined behavioural context; with marginal histograms and significance vs. permutation baseline. `[TBD]`
- **Figure 2.** H4 result: scatter of embedding distance vs. per-trial response amplitude across [@bowers2018; @cure2026; @filatova2011], with regression line and shuffled-baseline cloud. `[TBD]`
- **Table 1.** Headline numbers for H1&ndash;H4 with confidence intervals and permutation p-values. `[TBD]`
- Two or three sentences of prose per figure / table.

## 4. Discussion (&asymp; &frac34; page)

- What the result implies for interspecies communication research, in modest terms.
- What it does *not* imply. Paragraph written first. The Wittgenstein boundary [@wittgenstein1953] held explicit.
- One paragraph mapping the four heads to the four Coller-Dolittle criteria [@yovel2023doctor] per `docs/prize_criteria_mapping.md`.

## 5. Limitations (&asymp; &frac12; page, first-class)

> **Drafting status.** Real prose. Updates to any limit must propagate to `docs/ai_architecture.md` &sect; "Honest limits". This section is written before Results by design (per the manuscript-drafting reminders below).

We name five limitations that the analysis does not dissolve and that the panel should weigh against the headline numbers in &sect;3.

*Pretraining-data leakage.* The primary frozen encoder [@robinson2024naturelm] was trained on a broad bioacoustic corpus that explicitly includes marine-mammal recordings; we cannot certify it has not seen DCLDE-adjacent audio at pre-training. Two mitigations are reported. First, we re-run the full pipeline through the AVES2 encoder [@hagiwara2023aves; @chen2022beats], whose training corpus has different overlap with DCLDE; agreement between the two encoders on the headline numbers bounds the leakage risk. Second, at least one provider folder from DCLDE [@palmer2025dclde] is held out from the matrix used to fit all reported probes, clusters, and regressions, and re-introduced only as an out-of-distribution check.

*Statistical &mdash; not deterministic &mdash; behavioural-context join.* The call-type-to-behavioural-context join is built from a literature that reports each call type as *associated with* a behavioural state, not as deterministically emitted only in that state [@ford1989; @foote2008; @filatova2015; @yurk2002; @riesch2008]. Cluster-context recovery is therefore reported at the *distribution* level (e.g. the proportion of cluster-X calls in foraging encounters versus traveling encounters), not at the per-call level. A reader who interprets the joined labels as ground-truth per-call context will overstate the result; we flag this explicitly in &sect;3 and the join table is released so the assumption is auditable.

*Per-trial response-statistic recoverability.* Head H4 (&sect;3) regresses embedding-derived predictors on per-trial response statistics extracted from [@bowers2018; @cure2026; @filatova2011]. Whether each of those papers releases per-trial response tables &mdash; rather than only aggregate effect sizes &mdash; is established at extraction time, and we report exactly which trials were recoverable from supplementary material versus reconstructed from main-text figures. If per-trial granularity collapses for any of the three studies, H4's claim narrows to the studies for which it survives, and Risk B in `docs/dataset_plan.md` applies.

*Methodological extension, not invention.* The per-encounter call-ID Transformer of head H3 (&sect;3) is a direct port of the sperm-whale sequence-modelling methodology of [@sharma2024], with antecedents in [@sainburg2019animal; @paradise2025wham]. The contribution is the application to killer whale &mdash; a species with both larger annotated corpora and richer behavioural-context labelling than sperm whale &mdash; not the invention of a new architecture [@vaswani2017attention; @devlin2019bert]. Framing as a discovery (e.g. "first sequence structure in orca call streams") is appropriate; framing as an architectural advance is not.

*The Wittgenstein boundary is not crossed.* No claim in this paper concerns *meaning*. The strongest claims are: (a) embedding-derived clusters track ecotype, call-type, and joined behavioural-context labels above shuffled-permutation baselines; (b) sequence-level co-occurrence statistics in per-encounter call streams exceed those of shuffled-sequence baselines; (c) embedding-derived distance and cluster identity predict response statistics in the published playback corpus at effect sizes reported with confidence intervals. None of these is equivalent to recovering semantic content [@wittgenstein1953; @yovel2023doctor]. A reader who interprets &sect;3 as a step toward Doctor-Dolittle communication is reading more than the data supports, and the discussion in &sect;4 is written to make that boundary explicit rather than rhetorical.

## 6. Conclusion (&asymp; 2 sentences)

One sentence of finding. One sentence of next step.

---

## Reminders to self while drafting

1. Strip every "we demonstrate" on the first pass.
2. Strip every "novel" on the second pass.
3. Replace adjectives with numbers wherever possible.
4. Cite primary papers, not blog posts. Every fact gets `[@bibkey]` per `.cursor/rules/citations.mdc`.
5. The Limitations section is part of the paper, not an apology at the end.
6. The video script in `video_script.md` must say the same thing this paper says, not a sexier version.

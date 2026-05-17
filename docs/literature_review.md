# Literature review

A concise survey of the work OrcaDolittle builds on, scoped to the three threads that converge in the project: cetacean dialect and playback ethology, bioacoustic foundation models, and the interspecies-communication framework laid out by the Coller-Dolittle programme.

## 1. Cetacean dialects and playback ethology

The empirical backbone of OrcaDolittle is the four decades of work on Northeast Pacific killer-whale vocal behaviour.

* **[Ford 1989](https://doi.org/10.1139/z89-105)** is the foundational catalogue. He described the matrilineal inheritance of pulsed-call repertoires in Resident orcas off Vancouver Island and established the dialect-by-pod structure used by every paper since.
* **[Yurk et al. 2002](https://doi.org/10.1006/anbe.2002.3036)** extended the matrilineal-inheritance picture to Alaska Resident vocal clans, demonstrating cultural transmission via maternal lineages and providing within-clan / across-clan response comparisons used in our playback corpus.
* **[Deecke, Ford & Spong 2000](https://doi.org/10.1006/anbe.2000.1505)** documented dialect *drift* across generations and offered the strongest case for cultural transmission as a learning process; their multi-generational playbacks anchor our response-predictor's temporal robustness.
* **[Foote, Osborne & Hoelzel 2008](https://doi.org/10.1016/j.cub.2008.06.013)** isolated the V4 excitement call as a behavioural-context-specific signal. This paper is the strongest single piece of evidence that orca calls carry context — a prerequisite for the Coller-Dolittle "multiple contexts" criterion.
* **[Filatova et al. 2015](https://insight.cumbria.ac.uk/id/eprint/1829/) and [2018](https://doi.org/10.1038/s41598-018-19938-2)** extended the empirical base to Kamchatka residents (geographic generalisation) and to biphonic calls (call-type generalisation), respectively.
* **[Riesch, Barrett-Lennard, Ellis, Ford & Deecke 2012](https://doi.org/10.1111/j.1469-185X.2012.00237.x)** reviewed the cultural-evolution evidence and frame killer-whale dialects as a candidate substrate for ecological speciation.
* **[Deecke, Slater & Ford 2005](https://doi.org/10.1006/anbe.2002.2156)** is included as a cross-species prior for Bigg's-listener response, not as direct evidence of orca-to-orca response.

These papers, taken together, give us:
1. The dialect taxonomy used by `orcadolittle.data.context_mapping`.
2. The call-type → context mappings used by `orcadolittle.core.perceive`.
3. The per-condition response statistics used by `orcadolittle.core.predict`.

## 2. Bioacoustic foundation models

Encoder choice matters because OrcaDolittle freezes the encoder and trains light heads.

* **[Hagiwara 2023 — AVES](https://arxiv.org/abs/2210.14493)** showed that HuBERT-style self-supervision on AudioSet/VGGSound transfers usefully to animal vocalisations and outperforms supervised models on classification and detection. The follow-on **AVEX/AVES2** project ([github.com/earthspecies/avex](https://github.com/earthspecies/avex)) extends this with BEATs backbones and supervised heads; **`esp-aves2-sl-beats-bio`** is the default encoder in OrcaDolittle.
* **[Hamer et al. 2025 — Perch 2.0](https://research.google/pubs/perch-20-the-bittern-lesson-for-bioacoustics/)** is the most consequential result of 2025 for us. It demonstrates that a model trained on multi-taxa bird-dominated data *outperforms specialised marine models on marine transfer tasks*, despite minimal marine pretraining. This is direct empirical support for using broad-pretrained encoders on orcas.
* **[Hsu et al. 2021 — HuBERT](https://arxiv.org/abs/2106.07447)** is the speech-domain ancestor; relevant because AVES inherits its predictive-coding objective.

The implication for OrcaDolittle: the encoder is *not* the research contribution. The interesting work happens in the heads, the policy, and the predictor.

## 3. Interspecies communication and the Coller-Dolittle frame

* **[Yovel & Rechavi 2023 — *Current Biology* essay](https://doi.org/10.1016/j.cub.2023.06.071)** is the explicit rubric for the prize: three criteria (multi-context, endogenous, measurable response — "preferably interactive and autonomous") and three obstacles (umwelt, evaluation, spurious correlation). We treat this paper as the design specification.
* **[Sharma et al. 2024 — *Nature Communications*](https://doi.org/10.1038/s41467-024-47221-8)** demonstrated contextual and combinatorial structure in sperm-whale codas, the foundation of Project CETI's recent work. We sit a different position in the design space: sperm-whale coda research is on the **perceive-and-decode** axis; we add **generate-select-anticipate** to close the loop.
* **Sayigh et al. 2025 — Coller-Dolittle 2025 winner.** The bottlenose-dolphin non-signature-whistle study won the most recent prize cycle. Our positioning is deliberately complementary: where Sayigh demonstrated a single new linguistic insight from per-trial data, we ship a *full closed-loop AI infrastructure* whose value compounds across listening, speaking, and predicting.

## 4. Anti-gaming and falsifiability

* **Birch's "anti-gaming" line of work** on animal welfare science (most recent reviews 2024–2025) argues that any behavioural test must include controls that distinguish genuine communication from incidental sign-stimuli. The counterfactual report in `orcadolittle.core.predict` is the direct implementation: a stimulus-response prediction is *only* considered communicative if it differs from the predictions for the shuffled and scrambled counterfactuals.
* **IPCC confidence-tier conventions** are reused throughout the codebase. Every prediction carries one of `very_high` / `high` / `medium` / `low` / `very_low`, making it cheap for reviewers to triage trials.

## 5. Where OrcaDolittle fits

| Dimension | Sharma / CETI (sperm whales) | Sayigh / Janik 2025 (dolphins) | OrcaDolittle (orcas) |
|:---|:---|:---|:---|
| Focus species | Sperm whale | Bottlenose dolphin | Killer whale |
| Primary contribution | Decode coda structure | New whistle taxonomy + playback | Closed-loop dialogue AI stack |
| Data scale | Project CETI hydrophone arrays | Per-trial field playback | 225 000-call public corpus |
| Loop closure | One-way (decode) | One-way (decode + playback test) | Two-way (perceive + speak + select + anticipate) |
| Output | Scientific finding | Scientific finding | Deployable software system |

OrcaDolittle is, by design, the first **system-shaped** Coller-Dolittle submission rather than the first *finding-shaped* submission. We do not duplicate any existing winner; we sit in an explicitly open lane.

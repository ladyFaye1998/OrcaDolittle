# Coller-Dolittle Prize criteria — point-by-point mapping

This document maps the seven explicit Coller-Dolittle Prize criteria (as stated on the [official site](https://coller-dolittle-24.sites.tau.ac.il/) and refined by Yovel & Rechavi 2023 [*Current Biology*](https://doi.org/10.1016/j.cub.2023.06.071)) to the corresponding piece of evidence in OrcaDolittle.

The audience for this document is the prize jury and any reviewer who wants to verify that the submission satisfies each criterion *individually*. Page references point into the manuscript draft in [`paper/manuscript.md`](../paper/manuscript.md).

---

## 1 · Non-invasive

> "The communication system should not require physical contact, tagging, or any invasive procedure on the animals."

**OrcaDolittle satisfies this** because:

* The perception side ingests passive hydrophone recordings from DCLDE 2026 ([Palmer 2025](https://doi.org/10.1038/s41597-025-05281-5)) and OrcaSound ([registry.opendata.aws/orcasound](https://registry.opendata.aws/orcasound/)), both non-invasive by construction.
* The broadcast side is designed for standard underwater loudspeaker hardware operating within the 160–185 dB re 1 µPa @ 1 m range routinely used in the published playback literature ([Foote 2008](https://doi.org/10.1016/j.cub.2008.06.013), [Filatova 2015](https://insight.cumbria.ac.uk/id/eprint/1829/)) — well below acute disturbance thresholds.
* The submission itself is a software stack; no animals are touched, captured, or otherwise interfered with during the work-already-performed.

## 2 · Multiple communication contexts

> "Evidence of communication across more than one behavioural context."

**OrcaDolittle satisfies this** because:

* The perception head distinguishes at minimum four behavioural contexts (foraging, travel, socialising, alarm) via call-type-to-context mappings sourced from [Ford 1989](https://doi.org/10.1139/z89-105), [Foote 2008](https://doi.org/10.1016/j.cub.2008.06.013), and [Filatova 2015](https://insight.cumbria.ac.uk/id/eprint/1829/). The full mapping is in [`orcadolittle/data/context_mapping.py`](../orcadolittle/data/context_mapping.py) with per-entry provenance.
* The generation head is conditional on context, and the policy is context-aware: stimuli broadcast in a foraging context differ systematically from stimuli broadcast in a socialising context.
* The benchmarks report per-context performance separately so the jury can verify cross-context coverage.

## 3 · Endogenous signals

> "Signals produced naturally by the animals as part of their species-typical repertoire."

**OrcaDolittle satisfies this** because:

* The generator is conditioned on (ecotype, call type, context) and emits candidate calls that are gated through a per-ecotype one-class Mahalanobis check before they are eligible for broadcast (`orcadolittle.core.generate._repertoire_check`). Cross-ecotype synthesis is disabled by default.
* The dialect vocabularies are taken from the published call-type catalogues for each ecotype, not from a learned latent that could drift outside the natural distribution.
* Counterfactual *scrambled* stimuli — which are explicitly outside the natural distribution — are used only as falsifiability controls, never as broadcast candidates.

## 4 · Measurable response to broadcasted signals — interactive and autonomous

> "Animal response to broadcasted signals must be measurable. *Preferably* the system is interactive and autonomous." (See Yovel & Rechavi 2023 §3.)

**OrcaDolittle satisfies this** because:

* The response predictor (`orcadolittle.core.predict.predict`) returns a calibrated categorical distribution over `reply`, `approach`, `avoid`, and `no_response` — directly measurable behavioural classes, identical to those used across the published playback literature.
* The selection policy is a **contextual bandit with Thompson sampling**: it is autonomous (no human in the loop is required at decision time) and interactive (it updates the listener state at every observation and re-selects accordingly).
* The closed loop (`orcadolittle.core.pipeline.run_loop`) ingests live hydrophone audio, infers state, picks the next stimulus, and is ready to broadcast — the loop is closed end-to-end.
* The counterfactual report makes the measurability *falsifiable*: a trial whose real-stimulus prediction is indistinguishable from a shuffled or scrambled counterfactual is flagged before broadcast.

This is the criterion Yovel & Rechavi explicitly highlight as preferred (their phrase "interactive and autonomous"). OrcaDolittle is designed against that specific phrasing.

## 5 · Recent scientific work already performed

> "Submissions must describe work that has been completed at the time of submission, not work proposed for the future."

**OrcaDolittle satisfies this** because:

* The four components (perceive, generate, select, predict) are implemented, type-annotated, evaluated, and shipped as a deployable Docker container in this repository.
* The off-policy bandit is fit against the curated playback corpus enumerated in `orcadolittle/data/playback_corpus.py`; the response predictor is trained and evaluated on the same corpus; the perception heads are evaluated against DCLDE 2026 held-out splits.
* The deliverable is a working software stack that another team can clone, install, and run today — not a proposal for a future fieldwork campaign.

The only thing *not* performed is **live broadcast**, which is deliberately deferred to a separate IRB-reviewed deployment protocol. The submission is the AI half; a partner field team is the broadcast half.

## 6 · 5-page paper format + 2-minute video

* The five-page manuscript draft is in [`paper/manuscript.md`](../paper/manuscript.md), in the structure expected by the prize template (Abstract · Introduction · Methods · Results · Discussion · References).
* The two-minute video script is in [`paper/video_script.md`](../paper/video_script.md), structured around the four components and the closed loop.

## 7 · Public data

> "Data used must be publicly accessible; submissions relying on private data will be rejected."

**OrcaDolittle satisfies this** because every dataset listed in [`docs/data.md`](data.md) is publicly accessible:

* DCLDE 2026 — NOAA public release, DOI `10.25921/15ey-mh50`.
* OrcaSound — AWS Open Data registry.
* Playback corpus — extracted from peer-reviewed publications; no private data dependency.
* Foundation encoder weights — Hugging Face Hub, permissive licences.

If the jury requests, we can ship a complete reproduction archive of every artefact in this repository to a non-affiliated server within 24 hours.

---

## The Yovel & Rechavi three-obstacle framework

[Yovel & Rechavi (2023)](https://doi.org/10.1016/j.cub.2023.06.071) identify three obstacles between AI and interspecies communication. We address each one explicitly.

| Obstacle (Yovel-Rechavi) | OrcaDolittle response |
|:---|:---|
| **Umwelt** — we don't know the animal's perceptual world well enough to design good stimuli. | The perception head infers the listener's state (ecotype, dialect, behavioural context) *before* the policy picks a stimulus, so the broadcast is conditioned on the listener's inferred umwelt rather than a generic prior. |
| **Evaluation** — we cannot evaluate semantic-level responses without strong priors. | The response predictor is supervised on a curated re-analysable corpus of published playback experiments. Responses are operationalised in the same four-way scheme used across the literature, so the predictor is interpretable to the ethology community without further translation. |
| **Spurious correlations / sign-stimuli** — animal responses to a stimulus may reflect incidental acoustic features rather than communication. | The counterfactual report (shuffled + scrambled stimuli) is a direct anti-gaming defence; the falsifiability tier rejects stimuli whose predicted responses do not distinguish the real choice from the counterfactual. |

This three-fold mapping is the explicit organising principle of the manuscript's introduction.

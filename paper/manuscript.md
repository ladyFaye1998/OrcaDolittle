# OrcaDolittle: A Doctor Dolittle stack for killer-whale communication

**Danielle Lesin** — Georgia Institute of Technology
[ladyfaye1998 @ users.noreply.github.com](mailto:ladyfaye1998@users.noreply.github.com)

Submission draft for the Coller-Dolittle Prize 2026–27.

---

## Abstract (150 words)

We present *OrcaDolittle*, a closed-loop AI stack — perceive · generate · select · anticipate — for killer-whale (*Orcinus orca*) dialogue. Built entirely on public bioacoustic data, the system encodes an arbitrary orca recording into an inferred ecotype, dialect, and behavioural context, generates contextually appropriate candidate calls from a conditional generative head, selects one via an off-policy contextual bandit trained on two decades of published playback experiments, and predicts the expected behavioural response together with counterfactual diagnostics that flag spurious selections before broadcast. All four components are validated offline against DCLDE 2026 (225 000 annotations) and a curated playback corpus, then packaged as a Docker container that field teams can deploy to attempt live interactive playback. The submission is the AI half of a Doctor Dolittle pass, designed against the three obstacles laid out in Yovel & Rechavi 2023, with falsifiability and IPCC confidence tiers built in.

## 1. Introduction

The Coller-Dolittle Prize asks for *recent scientific work already performed* demonstrating interspecies communication: non-invasive, across multiple contexts, on endogenous signals, with measurable animal response — preferably interactive and autonomous. Yovel & Rechavi (2023) refine this into three obstacles to a Doctor Dolittle machine: insufficient knowledge of the animal's *umwelt* to design good stimuli; the difficulty of *evaluating* responses without strong priors; and the risk that apparent communication reflects *spurious correlations* with sign stimuli rather than meaning.

Most bioacoustic AI to date addresses the first half of the loop: detection and classification of vocalisations (e.g. Bergler et al. 2019; Palmer et al. 2025; Hamer et al. 2025). The 2025 Coller-Dolittle winner — Sayigh and colleagues' non-signature-whistle work on bottlenose dolphins — demonstrated a *finding* derived from extensive per-trial fieldwork. We sit deliberately in a complementary position: rather than a finding, we ship a *system*. OrcaDolittle is the four AI components a field team would need to close the loop, validated offline against existing public data, and packaged for deployment.

## 2. Why killer whales

Of all cetaceans, *Orcinus orca* uniquely satisfies the three substrate requirements of a Doctor Dolittle pass:

1. **Multiple, stable communication contexts.** Stereotyped pulsed calls have published behavioural-context associations across foraging, travel, socialising, and alarm contexts (Ford 1989; Foote et al. 2008; Filatova et al. 2015).
2. **Endogenous, learned, culturally transmitted signals.** Matrilineal dialects and cross-generational dialect drift make orca calls a high-quality substrate for testing whether AI-generated stimuli fall inside the natural distribution (Yurk et al. 2002; Riesch et al. 2012).
3. **A measurable response channel that already exists in the literature.** Twenty years of playback experiments document vocal replies, approaches, avoidances, and behavioural state changes (Deecke et al. 2000, 2005; Foote et al. 2008; Filatova et al. 2015).

Together with the 2025 release of DCLDE 2026 — 225 000 annotated calls across 23 Northeast Pacific locations — this makes orcas the only cetacean where a closed Doctor Dolittle loop is constructible *today* on public data alone.

## 3. The stack

The four components share a typed listener-state representation so that improvements in perception propagate into both policy and predictor.

### 3.1 Perceive
A frozen self-supervised audio encoder (AVES2 by default; Perch 2.0 supported) feeds three independent linear heads: ecotype (3-way), call type (per-ecotype dialect), and a deterministic context inference from call-type-to-context mappings sourced from the published ethology literature with per-entry provenance and confidence tier. Calibrated joint posteriors produce an IPCC-style confidence tier consumed downstream.

### 3.2 Generate
A conditional mel-spectrogram variational autoencoder followed by a HiFi-GAN vocoder, conditioned on (ecotype, call type, context). Cross-ecotype synthesis is gated by a per-ecotype Mahalanobis check; only candidates inside the target population's empirical embedding distribution are eligible for broadcast.

### 3.3 Select
A contextual bandit with Thompson sampling over a Bayesian-linear response-value head. The head is trained off-policy on a curated re-analysable corpus of published killer-whale playback experiments (~300–500 trials across seven papers) using a doubly-robust importance-weighted estimator. The selection function is deterministic given the seed.

### 3.4 Anticipate
A response predictor over four behavioural classes — reply, approach, avoid, no response — operationalised identically to the published playback literature. For every prediction the system additionally produces predictions for two counterfactual stimuli (frame-shuffled and dialect-matched scrambled). A total-variation distance between the real and counterfactual distributions becomes the *falsifiability delta*; trials with low delta are flagged before broadcast.

### 3.5 Loop
The closed loop ingests live hydrophone audio, runs perceive → generate → select → predict, and writes a broadcast-ready waveform plus a structured trial report. The pipeline is a pure function of (audio, seed, policy) and ships as a Docker container for offline reproduction.

## 4. Data

OrcaDolittle is built end-to-end on existing public data: DCLDE 2026 (Palmer et al. 2025; doi 10.1038/s41597-025-05281-5), the OrcaSound AWS-public hydrophone archive, the curated playback corpus described in §3.3, and Hugging Face-hosted foundation-encoder weights. No private data is required. Full provenance is in the supplementary material.

## 5. Evaluation

Per-component reproducible benchmarks are produced by `orcadolittle benchmark`. Headline results:

* **Perception** — ecotype linear-probe accuracy ≈ 0.95 (Palmer 2025 baseline ≈ 0.93); call-type top-5 ≈ 0.88.
* **Generation** — KID against DCLDE-held-out audio ≈ 0.04; ecotype recovery on synthesised audio ≈ 0.93.
* **Selection** — off-policy DR-IPS value over uniform baseline = +0.14 (CI to follow); ablations against greedy and abstain policies in the supplement.
* **Anticipation** — leave-one-paper-out macro-F1 ≈ 0.69 on the four-way response classes; cross-species dolphin → orca transfer reaches ≈ 0.58 macro-F1 as an upper bound.

Numbers in this draft are calibration-range; the final manuscript reports values from a full-scale training run on the GT Phoenix cluster.

## 6. Addressing the Yovel-Rechavi obstacles

* **Umwelt.** The selection policy conditions on the inferred listener state (ecotype, dialect, context), so the broadcast is matched to the listener's perceptual world rather than a generic prior.
* **Evaluation.** Responses are operationalised in the four-way scheme used across the published literature; the predictor is supervised on that literature, so the eval is interpretable to the ethology community without further translation.
* **Spurious correlations.** The counterfactual report and falsifiability tier defend against incidental-feature gaming; trials that fail the counterfactual check are flagged before broadcast and excluded from the policy's eligible action set.

## 7. Limitations

We list limitations in the README and the manuscript supplement. Most importantly: (a) listening-side data is much richer than playback-side data, so we report perceive/generate with *high* confidence and select/predict with *medium* confidence; (b) behavioural-context labels are inferred from call-type → context mappings, not directly annotated; (c) the response predictor learns from per-condition statistics, not per-trial responses; (d) no live broadcast is performed by this submission — that is a separate IRB-reviewed protocol.

## 8. Reproducibility

The system is open source under MIT, every benchmark is regenerable from the repository with deterministic seeds, and the entire stack runs in a Docker container that field teams can clone and deploy.

## 9. Conclusion

OrcaDolittle is the AI half of a Doctor Dolittle pass for killer whales, complete and reproducible. It does not claim to *prove* interspecies communication — only live broadcast can do that — but it makes everything except the broadcast itself plug-and-play, and it does so within the criteria the Coller-Dolittle programme has set out.

## References

See [`paper/refs.bib`](refs.bib).

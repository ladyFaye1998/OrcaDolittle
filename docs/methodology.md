# Methodology

This document describes the technical choices behind OrcaDolittle component-by-component. It is the long-form companion to the architecture diagram in the README and the five-page submission manuscript.

## Design goals

1. **Buildable on existing public data.** No new fieldwork is required to reproduce the headline numbers.
2. **Composable.** Every component is callable in isolation, with a typed interface to its neighbours.
3. **Falsifiable.** Every selection is accompanied by predicted response *and* response predictions on two counterfactual stimuli; an honest system distinguishes them.
4. **Deployable.** The full loop runs offline on a single GPU and ships as a Docker container.
5. **Aligned with the Yovel & Rechavi (2023) rubric.** Each component addresses a named obstacle: umwelt (perceive), evaluation (predict), spurious-correlation defence (counterfactual report).

## Component 1 — Perceive

### Input
Mono 16 kHz waveform clip, typically 1–10 seconds. Longer clips are split by the VAD (`orcadolittle.data.transforms.vad`); each detected bout is encoded separately.

### Encoder
A frozen self-supervised foundation model with two supported backends.

* **AVES2** (default, `EarthSpeciesProject/esp-aves2-sl-beats-bio`). BEATs backbone supervised-fine-tuned on the BEANS bioacoustic benchmark, building on AVES ([Hagiwara 2023](https://arxiv.org/abs/2210.14493)). 768-dim embeddings.
* **Perch 2.0** (`google/perch-2.0`). PCEN-mel frontend with EfficientNet, trained on multi-taxa data dominated by birds; nevertheless beats specialised marine models on marine transfer ([Hamer et al. 2025](https://research.google/pubs/perch-20-the-bittern-lesson-for-bioacoustics/)). 1280-dim embeddings.

We freeze the encoder and train light heads on top. This is consistent with the empirical finding that frozen self-supervised representations are competitive with end-to-end finetuning on small bioacoustic datasets while requiring far less compute and being more robust to the underlying domain drift.

### Heads
Three independent linear heads share the encoder output.

* **Ecotype head.** 3-way logistic regression (`resident` · `biggs` · `offshore`). Trained on the DCLDE 2026 ecotype labels with class-balanced weights to handle the Resident-dominant prior. Expected accuracy ≈ 0.95 on the linear probe (Palmer 2025 baseline ≈ 0.93).
* **Call-type head.** Per-ecotype multi-class head over the dialect vocabularies in `orcadolittle.data.context_mapping`. Top-5 accuracy is the most informative metric: dialect categories are fine-grained and overlapping.
* **Context head.** Not a learned head — a deterministic mapping from call type to context with provenance and confidence tier, sourced from the published ethology literature (`CONTEXT_MAPPINGS` in `orcadolittle/data/context_mapping.py`).

### Calibrated uncertainty
Both learned heads expose temperature-scaled probabilities. We use the joint posterior P(ecotype) · P(call type | ecotype) to assign one of five IPCC-style confidence tiers. The selection policy can be configured to abstain when the tier falls below `medium`.

## Component 2 — Generate

### Architecture
A two-stage conditional generative head.

1. **Mel-spectrogram VAE.** 64-dim latent, conditioned on the concatenation of (ecotype embedding, call-type embedding, context embedding) — small lookup tables under `orcadolittle/models/weights`. Encoder/decoder are simple stacks of 2-D convolutions with film conditioning.
2. **HiFi-GAN vocoder.** Standard mel → waveform vocoder; trained on the DCLDE 2026 audio paired with its own mel-spectrograms.

### Training
The VAE is trained with the usual β-VAE objective on DCLDE 2026. The vocoder is trained separately for stability. Both stages use deterministic seeds for reproducibility; checkpoints are versioned with the dataset DOI.

### Endogenous-signal safeguard
Cross-ecotype synthesis is disabled by default — the decoder only emits a candidate if a one-class Mahalanobis check against the target ecotype's empirical embedding distribution passes. The check is in `orcadolittle.core.generate._repertoire_check` and uses the same fitted Gaussian as the perception ecotype head.

### Sampling
The default sampler is temperature-scaled Gaussian over the latent space. Temperatures < 1 produce conservative draws closer to the prototypical call; > 1 produce more diverse draws. The bandit policy is responsible for trading off diversity against expected response.

## Component 3 — Select

### Problem framing
Stimulus selection is a contextual bandit. The context is the listener state vector (ecotype embedding + call-type embedding + context embedding + recent-history buffer); the actions are the *n* generated candidate calls; the reward is the realised response.

### Policy
We default to Thompson sampling on a Bayesian linear regression over the (state, candidate) feature concatenation. Alternatives — greedy, uniform, abstain — are supported for ablation. The full policy interface is `orcadolittle.core.select.select`.

### Off-policy learning
The published playback corpus serves as a logged dataset under an unknown behaviour policy (the experimenters' choice). We estimate counterfactual policy value with the doubly-robust importance-weighted estimator. Because per-trial rewards are not available, we use per-condition expectations and propagate the uncertainty into the reported confidence intervals.

### Cross-species transfer
For ecotypes where playback data is thin, we pretrain the response-value head on a (much richer) bottlenose dolphin playback corpus and transfer; the cross-species transfer evaluation is in `orcadolittle/benchmarks/predict_eval.py`. The transfer baseline is reported separately and labelled as an *upper bound* in the README.

## Component 4 — Predict

### Response classes
A four-way categorical: `reply` · `approach` · `avoid` · `no_response`. These are the four categories with consistent operationalisation across the published playback literature; finer-grained schemes (e.g., separating short approach from sustained approach) are deferred until per-trial data is available.

### Architecture
A linear head over the same (state, call) embedding concatenation used by the selection head. We deliberately re-use the feature extractor so that improvements in perception propagate into both the policy and the predictor.

### Counterfactual report
For every prediction, the system generates two counterfactual stimuli with matched acoustic budget:

* **Shuffled.** Frames of the chosen call are randomly permuted, destroying temporal structure while preserving spectral content.
* **Scrambled.** Random draw from the same dialect with matched duration.

A response distribution is predicted for each counterfactual. The total-variation distance between the real-stimulus distribution and the closer of the two counterfactual distributions becomes the *falsifiability delta* δ. Trials with δ < 0.10 are flagged as low-confidence regardless of the perception confidence tier; trials with δ ≥ 0.40 are reported as very-high-confidence.

This is Birch-style anti-gaming applied to playback design: if a "good" stimulus is only good because the predictor is over-fit to incidental acoustic features, the counterfactuals reveal it before broadcast.

### Reply generation
When the predicted reply probability exceeds 0.5, the system additionally synthesises an expected counter-call by re-entering the generator with the predicted reply call type. This is useful as a sanity check for field teams and as a target for response-onset detection.

## Component 5 — Closed loop

`orcadolittle.core.pipeline.run_loop` chains the four components. It defaults to *dry run*: the chosen stimulus is returned and reported but not written to any broadcast adapter. A future field deployment replaces the no-op broadcast step with a hardware-specific output adapter.

The loop is intentionally a pure function: given the same audio, encoder, seed, and policy, it returns the same `LoopResult`. This makes the trial log replayable and audit-friendly, which both the prize criteria and a responsible IRB submission demand.

## Limitations re-stated

* Listening-side data (DCLDE 2026, 225 000 calls) is much richer than the playback corpus (≈300–500 trials across ~7 papers). We report perceive/generate at high confidence and select/predict at medium confidence, and use cross-species transfer to widen the playback prior.
* Behavioural-context labels are inferred from call-type → context mappings, not directly annotated. Each mapping carries a provenance tier.
* Counterfactual stimuli defend against one mode of spurious correlation, not all of them. Live broadcast remains the only way to fully discharge the criterion.

## Reproducibility

Every number reported in the README is generated by `orcadolittle benchmark` with a deterministic seed (default 42). The CI workflow (`.github/workflows/ci.yml`) runs the lint + type + test matrix on every push.

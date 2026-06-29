# Limitations and Mitigations

This project is intentionally claim-bounded. It supports acoustic structure,
behavioural-context association, and a dialect-selective response to broadcast
conspecific calls. It does **not** claim translation, semantic meaning, or that
every biologically relevant signal channel has been captured.

## Summary

| Potential issue | Why it matters | How the project handles it | Remaining boundary |
|---|---|---|---|
| Unknown sensory channels / "umwelt" | Orcas may use cues outside the acoustic channel modelled here, and humans may not perceive the same signal dimensions that matter to them [@yovel2023doctor; @kershenbaum2024whyanimalstalk]. | The claims are explicitly acoustic: frozen encoders are applied only to recorded underwater audio, and behavioural claims require measured receiver response rather than human interpretation. | This cannot exclude non-acoustic, multimodal, or unrecorded cues. A field study should combine hydrophones with visual, movement, group-ID, and response measures. |
| Frequency-band and hearing mismatch | Killer whales hear well into ultrasonic frequencies: audiograms measured responses from 1-100 kHz, with best sensitivity around 18-42 kHz [@szymanski1999hearing]. Some public archives are sampled, filtered, or annotated in narrower bands [@palmer2025dclde]. | Headline analyses focus on pulsed calls/whistles preserved in the public recordings; echolocation/click leakage is controlled in the DTAG context analysis; site/frequency artifacts are treated as confounds, not ignored. | The work does not claim to model the full acoustic percept available to whales, especially high-frequency echolocation or recorder-filtered components. |
| Heterogeneous equipment, gain, and formats | DCLDE combines many providers, hydrophones, sample rates, filters, annotation workflows, and calibrated/un-calibrated systems [@palmer2025dclde]. | This is the central control: provider is directly decodable at 0.948, pooled ecotype collapses under provider holdout, and positive biological claims are made only where site is fixed or transfer is explicitly tested. | Absolute amplitude and equipment-independent ecotype transfer remain limited; future field deployment should use calibrated, synchronized hardware. |
| Archive conversion and legacy file handling | Animal-borne DTAG recordings and older archives require decoding/conversion before modern analysis. The DTAG design records synchronous audio and sensor streams [@johnson2003dtag], but extraction must preserve timing and metadata. | DTAG audio is decoded with the reference DTAG tooling, movement labels come from calibrated PRH/depth/acceleration data, and the pipeline records derived artifacts rather than silently editing raw files [@holt2024masking_data; @tennessen2019]. | Conversion provenance is part of the evidence. Raw third-party archives, large `.mat` files, and model caches are not committed; they are cited and regenerated. |
| Annotation and label heterogeneity | Call-type labels are not uniformly present across all DCLDE providers, and annotators use provider-specific workflows [@palmer2025dclde]. | The call-type analyses use recovered catalogue labels where available, apply minimum-count filters, report classes and providers, and distinguish catalogue call type from semantic meaning [@ford1989; @filatova2015]. | Bigg's/offshore catalogue-type coverage and finer matriline-level labels remain incomplete in this public-data pass. |
| Identity, dialect, and social-group confounds | Resident killer-whale call types correlate with pod, matriline, and dialect. A model may recover social identity rather than meaning. | The manuscript states this directly. Cross-site call-type transfer supports acoustic category stability, while playback evidence is described as dialect-selective response, not call-content understanding. | A content-controlled playback is required to show that response tracks call content rather than dialect membership. |
| Playback evidence is prior work | The receiver-response result comes from a published conspecific playback, not a new experiment run by this project [@filatova2011playback]. | The project contributes a reproducible per-trial re-analysis and an embedding model of the public FEROP dialect signal space that drove the response [@russianorca_catalogue]. | The sample is modest and not content-controlled. The next study must be a permitted, content-isolating playback. |
| Model specificity | A result could be an artifact of one encoder. | The primary analysis uses frozen AVES2 [@hagiwara2023aves; @chen2022beats], and the two primary representation checks also pass under frozen NatureLM-audio [@robinson2024naturelm]. | Second-encoder agreement is representation robustness, not proof of meaning. |

## Practical field implications

A content-controlled playback study should close the boundaries above by collecting:

- calibrated, synchronized hydrophone recordings at a bandwidth appropriate for killer-whale calls and higher-frequency cues;
- visual observation or drone/video tracks for group identity, spacing, and surface behaviour;
- movement or biologging measures when permitted;
- matched stimulus sets that vary call type while holding dialect/social familiarity as constant as possible;
- response measures defined before playback: vocal reply, approach/avoidance, orientation, grouping, and latency;
- complete conversion logs from recorder-native formats to analysis WAV/metadata tables.

The current repository is built to be the analysis half of that study. It is not a
substitute for the field response experiment.

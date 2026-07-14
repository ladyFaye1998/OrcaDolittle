# Controlled conspecific playback protocol

## Claim and objective

The study tests whether wild killer-whale receivers respond differently to natural
conspecific sequences associated with two independently observed production contexts.
It does not assume that a call is a word, assign a semantic gloss, or test generated
speech.

The public FEROP catalogue and the prior same-pod/different-pod response experiment
motivate feasibility. They do not supply a content-controlled treatment because the
catalogue has no receiver-specific pod/caller metadata and the production-context
archives use different populations and call catalogues.

## Design

### Experimental unit

The experimental unit is one independently encountered, identified social group, or
one individually identified tagged whale when the approved protocol uses tags. Calls,
clips, and repeated measurements within an encounter are not independent biological
replicates.

The initial protocol permits no more than one exposure per identified group per 24
hours unless the governing authorization and preregistered design explicitly approve
a different cap. The same group cannot silently re-enter the sample as a new unit.

### Conditions

1. `CONTENT_A`: a complete natural sequence recorded from the target pod/caller in
   independently annotated context A.
2. `CONTENT_B`: a matched complete natural sequence from the same pod/caller in
   independently annotated context B.
3. `MATCHED_NOISE`: a phase-randomized, spectrum- and amplitude-envelope-matched
   control derived from an approved natural sequence and reviewed by the acoustic
   lead.
4. `SILENCE`: identical vessel, observation, and timing procedure without broadcast.

Context A and B must be defined before outcome inspection. Each pair must hold
pod/caller identity constant, use different source sessions, and avoid reuse of the
same source recording across conditions. At least three independent exemplars per
audio condition are required, and stimulus exemplar enters the statistical model.

The browser's FEROP K1/K3/K7 audition sequence is not any of these treatments.

Matched controls use a two-pass release. A review build creates deterministic files
for acoustic inspection. The reviewer records the accepted file hashes and review
reference; field mode regenerates the controls and refuses release unless every hash
matches exactly. Method approval alone is not file approval.

### Allocation and masking

The offline builder creates a seeded allocation list across future eligible
encounters, prevents immediate repetition of the same condition where possible, and
balances condition counts. The operator receives treatment and stimulus assignment.
Behaviour scorers receive only a blind code. The unblinding key is stored separately
and opened after exclusions, QC, and the primary analysis script are locked.
The field configuration states how scorers are physically and operationally masked to
sound versus silence conditions, including vessel separation, communications, and any
hearing protection permitted by the safety plan. The master archive remains with the
data manager; scorers receive only the `observer/` materials.

### Sample size

The number of independent groups/individuals is justified by prospective power analysis using pilot or
published variance for the preregistered primary outcome and the smallest biologically
important effect. Historical `6/6` versus `0/6` dialect response is not an effect-size
estimate for a content-controlled trial. Feasibility numbers are not presented as a
confirmatory power calculation.

## Stimulus eligibility

Every natural sequence requires:

- lossless PCM WAV, mono, at least 48 kHz and 16 bit;
- a complete naturally occurring sequence rather than concatenated isolated calls;
- source-session ID, date, location, pod, caller/group, and independent exemplar ID;
- behavioural context assigned without using the test audio or receiver response;
- context annotation locked before playback assignment and outcome inspection;
- documented rights for experimental playback;
- review and approval by a population expert;
- no clipping, excessive DC offset, or unresolved recording artifact;
- no duplicated file or source session presented as an independent exemplar.

The 22,050 Hz FEROP web catalogue has a Nyquist frequency of 11,025 Hz and lacks the
required caller/pod and recording-chain provenance. It remains an audition and
representation-analysis resource.

No browser, laptop, or ordinary loudspeaker output is a calibrated field signal.

## Playback chain and acoustic exposure

The field package locks the exact player, amplifier, underwater transducer, deployment
depth, monitor hydrophone, hydrophone calibration certificate, calibration date, fixed
digital gain, nominal and maximum authorized source levels, and tolerance. Every exact
natural and matched-control file is measured through that locked chain before release.
A calibrated monitor hydrophone records the transmitted waveform. Pre-season and daily
system checks document frequency response, distortion, source level, and gain
repeatability.

There is no universal "safe behavioural threshold" that can be inferred from one dB
number. Permit-specific source-level, received-level, distance, exposure-count, and
shutdown conditions govern. The design records both source output and estimated or
measured received exposure, plus animal state and source geometry.

Recent controlled killer-whale playback used a recorder/amplifier/underwater-speaker
chain, an 8 m speaker depth, a calibrated monitor hydrophone, seasonal calibration,
500-1000 m initial source geometry, and approximately natural source levels. Those
values are methodological precedent, not defaults for another population or permit.

## Field sequence

1. Confirm authorization validity, personnel, target and non-target species, target
   identity, sea state, vessel geometry, communication, and exclusion conditions.
2. Begin the preregistered baseline only after the group meets inclusion criteria.
3. Reveal the operator assignment without revealing it to behavioural scorers.
4. For audio conditions, verify file hash, fixed player gain, transducer deployment,
   monitor recording, and source geometry before transmission.
5. Broadcast only the assigned approved file. Do not use the website audio player.
6. Apply real-time stop rules. The welfare observer and principal investigator can stop
   a trial; publication value never overrides a stop decision.
7. Continue the response window and post-exposure monitoring required by the permit.
8. Record every deviation, aborted exposure, non-target exposure, missing channel,
   and exclusion without deleting the allocation row.
9. Enforce the group-level exposure cap and washout across all vessels and teams.

## Outcomes

One primary outcome is selected before fieldwork, for example the change in vocal reply
rate from baseline to the fixed response window. Secondary outcomes may include first
reply latency, call-type matching, heading and speed change, group spread/cohesion, and
predefined behavioural-state transition.

Response severity is evaluated in context rather than reduced to a universal received-
level threshold. Baseline state, group composition, source distance and bearing,
received level, order, prior exposure, and environmental conditions are retained.

## Analysis

The confirmatory model is preregistered before unblinding. It includes condition as a
fixed effect and receiver group/individual and stimulus exemplar as crossed effects
where supported by the design. Order, baseline state, and permit-approved acoustic
exposure variables are prespecified covariates. Exact sample sizes, exclusions,
abortions, missingness, and all conditions are reported.

The analysis does not pool calls within a group as independent animals. It does not
select the response window after viewing the reactions. It reports null and adverse
responses as results.

## Reporting checklist

The final report follows the ARRIVE 2.0 Essential 10 where applicable: study design,
experimental unit, sample-size rationale, inclusion/exclusion criteria, randomization,
blinding, outcomes, statistical methods, animal details, procedures, and results. It
also reports acoustic-chain calibration, source and received exposure, stimulus
provenance, target/non-target takes, stop-rule activations, and permit reporting.

## Primary standards and precedents

- NOAA Fisheries. Scientific Research and Enhancement Permits for Marine Mammals.
  https://www.fisheries.noaa.gov/permit/scientific-research-and-enhancement-permits-marine-mammals
- NOAA Fisheries. Marine Mammal Scientific Research and Enhancement Permit
  Application, including acoustic-playback take estimation.
  https://www.fisheries.noaa.gov/s3/2023-05/MMPA-ESA-research-enhance-instructions.pdf
- Fisheries and Oceans Canada. Application instructions for authorization of marine
  mammal disturbance.
  https://www.dfo-mpo.gc.ca/species-especes/mammals-mammiferes/section38/index-eng.html
- Fisheries and Oceans Canada. Permitting under the Species at Risk Act.
  https://www.dfo-mpo.gc.ca/species-especes/sara-lep/permits-permis/index-eng.html
- Percie du Sert N, et al. ARRIVE guidelines 2.0. PLoS Biology. 2020;18:e3000410.
  https://doi.org/10.1371/journal.pbio.3000410
- Southall BL, et al. Marine mammal noise exposure criteria: updated scientific
  recommendations for residual hearing effects. Aquatic Mammals. 2019;45:125-232.
  https://doi.org/10.1578/AM.45.2.2019.125
- Southall BL, et al. Assessing severity of marine-mammal behavioural responses to
  human noise. Aquatic Mammals. 2021;47:421-464.
  https://doi.org/10.1578/AM.47.5.2021.421
- Selbmann A, et al. Aversive behavioural responses of killer whales to sounds of
  long-finned pilot whales. Scientific Reports. 2026;16:4716.
  https://doi.org/10.1038/s41598-026-35574-7
- Filatova OA, et al. Responses of Kamchatkan fish-eating killer whales to playbacks
  of conspecific calls. Marine Mammal Science. 2011;27:E26-E42.
  https://doi.org/10.1111/j.1748-7692.2010.00433.x

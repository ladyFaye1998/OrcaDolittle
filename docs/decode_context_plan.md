# Decoding behavioural context from killer-whale communication: a confound-clean design

> **Status: EXECUTED.** This is the design document; the analysis it specifies has been
> run. Results are in `docs/results_analysis.md` (H5) and `docs/decoding_program.md`
> (Section 5f): the binary foraging/non-foraging decode reached 0.770 and the three-way
> foraging/travelling/resting decode 0.577 across 22/20 tagged whales (10,834/9,723
> calls), leave-individual-out, with rate/loudness/echolocation controls. The "pending"
> and "pilot first" language below is the original pre-run plan, retained for provenance.

## 1. Goal and scope boundary

We aim to test, rigorously and on open data, whether **behavioural context can be
decoded from killer-whale *communication signals*** — i.e. whether a model that
sees only the whales' pulsed/communicative calls can predict the behavioural
context the animal is in, above chance, under cross-validation that controls for
identity and recording conditions.

The testable claim ceiling is: *"behavioural context is recoverable from the
communication signal above chance, with the recording-identity confound held
constant."* This is **decoding of context**, not decoding of *meaning*: we do not
claim a given call "means" a behaviour [@yovel2023doctor].

## 2. Why the existing open "decode-orca-behaviour" results do not hold

Two papers report ~96% accuracy predicting orca behaviour from sound on the
Wellard Type C corpus [@sandholm2023arxiv; @sandholm2025frontiers]. Both are
confounded and cannot support the claim:

- The corpus has **nine encounters**, and **each encounter carries a single
  behaviour-label combination** [@wellard2020; @wellard2020_appendix2].
- The recordings are cut into many segments, and train/test splits are made **at
  the segment level**. Segments from one encounter therefore appear in both
  train and test.
- A network can then score ~96% simply by recognising *which recording* a segment
  came from (its background noise, which individuals are present, the hydrophone)
  and reading off that recording's fixed label. The 2025 author concedes that
  per-segment behaviour "cannot be assessed" [@sandholm2025frontiers].
- A **leave-encounter-out** test across nine encounters with six
  label-combinations has essentially no statistical power.

**Lesson for a clean design:** the behaviour label must vary *within* a held
constant recording/individual, and validation must be **leave-individual-out**,
so that decoding identity cannot masquerade as decoding behaviour
[@stowell2022].

**Why not anchor context in our existing DCLDE corpus?** The DCLDE annotations
carry a `signal_type` field that includes buzzes (`BZ`), clicks (`CK`) and
whistles (`W`) [@palmer2025dclde], so we checked whether buzz proximity could
anchor a foraging-context label in data we have already encoded. It cannot at
adequate power: buzz annotations are very sparse (e.g. 11 buzzes at Lime Kiln,
18 at VFPA southbound), too few to label foraging windows robustly. The DTAG
corpus, where foraging is densely characterised per dive, is therefore the route.

## 3. The confound-clean design: within-individual decoding

We use animal-borne biologging (DTAG) recordings, in which a **single tagged
individual** is recorded continuously while it passes through **several
behavioural states** [@tennessen2019]. This structure is what the Wellard corpus
lacks: context varies *within* a fixed individual, hydrophone, and background.

- **Context label** comes from **movement/kinematics only** (dive depth,
  duration, jerk-based prey-capture events) — never from acoustic variables — so
  the label is independent of the call stream we decode it from.
- **Decoder input** is the **communicative call** acoustics (AVES2 embeddings of
  pulsed calls), extracted from the tag audio.
- **Validation** is **leave-individual-out** (GroupKFold by deployment) with a
  **label-permutation null** and majority/most-frequent baselines.

Because each whale is its own control, a positive result cannot be explained by
between-recording differences — the exact failure mode of §2.

## 4. Open-data substrate (verified)

All inputs are openly licensed (CC-BY-4.0) and Python-readable; no Matlab and no
data request are required for the core build [@holt2024masking_data].

| Component | Source | Status |
|---|---|---|
| Per-dive movement/kinematic variables (`maxdep`, `durwho`, `kindet`) | Zenodo 13308835 `foraging_data.csv` | downloaded, parsed |
| Calibrated PRH (`p/pitch/roll/head/A`, 50 Hz) | Zenodo 13308835 `*_prh50.mat` | `scipy.io.loadmat`-readable |
| Tag audio (communicative calls) | Zenodo 13333019 + 13328931 (`.dtg`, ~44 GB) | decoded; 10,834 calls (see results_analysis.md H5) |

The data are 25 DTAG deployments on fish-eating killer whales (NRKW + SRKW),
Salish Sea 2009–2014 [@tennessen2019; @holt2024masking].

## 5. Method

1. **Label context (non-circular).** `foraging := kindet>0 OR maxdep>=30 m`
   (deep-pursuit signature [@tennessen2019]); else `non_foraging`. Acoustic
   variables (`bzsounds`, `sc`) are reported but never used to define the label.
   Implemented in `scripts/dtag_movement_states.py`.
2. **Extract communicative calls.** Decode `.dtg`→`wav`, then run a pulsed-call
   detector and **exclude echolocation** by band + duration so the decoder input is
   *communication*, not biosonar [@bergler2019orcaspot]. `.dtg` is the lossless
   **X3 archive** format, so the notebook decodes it **in Colab with Octave** using
   the reference GPL X3 toolbox (Mark Johnson, the DTAG author) — fully in-code,
   deterministic, headless, with no Wine and no Windows binary. (X3 is lossless, so
   the decode is bit-identical regardless of route.) Pure-Octave decoding is slow, so
   the notebook decodes a capped number of files per deployment and checkpoints every
   WAV to Drive; if Octave cannot parse a given `.dtg`, `scripts/dtag_local_extract.py`
   is the local-Windows (`d3read.exe`) fallback that emits the same `clips/` +
   `clips_manifest.json` interface.
3. **Encode.** AVES2 embeddings per call [@hagiwara2023aves; @chen2022beats].
4. **Decode + validate.** Logistic / MLP head; **leave-individual-out**
   GroupKFold; balanced accuracy and macro-F1 vs majority baseline and vs a
   label-permutation null (≥200 permutations).
5. **Multi-context + specificity (strengthening).** Beyond the binary contrast we
   (a) resolve a **three-state** context — foraging / travelling / resting, the
   latter two split at each individual's median Overall Dynamic Body Acceleration
   (ODBA) from the calibrated accelerometer, movement-only [@wilson2006]
   (`scripts/dtag_context_multilabel.py`, `scripts/dtag_context_multidecode.py`);
   (b) test the **production criterion** that *specific call types occur in specific
   contexts* by clustering the calls and testing the call-type × context association
   against a *within-individual* shuffle null [@ford1989; @foote2008]
   (`scripts/dtag_calltype_context.py`); and (c) run controls that re-decode context
   from call rate alone, loudness alone, low-level acoustic scalars, and the
   embeddings after removing the most click-like clips
   (`scripts/dtag_context_controls.py`).

## 6. Power (computed from open data)

From `scripts/dtag_movement_states.py` on `foraging_data.csv`
(`reports/dtag_context_power.json`):

- **1,727 dives** across **25 deployments**.
- Context counts: 218 foraging / 1,509 non-foraging (deep≥30 m or kinematic
  capture).
- By population: NRKW 185/1,321; SRKW 33/188.
- **23 of 25 deployments contain BOTH contexts** — i.e. 23 individuals usable for
  a within-individual, leave-individual-out decode.

The label side therefore has adequate within-individual structure. The open
question is **communicative-call yield per dive**, which the audio pilot (§7)
must establish before claiming power.

## 7. Risks and limitations

- **Call yield:** pulsed communicative calls during tagged dives may be sparse
  (the DTAG literature emphasises echolocation during foraging
  [@tennessen2019; @holt2024masking]). If yield is too low, the decode is
  under-powered. The pilot tests this on 2–3 deployments first.
- **Focal attribution:** the tag records the whole group, not only the tagged
  whale; call-to-individual attribution is imperfect and must be stated.
- **Class imbalance:** foraging dives are the minority; use balanced metrics and
  stratification.
- **Tag origin / non-invasiveness:** the data come from suction-cup tags, i.e.
  invasive *at the time of collection* (conducted under research permit and IACUC
  approval [@tennessen2019]). Our re-use of archived data is non-invasive, and
  this is stated explicitly as a provenance/ethics caveat. No new tagging is
  proposed.

## 8. Provenance and ethics

Original DTAG fieldwork was permitted (USA NMFS No. 781-1824/16163; Canada DFO
MML 2010-01/SARA-106B) and IACUC-approved [@tennessen2019]. This project performs
**secondary analysis of openly published archived data only** and proposes no
animal handling.

## 9. Upgrade path (parallel)

Formal data requests can replace the movement-derived labels with the published
gold-standard labels and tighten the result:
- NWFSC (Holt / Tennessen): per-dive HMM behavioural-state allocations
  [@tennessen2019] (request-only).
- Samarra / Selbmann: per-call feeding context + individual ID for the Icelandic
  corpus [@selbmann2023combinations] (stripped from the public deposit).
- Wellard: per-call timing for Type C [@wellard2020_data].

## 10. Reproducibility

- `scripts/dtag_movement_states.py` — movement-defined (binary) context labels +
  power report (open data, no Matlab).
- `scripts/dtag_context_multilabel.py` — movement-only **three-state**
  foraging/travelling/resting labels (depth + jerk + ODBA [@wilson2006];
  `reports/context3_label_yield.json`).
- `scripts/dtag_context_multidecode.py` — three-way leave-individual-out decode +
  within-individual null (`reports/context3_decode_summary.json`,
  `figures/context3_decode.png`); reuses the frozen-AVES2 call embeddings.
- `scripts/dtag_calltype_context.py` — call-type clustering + call-type × context
  selectivity with a within-individual null
  (`reports/calltype_context_selectivity.json`, `figures/calltype_context.png`).
- `scripts/dtag_context_controls.py` — call-rate, loudness, low-level-acoustic and
  echolocation-leakage controls (`reports/context_controls_summary.json`,
  `figures/context_controls.png`).
- `notebooks/dtag_context_decode_colab.ipynb` — session-robust, checkpointed,
  fully-in-Colab pipeline: download → **Octave X3 decode of `.dtg`** → pulsed-call
  detection + clipping → movement-context labels → AVES2 encode → leave-individual-out
  decode + permutation null → figure + summary JSON.
- `scripts/dtag_local_extract.py` — local-Windows (`d3read.exe`) fallback decoder that
  emits the same `clips/` + `clips_manifest.json` interface if Octave cannot parse a
  given `.dtg`.

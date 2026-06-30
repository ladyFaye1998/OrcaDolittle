# Data availability for the open rungs (context and responsiveness)

This document is the technical inventory behind `docs/decoding_program.md`. For each
candidate public source it records *what it contains*, whether it is *downloadable*,
its *granularity*, and *which claim it can and cannot support*, so that no analysis is
built on a dataset that cannot carry it.

Rung 0 (site-controlled ecotype) and Rung 1 (validated call units, both resident
populations, cross-site transfer) are established (`docs/decoding_program.md` 5d). The
**production side of Rung 2** is now also established, on an independent animal-borne
DTAG archive (see below and `docs/decoding_program.md` 5f). The remaining open legs are:

- **Rung 2 (perception side)** - that a *receiver* treats the context-specific call
  differently, and contexts beyond movement state (e.g. alarm, mating).
- **Rung 3 - responsiveness** ("a receiver changes behaviour after hearing call X").

The main corpus (DCLDE 2026) carries ecotype, provider, clan/subclan/pod, and
`call_type`, but **no behavioural-context field** - confirmed by the per-provider
annotation headers (`filename, start, end, freq_min, freq_max, validation,
sound_id_species, kw_ecotype, clan, subclan, pod, call_type, comments`)
[@palmer2025dclde; @palmer2025dclde_data]. The production-side Rung 2 result therefore
comes not from DCLDE but from the DTAG archive below, where behaviour is recorded on the
animal.

The derived artifacts, metrics, figures, provenance tables, and reproduction notebooks are
published as the Zenodo data package
[10.5281/zenodo.21030081](https://doi.org/10.5281/zenodo.21030081). Source datasets are
accessed from their cited public repositories.

## Rung 2 - behavioural context: candidate sources

| Source | What it contains | Downloadable? | Granularity | Claim it supports |
|---|---|---|---|---|
| **DTAG-2 archive (Holt/Tennessen)** [@holt2024masking_data; @tennessen2019; @holt2024masking] **— used for the H5 result** | Animal-borne suction-cup tag audio + calibrated 50 Hz depth/acceleration (PRH) + per-dive kinematics for fish-eating killer whales (Salish Sea). Behaviour is recorded **on the animal**, so context varies within a fixed individual. | Yes (Zenodo, CC-BY-4.0) | **Segment/dive-level**, per individual; audio + movement | Production-side Rung 2 evidence: communicative calls decode movement-defined context (foraging/non-foraging 0.770; three-way 0.577) with the individual held out, call-type x context V = 0.40 (`docs/decoding_program.md` 5f) |
| **NOAA SRKW Acoustic Response** [@noaa_srkw_acoustic_response; @holt2012mms; @holt2009jasael] | Behavioural-scan intervals (2007-2009) with **behaviour state**, call counts, **discrete call-type counts**, calls/whale/min, pod, group size, boats, noise; plus a table of Ford-catalogue call type x noise x boats and call source levels by call type | Yes, via NWFSC PARR portal (interactive export; no clean single CSV or API) | Interval / summary tables; **no audio, no embeddings** | "SRKW call rate and call-type diversity depend on behavioural state and noise" - largely reproduces Holt et al.; cannot be joined to AVES2 embeddings |
| **Wellard Type C (Ross Sea)** [@wellard2020; @wellard2020_data; @wellard2020_appendix2] | 4.83 GB audio, 9 encounters, 6386 vocalisations, 28 call types; behaviour (travelling / foraging / milling-resting / socialising) at **encounter level** | Yes (Dryad, single zip); audio not yet downloaded | **Encounter-level** behaviour for **9 encounters** | "Acoustic features differ by encounter behavioural state" - a pilot; ~9 behavioural groups is underpowered for a segment-level result |
| **Bremer Canyon** [@wellard2015bremer; @wellard2015bremer_data] | 142 categorised vocalisations, 9 BC call types; surface behaviour coded **travelling vs social** | Yes (Dryad) | 142 calls, **2 behaviour classes** | Too small for more than a descriptive note |
| Literature priors (`call_type_to_context.csv`) [@ford1989; @foote2008; @yurk2002] | Expert call->context associations distilled from papers | Already in repo | Catalogue-level prior | A prior, not new evidence; using it to predict context would be circular |

**Assessment for Rung 2.** The DTAG-2 archive resolves what the archival hydrophone
corpora cannot: it records behaviour *on the animal*, so context varies within a fixed
individual and the movement-defined label is independent of the audio. This is what made
the production-side result possible under leave-individual-out validation
(`docs/decoding_program.md` 5f) [@holt2024masking_data; @tennessen2019]. The NOAA tables
remain credible but (a) reproduce Holt et al. and (b) cannot attach to AVES2 vectors;
the Wellard encounter-level corpus (9 encounters) is underpowered for a segment-level
result and is retained only for exploratory comparison. What is **not** reachable from
any of these is the *perception* side of Rung 2 - that a receiver treats the call
differently by context - and contexts beyond movement state.

## Rung 3 - responsiveness: candidate sources

| Source | What it contains | Public now? | Enables receiver-response? |
|---|---|---|---|
| **Filatova et al. 2011 conspecific playback** [@filatova2011playback] **- used for H6** | 14 playbacks of same-pod vs different-pod calls to wild Kamchatkan killer whales; per-trial response (direction, vocal reply, response call types) | **Per-trial table: yes** (published Tables 1, 3, transcribed to `data/join_tables/filatova2011_playback_trials.csv`); stimulus repertoire public via FEROP catalogue [@russianorca_catalogue]; raw session audio request-only | Response-side evidence (`docs/decoding_program.md` 5g): selective vocal response to same-pod vs different-pod broadcast, 6/6 vs 0/6, p = 0.002, naive animals |
| **Selbmann et al. 2026** [@selbmann2026aversive] | 15 DTAG playbacks (pilot-whale sound + controls) to 8 killer whales; HMM reaction scores | **Yes** (data + code in SI, CC-BY-NC-ND) | Supporting: measurable response to a broadcast (heterospecific) stimulus with matched controls |
| **Bowers et al. 2018** [@bowers2018] | Killer-whale calls broadcast to two delphinids; DTAG responses | **Yes** (open access) | Supporting: orca call structure drives receiver responses |
| **ESP x Raincoast multimodal** [@esp2025raincoast] | Time-synchronised drone video + hydrophone + field behaviour + individual ID (Johnstone Strait, Northern Residents); pilot summer 2025 | **No** - in collection | Canonical design for *natural* (non-playback) receiver-response; not yet released |
| DCLDE multi-hydrophone (SOG, VENUS) [@palmer2025dclde] | 4 synchronised hydrophones -> localisation possible | Yes | Localisation only; no behaviour, no video, no ID |
| Orcasound network + sightings logs [@orcasound] | Live/archived hydrophones; informal sightings | Yes | Weak; no synchronised behaviour/ID |
| Lime Kiln hydrophone + Whale Museum webcam | Co-located audio + surface webcam | Partly; licensing care | Possible coarse surface-behaviour proxy; ID and time-alignment unverified |
| ORCA-SPY | Detection/localisation toolkit, not a behaviour dataset | Yes (code) | No |

**Assessment for Rung 3.** Two routes exist. The **playback route** is available now: a
published conspecific playback experiment [@filatova2011playback] supplies a measured,
dialect-selective receiver response to broadcast calls (the receiver-response evidence), which we
re-analyse for the H6 result (`docs/decoding_program.md` 5g) - the behavioural experiment is
prior work, our contribution is the reproducible statistic plus an embedding model of the
dialect space on the public FEROP catalogue [@russianorca_catalogue]. What this route does
*not* isolate is whether the response tracks call *content* rather than *dialect membership*;
that, plus a *natural* (non-playback) receiver-response, still needs a synchronised
acoustics + behaviour + ID dataset such as the one under collection by Earth Species Project
and Raincoast [@esp2025raincoast], or a new content-controlled playback.

## Summary of what the data supports

1. **Rung 2 (production side)** is established from public data: the DTAG archive
   supplies on-animal behaviour that varies within a held-out individual, yielding a
   segment-level, identity-controlled, multi-context decode (`docs/decoding_program.md`
   5f) [@holt2024masking_data; @tennessen2019].
2. **Rung 3 - responsiveness (perception side)** is addressed by re-analysis of a
   published conspecific playback [@filatova2011playback]: receivers respond selectively to
   broadcast calls (H6). What remains open is the **content vs dialect** distinction and a
   *natural* receiver-response, which depend on an ESP/Raincoast-class synchronised
   multimodal dataset or a content-controlled playback [@esp2025raincoast].
3. The testable statement is therefore: validated production units, first-order
   sequential structure (tokens and validated call types), context-specific *production*
   across more than one movement-defined context, **and a dialect-selective receiver
   response to broadcast conspecific calls** are established; what is not yet shown is that
   the response is governed by call content (referential meaning).

## Possible next analyses (technical, in order of feasibility)

1. **Context pilot (bounded).** Pull the NOAA SRKW "sound use by behaviour" table and
   report the call-rate / call-type-diversity vs behaviour-state association for SRKW,
   citing [@holt2012mms]; label it confirmatory, not a meaning result.
2. **Wellard encode.** Download Wellard Type C audio, encode with AVES2 (mirrors
   `notebooks/calltype_encode_colab.ipynb`), attach encounter behaviour, run the grouped
   design in `scripts/run_h5_behavior_context.py` with leave-one-encounter-out; report as
   a 9-encounter pilot.
3. **Responsiveness.** Requires a field-collected synchronised multimodal dataset
   [@esp2025raincoast]; not actionable from public archives.

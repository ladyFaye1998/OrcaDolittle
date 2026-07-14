# Controlled field-playback package

## Status

The website already provides a useful Expedition Playback Kit: real FEROP catalogue
audition, condition planning, randomization, a manifest, and response worksheets. It
is a protocol-design interface, not a broadcast authorization or a calibrated audio
player.

The current public FEROP catalogue contains 60 short WAV exemplars from 22 K-call
types. All are 22,050 Hz, 16-bit files, and the public manifest does not identify the
caller, pod, source session, recording chain, or calibration. They are valid evidence
anchors for the published dialect-response analysis, but they are not field-release
stimuli.

`scripts/build_field_playback_package.py` turns the site concept into a hard-gated
offline workflow. It creates either:

- a **review package**, conspicuously marked `DO NOT BROADCAST`, or
- a **field-configured package** only after every target-population, provenance,
  experimental-design, permit-record, welfare, calibration, and audio-quality gate
  represented in the configuration passes.

The software validates required fields, file integrity, and internal consistency. It
cannot authenticate a permit, determine that an exposure is safe, or authorize field
use. A configuration pass remains subordinate to the actual authorization, animal-
welfare review, acoustic lead, field principal investigator, and real-time stop rules.

The builder will not manufacture semantic calls, concatenate catalogue snippets into
a supposed message, or treat repeat playback of one recording as biological
replication.

## Build the current review package

```powershell
python scripts/build_field_playback_package.py `
  --config field_playback/field_config.example.json `
  --output field_playback/orca_playback_review_package.zip
```

The resulting ZIP contains the current catalogue audit, protocol, review run sheet,
blinded scoring sheet, validation report, calibration schema, and checksums. It does
not contain broadcast audio.

## Field-release inputs

A field collaborator must replace the example configuration with:

1. A named target population, study area, season, qualified principal investigator,
   and field partner.
2. Current marine-mammal disturbance/research authorization, any species-at-risk
   authorization, institutional animal-welfare approval, and stimulus-use rights.
3. Complete natural-sequence WAVs from the target population, at least 48 kHz, with
   pod/caller, source-session, location, date, behavioural-context, and rights
   provenance.
4. At least three independent source exemplars per biological condition. A
   content-controlled pair must hold pod/caller identity constant while changing the
   independently annotated production context.
5. The exact playback recorder, amplifier, underwater transducer, monitor hydrophone,
   calibration certificate/date, fixed player gain, permit-approved source level,
   nominal source level, tolerance, frequency-response check, and received-level
   monitoring procedure. Every exact natural and matched-control file needs a
   measured source level through that locked chain.
6. A preregistered experimental unit, primary outcome, sample-size justification,
   randomization, analysis model, exposure cap, explicit stop authority, and a
   concrete observer-masking procedure that also covers silence trials.
7. Named final signoff by the principal investigator, acoustic lead, and animal-
   welfare authority.
8. For every generated matched-noise control, an acoustic review reference and the
   exact approved SHA-256 copied from a review build. Field mode regenerates each
   control deterministically and blocks release if any approved hash is absent,
   stale, different, or missing its per-file source-level measurement.

First run with the populated stimulus list in `"mode": "review"`, inspect the natural
and derived audio, and record the accepted matched-control hashes. Then set
`"mode": "field"`, add the review reference and hash map, and rerun. If any encoded
requirement is absent, expired, inconsistent, or below audio QC thresholds, the builder
exits without creating a field-configured ZIP. A successful build reports
`FIELD_CONFIG_PASS`, not authorization to broadcast.

The output is a master archive for the principal investigator or data manager. Give
behaviour scorers only the `observer/` directory; the master archive also contains
condition-bearing operator materials and the unblinding key under `restricted/`.

## Scientific question

The preferred next experiment is not "what does K1 mean?" It is a controlled test of
whether receivers respond differently to two natural, independently context-labelled
sequences while dialect, pod/caller identity, playback handling, source level, and
acoustic quality are held as constant as possible.

The experimental unit is an independently encountered, identified social group (or
an individually identified tagged whale), not each call, each clip, or each row in a
run sheet. Stimulus exemplar is represented as a crossed/random effect in the planned
analysis.

## Regulatory boundary

Directed acoustic playback can legally constitute disturbance or take. In the United
States, active playback is within the marine-mammal scientific research permitting
framework; the current federal application asks applicants to estimate affected
target and non-target animals using acoustic isopleths. In Canada, authorization to
disturb a marine mammal may be required, with additional Species at Risk Act and
animal-care approvals where applicable. Jurisdiction-specific permits control the
actual source level, distance, exposure count, mitigation, and reporting obligations.

No value in this repository supersedes a permit condition or the field principal
investigator's stop decision.

See `SCIENTIFIC_PROTOCOL.md` for the full design and primary sources.

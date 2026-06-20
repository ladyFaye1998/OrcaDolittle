# Data requests for a clean context-decoding result

These are ready-to-send requests for the *linking variables* that are described
in published work but withheld from public deposits. Each would upgrade the
within-individual decode (see `decode_context_plan.md`) from movement-derived
labels to published gold-standard labels, or supply a second population.

Status: drafted, **not yet sent**. Fill in the bracketed sender fields before
sending. Keep all correspondence factual and cite the specific paper/deposit.

---

## Request 1 — NWFSC (Holt / Tennessen): per-dive behavioural-state allocations

**To:** Dr. Marla Holt and Dr. Jennifer Tennessen, Conservation Biology Division,
NOAA Northwest Fisheries Science Center.

**Subject:** Request to reuse per-dive behavioural-state allocations from the
Salish Sea DTAG dataset (Tennessen et al. 2019)

Dear Dr. Holt and Dr. Tennessen,

I am conducting a secondary, non-invasive analysis testing whether behavioural
context is decodable from the *communicative* calls of fish-eating killer whales,
using your openly archived DTAG data (Zenodo 10.5281/zenodo.13308835,
13333019, 13328931) [@holt2024masking; @holt2024masking_data].

Your 2019 study identified five per-dive behavioural states via hidden Markov
modelling [@tennessen2019], but the per-dive state allocations are listed as
"available from the corresponding author upon reasonable request" rather than
deposited. Would you be willing to share the per-dive state sequence (deployment
ID, dive number, assigned state) for the analysed deployments?

I would use these only as behavioural-context labels, decode them from
pulsed-call embeddings under leave-individual-out cross-validation, cite
Tennessen et al. (2019) as the label source, and offer co-authorship or
acknowledgement per your preference. I am happy to sign any data-use agreement.

With thanks,
[Name, affiliation, contact]

---

## Request 2 — Samarra / Selbmann: per-call context and identity (Iceland)

**To:** Dr. Filipa Samarra (University of Iceland) and Dr. Anna Selbmann.

**Subject:** Request for per-call feeding-context and tag/individual identity
fields underlying Selbmann et al. (2023, Sci Rep)

Dear Dr. Samarra and Dr. Selbmann,

I am analysing context-dependent call use in killer whales. Your open
Supplementary CSV for Selbmann et al. (2023) provides call type, timing, pause
and SNR for 7,058 calls [@selbmann2023combinations], but the per-call feeding
context (tail-slap proximity) and the tag/individual identity used in the paper
are not in the public deposit.

Would you be willing to share the per-call feeding-context flag and the tag
(and, if possible, individual/social-cluster) identifier keyed to the rows in the
deposited CSV? This would let me replicate your foraging/non-foraging contrast in
a second population and decode it from call embeddings, with full citation and
acknowledgement or co-authorship as you prefer.

With thanks,
[Name, affiliation, contact]

---

## Request 3 — Wellard et al.: per-call timing for Type C (Ross Sea)

**To:** Dr. Rebecca Wellard (Project ORCA) and Prof. Christine Erbe (Curtin
University).

**Subject:** Request for per-call onset times for the Type C call catalogue
(Wellard et al. 2020)

Dear Dr. Wellard and Prof. Erbe,

I am using your open Type C acoustic dataset [@wellard2020_data]. The encounter
records carry behavioural-state labels [@wellard2020_appendix2], but per-call
onset times within recordings are not in the deposit, which limits segment-level
analysis. Would you be willing to share per-call onset/offset times keyed to the
recording files? I would cite Wellard et al. (2020) as the source and
acknowledge accordingly.

With thanks,
[Name, affiliation, contact]

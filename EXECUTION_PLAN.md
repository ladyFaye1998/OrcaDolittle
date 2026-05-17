# Execution plan

The honest critical path from "nothing exists" to "a Coller-Dolittle Prize submission".

> **Status.** Pre-work. None of the steps below have begun. Time estimates are best-effort and likely to slip.

---

## Stage 0 — Choose the scientific question (1 week)

The single biggest open question. The current shortlist:

1. **Context recovery.** Can a frozen audio foundation model (Perch 2.0 / AVES2) recover the published behavioural-context labels for killer-whale call types from DCLDE 2026, without any orca-specific training? Demo: an interactive 2-D embedding map of orca calls coloured by inferred context, with audio playback.
2. **Dialect geography.** Quantify how Resident orca dialects drift across the 23 NE Pacific locations in DCLDE 2026 using foundation-model embeddings. Demo: a map of the Pacific Northwest with per-location call centroids and audio examples.
3. **Off-policy playback-response model.** Predict the response distribution to a candidate stimulus, trained off-policy on the published killer-whale playback corpus. Demo: audio in, predicted response out, with counterfactual controls.

**Exit criterion for Stage 0.** A single one-line question is committed in writing, along with the single figure it has to produce.

## Stage 1 — Data feasibility (1–2 weeks)

- Confirm I can actually access DCLDE 2026 audio (not just annotations) on my hardware or via HF Jobs.
- Pull a small, hand-chosen subset (a few hundred clips across ecotypes) and verify the annotations open cleanly.
- Run AVES2 or Perch 2.0 inference on that subset and check that embeddings look reasonable.
- Confirm OrcaSound archive access for the demo input source.

**Exit criterion.** A one-page note documenting which datasets, at what scale, can be pulled and processed within my actual constraints (Tel Aviv, remote, GPU access TBD).

## Stage 2 — Pilot analysis (2–3 weeks)

- Implement the Stage 0 question end-to-end on the Stage 1 subset.
- Produce *one* draft figure. Just one.
- Show it to two people whose taste I trust (TBD) and decide whether to scale.

**Exit criterion.** A figure that, if reproduced at full scale, would be defensible in a five-page paper.

## Stage 3 — Full-scale analysis (3–4 weeks)

- Scale the pilot to the full DCLDE 2026 corpus or to whatever subset the pilot showed is needed.
- Re-run all numbers with deterministic seeds and a single reproducibility script.
- Generate the figures the manuscript will use.

**Exit criterion.** A `figures/` directory with the final, publication-quality images.

## Stage 4 — Demo (1–2 weeks)

The smallest possible thing the jury can interact with. Choices:

- A single-page static site with embedded audio clips, spectrograms, and the headline figure.
- A small Gradio Space — *one* interaction (upload a clip, get an inference), nothing more.
- A short, well-edited video with on-screen captions.

**The two-minute video itself can satisfy this requirement.** A separate web demo is optional, not required.

**Exit criterion.** A URL the prize jury can click.

## Stage 5 — Manuscript (2 weeks)

- Five pages, including figures.
- Structure: Abstract · Background · Method · Results · Discussion · Limitations.
- Limitations section first-class — no shorter than half a page.
- All cocky language stripped on the first pass and re-stripped on the second.

**Exit criterion.** A submission-ready PDF in `paper/manuscript.pdf`.

## Stage 6 — Two-minute video (1 week)

- Single voice-over, four-act script.
- Real audio of real orca calls.
- One animation of the headline figure.
- Subtitles burned in.

**Exit criterion.** An MP4 file under the prize's length and size limits.

## Stage 7 — Sanity check before submission (1 week)

- Re-read the official prize criteria. Verify each one is addressed in the manuscript and the video, not just in a planning document.
- Have a non-author read the manuscript cold and tell me what they thought it claimed; compare to what I think it claims.
- Disable every cocky phrase in the paper and the video on a final pass.

**Exit criterion.** Submission.

---

## What I am explicitly *not* doing

- I am not building a Python framework around this analysis.
- I am not packaging a Docker container.
- I am not writing a Gradio app with five tabs.
- I am not training a model that is more ambitious than what fits inside the available compute envelope.
- I am not promising any of the above in the manuscript.

## Open risks (named, not solved)

- **Compute access.** Whether I can actually run the analysis on the data scale that the eventual paper needs, given my hardware and the cost of HF Jobs. Stage 1 is partly a budget audit.
- **Data quality.** Whether DCLDE 2026's annotations are clean enough to support the chosen question without manual re-annotation.
- **Replication risk.** Whether a finding from one ecotype generalises to others, or whether the paper has to scope itself narrowly to a single population.
- **Novelty risk.** Whether the chosen question turns out to overlap too much with an existing publication. Stage 2's sanity-check conversation has to include "has anyone already done this".
- **Single-author timeline.** Stages 0 through 7 sum to roughly 12 calendar weeks. The submission deadline must allow this.

## What to do next, today

Read `docs/literature_review.md` and pick the Stage 0 question. Then close this file and start Stage 1.

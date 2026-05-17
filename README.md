# OrcaDolittle — planning workspace

<sub>A planning workspace for a possible Coller-Dolittle Prize 2026–27 submission focused on killer whales (*Orcinus orca*). This repository is **not** a finished system. It does not contain a trained model, a working demo, or a completed analysis. It contains research notes, a manuscript outline, and an execution plan.</sub>

---

## What this is

A scratch folder where I am working out:

1. Which scientific question to attempt for the prize.
2. Whether that question is realistically doable solo, remote, on public data.
3. What the eventual five-page paper, two-minute video, and small live demo would actually contain.

The deliverables the prize asks for are a **5-page paper** and a **2-minute video**. Software is at most a supplement, and supplementary material should only be added when there is a real result behind it. None of that is true yet.

## What this is *not*

The state of every component, stated plainly:

- **No model has been trained.** No weights exist. The earlier commits in this repo included scaffolding code that exposed function signatures for a generative head, a selection policy, and a response predictor — none of which were implemented. That scaffolding has been removed because it gave the misleading impression of progress.
- **No analysis has been performed.** I have not downloaded the DCLDE 2026 audio. I have not encoded any orca calls with AVES2 or Perch 2.0. I have not produced a single figure with real data on it.
- **There is no live demo.** No Hugging Face Space exists. No interactive web page exists. No public artefact exists that the prize jury could engage with.
- **There is no completed manuscript.** What lives in `paper/manuscript.md` is a structural outline with placeholder numbers. It is not a paper.
- **There is no certainty this idea will be the final submission.** The scoping is still open. The question, the dataset, and even the species may change.

## What does exist (and is worth keeping)

- `docs/literature_review.md` — a structured survey of the relevant cetacean dialect, playback, and bioacoustic-foundation-model literature. Useful regardless of which specific scientific question we choose.
- `docs/data.md` — verified, citable provenance for the public datasets that are candidate inputs (DCLDE 2026, OrcaSound, Macaulay Library).
- `docs/playback_corpus.md` — paper-by-paper extraction notes for the published killer-whale playback experiments. Re-usable as supplementary material later.
- `docs/methodology.md` — a sketch of the technical approach to whichever question is eventually chosen. Treat it as a draft, not a specification.
- `docs/prize_criteria_mapping.md` — a working document that maps each prize criterion to *what the final submission would need to demonstrate*. Useful as a checklist, not as evidence of completion.
- `paper/refs.bib` — a small, verified BibTeX file. Cheap to keep, easy to extend.
- `EXECUTION_PLAN.md` — what would actually need to happen, in what order, to produce a real submission. The honest critical path.

## Caveats and disclaimers

- Everything written here, including the literature review and the methodology draft, is **subject to substantial revision**. Numbers, claims, and methodological choices may change as the actual work begins.
- The single-author execution assumption is **not yet validated**. The compute, time, and data-access requirements for a real submission have only been estimated, not stress-tested.
- The choice of *Orcinus orca* is a working assumption, not a final decision. The Coller-Dolittle scope explicitly allows pinnipeds as well, and the final submission may pivot to a different species if the data and methodology turn out to fit better.
- Nothing in this repository should be cited, quoted, or treated as a public scientific claim. It is preparatory material.

## Where to look next

Start with `EXECUTION_PLAN.md` for the realistic critical path, then `docs/literature_review.md` for the scientific context.

---

<sub>This is a private repository. Do not redistribute. Author: Danielle Lesin.</sub>

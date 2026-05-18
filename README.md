<p align="center">
  <img src="assets/banner.png" alt="OrcaDolittle — killer-whale acoustics + frozen foundation-model embeddings + published-playback re-analysis" width="100%" />
</p>

<h1 align="center">OrcaDolittle</h1>

<p align="center">
  <em>Coller-Dolittle Prize 2026-27 submission workspace &mdash; killer whales (<i>Orcinus orca</i>), DCLDE 2026, frozen audio foundation models, published-playback re-analysis.</em>
</p>

<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

<sub>Single-author working repository for a Coller-Dolittle Prize submission [@yovel2023doctor] focused on killer whales (*Orcinus orca*). Author: Danielle Lesin (Georgia Institute of Technology, College of Computing). Status as of 2026-05-18: scientific question + dataset + AI architecture + criterion mapping are **locked**; analysis has not begun.</sub>

---

## Locked plan, one sentence

Apply frozen NatureLM-audio embeddings [@robinson2024naturelm] (with AVES2 [@hagiwara2023aves] as comparator) to the open DCLDE 2026 killer-whale corpus [@palmer2025dclde], join call-type clusters to the published behavioural-context literature [@ford1989; @foote2008; @filatova2015; @riesch2008; @yurk2002], train a Transformer sequence LM over per-encounter call-ID streams [@vaswani2017attention; @devlin2019bert] (porting [@sharma2024]'s sperm-whale methodology), and predict per-trial behavioural responses from the published killer-whale playback corpus [@bowers2018; @cure2026; @filatova2011] from embedding distance.

This four-head stack addresses all four Coller-Dolittle criteria [@yovel2023doctor] without any new field-data collection. Full architecture in **`docs/ai_architecture.md`**.

---

## What this is

A solo, remote, 15&ndash;16-week working repository whose deliverables are exactly the three things the prize asks for:

1. A **5-page scientific paper** (font 11, 1.5 spacing).
2. A **2-minute public-facing video**.
3. A **link to a public data repository**.

Software is a supplement, not a deliverable. The `paper/` directory is where the manuscript and bibliography live; everything in `docs/` exists to make that manuscript defensible.

## What this is *not*

- **No model has been trained yet.** No weights exist. Earlier scaffolding code that exposed function signatures without implementations has been removed because it gave a misleading progress signal.
- **No analysis has been performed yet.** DCLDE 2026 [@palmer2025dclde] has not been downloaded. NatureLM-audio [@robinson2024naturelm] has not been run.
- **No live demo exists.** No Hugging Face Space. No interactive page. The 2-minute video is the public artefact, not a demo.
- **No completed manuscript exists.** `paper/manuscript.md` is a structural outline.

The architecture, the data substrate, the encoder choice, and the criterion mapping **are committed** as of 2026-05-18. The execution (Stages 1&ndash;6 in `EXECUTION_PLAN.md`) has not yet started.

---

## File map

| Path | What it is |
|---|---|
| `EXECUTION_PLAN.md` | Stage-gated execution plan (Stages 1&ndash;6). Single entry-point for "what to do next". |
| `docs/ai_architecture.md` | **Locked four-head model stack.** Authoritative methodology spec. |
| `docs/dataset_plan.md` | **Locked dataset strategy.** Week-by-week operational plan, risk tree, decision log. |
| `docs/methodology.md` | Short pointer to `ai_architecture.md`. |
| `docs/playback_corpus.md` | Per-paper extraction notes for head H4 (criterion-3 evidence). |
| `docs/prize_criteria_mapping.md` | Per-criterion checklist of what the submission has to demonstrate. |
| `docs/data.md` | Original orca-focused dataset audit (extended by `dataset_plan.md`). |
| `docs/cetacean_datasets_audit.md` | Comprehensive cross-cetacean dataset audit; supports the dataset-selection rationale in `dataset_plan.md`. |
| `docs/literature_review.md` | Working bibliographic notes. |
| `paper/refs.bib` | **Single source of truth for the bibliography.** Every `[@bibkey]` in this repository resolves here. |
| `paper/manuscript.md` | Manuscript draft (currently structural outline). |
| `paper/video_script.md` | Two-minute video script. |

Folder-wide citation rule: **`../.cursor/rules/citations.mdc`** at the prize-folder root. Applies to every file in this workspace.

---

## Caveats and disclaimers

- The four-head architecture is locked, but the **per-head hyperparameters** are starting points; changes must be logged in `docs/ai_architecture.md`.
- The behavioural-context join layer [@ford1989; @foote2008; @filatova2015; @riesch2008; @yurk2002] is a **statistical association**, not a deterministic mapping. The submission paper has to surface this honestly.
- The criterion-3 evidence [@bowers2018; @cure2026; @filatova2011] is **published playback data re-analysed**, not a new playback experiment. Whether the panel reads "predicts published playback responses" as satisfying "measurable response to broadcasted signals" remains the binding interpretive uncertainty for criterion 3 [@yovel2023doctor].
- Win probability for a solo external entrant on this prize is **~1&ndash;3%** (see `../PLAN.md` "Honest assessment"). This is a moonshot, not a near-certainty.

---

## Where to look next

1. Open `EXECUTION_PLAN.md`. Read the locked-decisions table.
2. Open `docs/ai_architecture.md`. Verify the four-head stack matches what you intend to build.
3. Open `docs/dataset_plan.md`. Work through the Week 1 checkboxes (data pull + encoder install + library-access pulls + the email to the prize coordinator).

---

<sub>Author: Danielle Lesin. Affiliation on submission: Georgia Institute of Technology, College of Computing (OMS-CS, AI specialization). Repository visibility: private. Not for redistribution.</sub>

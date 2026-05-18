<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Coller-Dolittle criteria &mdash; what the locked plan demonstrates

> **Status.** **Updated 2026-05-18 (rev 3) to reflect the locked plan.** Every criterion now has a *mechanism* (what the submission will demonstrate), a *source* (the BibTeX key set that backs it), and an *honest gap* (what the panel may still attack). The seven explicit prize criteria are drawn from the [official site](https://coller-dolittle-24.sites.tau.ac.il/) and refined by [@yovel2023doctor].

| # | Criterion | What the submission demonstrates | Source | Honest gap |
|:---|:---|:---|:---|:---|
| 1 | Non-invasive | All listening is via the DCLDE 2026 passive-hydrophone arrays; every cited playback paper used non-invasive DTAG suction-cup tags or boat-mounted projectors. No animal handling, no surgery, no restraint. | [@palmer2025dclde; @bowers2018; @cure2026] | None binding. |
| 2 | Multiple contexts | Embedding-space heads H1 (linear probes) and H2 (unsupervised clusters) discriminate (a) ecotype, (b) vocal category, (c) joined behavioural-context labels (foraging / traveling / resting / socializing). Strict reading uses joined call-type-to-context labels; lenient reading uses ecotype + vocal-category alone. | [@palmer2025dclde; @ford1989; @foote2008; @filatova2015; @yurk2002; @riesch2008] | The behavioural-context join is statistical, not deterministic. Reported at the distribution level, not per-call. |
| 3 | Endogenous signals | Every stimulus in the criterion-3 layer is a real recorded orca call from the published corpus; no synthesised calls are broadcast. | [@bowers2018; @cure2026; @filatova2011; @palmer2025dclde] | None binding. |
| 4 | Measurable response, preferably interactive and autonomous | Head H4 regresses embedding distance + cluster identity on per-trial response statistics extracted from the published killer-whale playback corpus. Not a *new* playback experiment, an *off-policy re-analysis*. | [@bowers2018; @cure2026; @filatova2011] | Whether the panel reads "predicts published responses" as satisfying "measurable response to broadcasted signals" remains the binding interpretive uncertainty. Ask the coordinator in Week 1. The "interactive and autonomous" clause is *not* claimed; the submission is honest about this. |
| 5 | Recent work already performed | Preprint posted to bioRxiv before submission; GitHub repo tagged; Zenodo data DOI minted. | This repo + bioRxiv + [@zenodo] | None binding once Stages 4&ndash;5 complete. |
| 6 | Five-page paper + two-minute video | `paper/manuscript.pdf` + 2-min MP4 produced per `RUBRIC.html` &sect;6. Both pitched at the [@kershenbaum2024whyanimalstalk] audience for the video, the [@yovel2023doctor] audience for the paper. | This repo | Both deliverables are still TBD as of 2026-05-18. |
| 7 | Public data | DCLDE 2026 [@palmer2025dclde_data] is US Government public domain. All derived analysis artefacts (join table, embeddings index, code) released on Zenodo + GitHub under MIT. | [@palmer2025dclde_data; @zenodo] | None binding. |

## The Yovel-Rechavi three obstacles &mdash; addressed in the locked plan

[@yovel2023doctor] names three obstacles between AI and interspecies communication. Treat these as design constraints, not boxes already ticked.

- **Umwelt.** The submission methodology section is explicit that the foundation-model embedding [@robinson2024naturelm] is not an animal's perceptual world. The discussion section names the discrepancy rather than papering over it.
- **Evaluation.** The response taxonomy (reply / approach / avoid / no response) is the four-class scheme used across the published playback literature [@bowers2018; @cure2026; @filatova2011], not a private invention. Every per-trial extraction is footnoted with the exact mapping back to the source paper.
- **Spurious correlations.** Every reported effect (H1, H2, H3, H4) is validated against a shuffled-permutation baseline (n_perm = 10,000). The Wittgenstein-boundary framing [@wittgenstein1953] is preserved: we do not claim "meaning"; we claim cluster-context association and quantitative response prediction.

## What this document is *not*

- It is not evidence that the criteria are *currently* satisfied; analysis has not begun.
- It is not a substitute for the per-head plan in `ai_architecture.md` or the operational plan in `dataset_plan.md`.
- It is not a guarantee that the panel will read the lenient interpretations of criterion 2 and criterion 4 the way we hope. Honest reading: lenient interpretation is ~70&ndash;90% likely to be accepted, strict interpretation is ~30&ndash;70% likely to be accepted, depending on which panel-member's reading dominates the discussion.

A defensible submission can be one that focuses on a subset of criteria deeply and is honest about the remaining gap. The 2025 winner [@sayigh2025nsw] did exactly that &mdash; they did not close a Doctor Dolittle loop; they showed one well-defined finding about dolphin whistles.

## Cross-references

- `ai_architecture.md` &mdash; per-head model spec and per-criterion claim paragraph.
- `dataset_plan.md` &mdash; dataset selection, week-by-week plan, risk tree.
- `playback_corpus.md` &mdash; per-paper extraction notes for criterion 4 (head H4).
- `paper/refs.bib` &mdash; bibliography source of truth.
- `.cursor/rules/citations.mdc` &mdash; folder-wide citation rule.

# Coller-Dolittle criteria — what a real submission would need

> **Status.** A checklist of what *would have to be true* for a submission to be defensible against each prize criterion, not a claim that any of them have been satisfied. Almost every row currently reads "not yet". That is honest.

The seven explicit prize criteria, drawn from the [official site](https://coller-dolittle-24.sites.tau.ac.il/) and refined by Yovel & Rechavi (2023) in [*Current Biology*](https://doi.org/10.1016/j.cub.2023.06.071).

| # | Criterion | What a real submission would need | Current state |
|:---|:---|:---|:---|
| 1 | Non-invasive | Show that all listening is via passive hydrophones, and that any proposed broadcast hardware is within the SPL range routinely used in the published playback literature, with explicit references. | Easy to satisfy in principle, but no submission text exists yet that makes the case. |
| 2 | Multiple contexts | Show measurable variation across **more than one** behavioural context. For orcas this would mean at least foraging / travel / socialising / alarm. | Context labels exist in the published ethology literature, but they have not been operationalised against any audio I have processed. |
| 3 | Endogenous signals | Show that any synthesised or broadcast stimulus falls inside the species' natural repertoire. | Not applicable yet — nothing has been synthesised. |
| 4 | Measurable response, preferably interactive and autonomous | Demonstrate response to a broadcast stimulus, with measurable behavioural or vocal categories. The "preferably interactive and autonomous" clause is what Yovel-Rechavi explicitly highlight as ideal. | Not applicable yet — no playback has been run. Off-policy re-analysis of the published playback literature is on the candidate-question shortlist and would partially address this criterion *for the paper*, not for a live demonstration. |
| 5 | Recent work already performed | The submission must describe completed work, not a proposal. | **Not yet true.** No analysis has been completed. The honest state is "in planning". |
| 6 | Five-page paper + two-minute video | A submission-ready PDF and a submission-ready MP4. | Neither exists. `paper/manuscript.md` is a structural outline; there is no video. |
| 7 | Public data | Every dataset cited and every reference auditable. | Achievable, and the candidate datasets in `docs/data.md` are public. But no audited list of "what we actually used" exists yet, because nothing has been used. |

## The Yovel-Rechavi three obstacles — addressed honestly

[Yovel & Rechavi (2023)](https://doi.org/10.1016/j.cub.2023.06.071) name three obstacles between AI and interspecies communication. Treat these as design constraints for the eventual paper, not as boxes already ticked.

- **Umwelt.** The eventual submission has to be explicit about *what* it assumes the listener can perceive. A foundation-model embedding is not an animal's perceptual world; the difference has to be discussed, not hidden.
- **Evaluation.** The submission has to define a response taxonomy that is interpretable to ethologists, not a private one. The four-class scheme (reply / approach / avoid / no response) used across the published playback literature is the natural starting point.
- **Spurious correlations.** Any positive finding in the paper has to be tested against at least one counterfactual control (e.g., shuffled-frame or dialect-matched scrambled stimuli). Without that, the finding will be attacked on Birch-style grounds and rightly so.

## What this document is *not*

- It is not evidence that the submission satisfies the criteria.
- It is not a manuscript section.
- It is not a guarantee that the chosen question will end up addressing all seven criteria; some criteria (3, 4) may be addressable only at the level of *what the methodology supports*, not at the level of *what is demonstrated in this submission*.

That last point matters: a defensible submission can be one that focuses on a subset of criteria deeply (e.g., 1, 2, 5, 6, 7) and is honest about not addressing the others in this iteration. The 2025 winners did exactly that — they did not close a Doctor Dolittle loop; they showed one well-defined finding about dolphin whistles.

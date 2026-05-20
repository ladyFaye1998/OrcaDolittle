<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Coller-Dolittle Prize coordinator &mdash; Week 1 email draft

> **Status.** Draft. Send during Stage 1 / Week 1 per `EXECUTION_PLAN.md`. Single-author repository, sole sender: Danielle Lesin. Recipient: `CollerDolittleAward@gmail.com` (the address listed on the [official prize site](https://coller-dolittle-24.sites.tau.ac.il/)).
>
> **Why this email matters more than its length suggests.** Two questions cannot be answered from the public prize page: (1) the 2026-27 cycle submission deadline, and (2) the panel's working interpretation of criterion 4's "measurable response, preferably interactive and autonomous" clause [@yovel2023doctor] as it applies to *re-analysis* of published playback data versus *new* playback experiments. Both questions bind the architecture of `docs/ai_architecture.md` (head H4) and the schedule of `docs/dataset_plan.md` (Stages 4&ndash;5). Ask both now, in one email, politely and concretely. Do not wait until Stage 3.

---

## What to send

**Subject:** Coller-Dolittle Prize 2026&ndash;27: cycle deadline + criterion-4 interpretation question

**Body:**

> Dear Coller-Dolittle Prize coordinators,
>
> I am preparing a single-author submission for the 2026&ndash;27 Coller-Dolittle Prize cycle on killer whales (*Orcinus orca*), built on the recently released DCLDE 2026 open corpus and the published killer-whale playback literature. Before I commit to my analysis schedule, I would be grateful for clarification on two points that I could not resolve from the prize website.
>
> 1. **Cycle deadline.** Could you confirm the submission deadline for the 2026&ndash;27 cycle, and the format of the three deliverables (the 5-page paper, the 2-minute video, and the public-data link)? I want to make sure the format requirements have not changed since the 2025&ndash;26 cycle.
>
> 2. **Criterion-4 interpretation.** Criterion 4 asks for a "measurable response of the organism to broadcast signals, preferably interactive and autonomous." My planned methodology addresses this by *re-analysing* the published killer-whale playback corpus (Bowers et al. 2018; Cur&eacute; et al. 2026; Filatova et al. 2011) and showing that embedding-derived distance and cluster identity predict the per-trial response statistics those studies reported. The "preferably interactive and autonomous" clause is not satisfied by this design, and the analysis introduces no new field broadcasts. Before I commit to this design, could you indicate whether the panel will accept a re-analysis-only criterion-4 submission, or whether new playback experimentation is *de facto* required? Either answer is useful to me; I am asking so that I can plan honestly rather than after the fact.
>
> I am happy to provide more detail on either point if it would help. Thank you for your time.
>
> Best regards,
> Danielle Lesin
> Georgia Institute of Technology, College of Computing (OMS-CS, AI specialization)
> [contact email]

---

## Drafting notes

- **Length.** Under 300 words. Coordinators triage administrative email; long messages get deprioritised.
- **Tone.** Polite, specific, scheduled. No name-dropping of panel members. No appeal to special circumstance. No mention of win probability, prize money, or competitive landscape.
- **What this email does *not* do.** It does not pitch the methodology, ask for guidance on encoder choice, ask whether DCLDE counts as a public corpus (it does &mdash; US Government public domain [@palmer2025dclde_data]), or request introductions to anyone. Each of those would dilute the two binding questions.
- **What to do with the response.** Log it in the `## Decision log` of `docs/dataset_plan.md` with the date received and a one-line summary. If the criterion-4 answer is "re-analysis is acceptable," head H4 stays as specified in `docs/ai_architecture.md`. If the answer is "new playback required," head H4 collapses and Risk B of `docs/dataset_plan.md` triggers immediately, well before Stage 3 commits any compute.
- **If no reply within 14 days.** Send one polite follow-up referencing the original date. After that, treat silence as "no commitment either way" and proceed with the lenient-interpretation reading documented in `docs/prize_criteria_mapping.md`, with the criterion-4 ambiguity surfaced explicitly in the manuscript's Discussion section (&sect;4).

---

## Cross-references

- `EXECUTION_PLAN.md` &mdash; Stage 1 / Week 1 checklist item: "Email `CollerDolittleAward@gmail.com` for the 2026-27 cycle deadline."
- `docs/dataset_plan.md` &mdash; Week 1 operational plan; Risk E (deadline) and Risk B (per-trial playback statistics) both connect here.
- `docs/prize_criteria_mapping.md` &mdash; criterion-4 row, "honest gap" column: the binding interpretive uncertainty this email is designed to resolve.
- `paper/refs.bib` &mdash; bibliography source of truth for the published playback corpus cited above.

<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Proposal: pivot the submission headline to head H3 (orca sequence LM)

> **Status.** **Proposal, not a locked decision.** Drafted 2026-05-20. Does not supersede `docs/ai_architecture.md` until adopted via a `## Decision log` entry in `EXECUTION_PLAN.md`. The current locked plan keeps four co-equal heads. This document argues for one of them being elevated to *the* headline and the others demoted to supporting evidence, and lays out what would have to be true for that pivot to make sense. Accept, reject, or modify.

---

## One-sentence proposal

**Promote head H3 &mdash; the per-encounter Transformer MLM over killer-whale call-ID sequences &mdash; from one of four co-equal heads to the single headline claim of the submission paper and video, and demote H1 / H2 / H4 to supporting evidence in the same paper.**

The four-head architecture itself stays exactly as specified in `docs/ai_architecture.md`. Only the *framing* changes &mdash; what the abstract leads with, what Figure 1 shows, what the 2-minute video [@kershenbaum2024whyanimalstalk] is built around, and what the panel is asked to evaluate first.

---

## Why this proposal exists

The current `docs/prize_criteria_mapping.md` framing optimises for **passing a four-criterion checklist**. That is the right framing if the goal is "do not be rejected." It is not the right framing if the goal is "win against institutional teams."

The 2025 winner [@sayigh2025nsw] won with *one* well-defined empirical finding about dolphin non-signature whistles, defended hard, backed by primary data. The pattern that wins this prize, on the evidence to date, is one sharp result, not four lukewarm ones. The four-head stack as currently framed produces four lukewarm results &mdash; each individually defensible, none individually memorable.

Of the four heads, H3 is the only one with a serious chance of being a sharp result:

| Head | Headline-claim ceiling | Bottleneck |
|---|---|---|
| H1 (probes) | "Frozen embeddings linearly separate ecotype, vocal category, and joined context" | Methodologically standard; not novel. Reads as a sanity check, not a discovery. |
| H2 (clusters) | "UMAP + HDBSCAN on frozen embeddings recovers literature call-type catalogue" | Sainburg-style repertoire discovery [@sainburg2020] is a well-trodden pattern; recovering a known catalogue is confirmatory, not novel. |
| **H3 (sequence LM)** | **"Per-encounter call streams in killer whale exhibit Transformer-detectable co-occurrence structure analogous to the combinatorial structure reported for sperm whale [@sharma2024]"** | **Novel-for-orca. First Transformer LM over orca call sequences. Falsifiable against a shuffled-sequence baseline. Effect size is recoverable from MLM loss alone.** |
| H4 (playback predictor) | "Embedding distance predicts published playback responses" | Bottlenecked by per-trial-table recoverability from [@bowers2018; @cure2026; @filatova2011] (Risk B); also lives entirely in re-analysis territory, which is the part of criterion 4 the panel may discount. |

H3 is the only one of the four that, if it lands, produces a sentence the panel will remember a week later: *"Killer-whale call sequences have detectable combinatorial structure, recovered with a 30M-parameter Transformer over per-encounter call-ID streams, mirroring the result reported for sperm whale by Sharma et al. (2024) [@sharma2024]."*

---

## What would change under this proposal

### What stays the same

- The four-head architecture in `docs/ai_architecture.md`. All four heads still get built. All four still appear in the paper.
- The frozen-encoder choice (NatureLM-audio + AVES2) [@robinson2024naturelm; @hagiwara2023aves].
- The permutation-test discipline (n_perm = 10,000) for every reported effect.
- The dataset substrate (DCLDE 2026) [@palmer2025dclde; @palmer2025dclde_data].
- The behavioural-context join layer [@ford1989; @foote2008; @filatova2015; @yurk2002; @riesch2008].
- The Wittgenstein boundary &mdash; no "meaning" claim [@wittgenstein1953; @yovel2023doctor].
- The entire risk tree in `docs/dataset_plan.md`.
- Stages 1, 2, 4, 5, 6 of `EXECUTION_PLAN.md`.

### What changes

| Surface | Before (current locked plan) | After (this proposal) |
|---|---|---|
| Paper working title | "Frozen audio foundation models recover behavioural-context structure and predict playback responses in killer whales" | "Combinatorial structure in killer-whale call sequences: a Transformer language-model probe of the DCLDE 2026 corpus" |
| Paper abstract leads with | Four-head stack overview, one sentence per head | One sentence on H3 finding + effect size; H1 / H2 / H4 mentioned in single supporting sentence |
| Figure 1 | UMAP of embeddings coloured by behavioural context (H1 / H2 result) | H3 result: MLM loss vs. shuffled-sequence baseline across the three ecotypes, with permutation null distribution |
| Stage 3 (`EXECUTION_PLAN.md`) priority order | H1 &rarr; H2 &rarr; H3 &rarr; H4 (current order in the plan) | **H3 first**, then H1 / H2 in parallel as supporting figures, then H4 last (and only if Risk B does not trigger) |
| Video [@kershenbaum2024whyanimalstalk] beat 3 (the "result" beat) | UMAP figure + playback-prediction result | H3 result animated: scrambled vs. real call-sequence MLM loss, one ecotype at a time |
| `docs/prize_criteria_mapping.md` criterion 2 row | Multi-context claim from H1 + H2 | Multi-context claim from H1 + H2 *and* sequence-structure claim from H3 *as a strengthened criterion-2 satisfier* |
| `docs/prize_criteria_mapping.md` criterion 4 row | H4 as primary satisfier | H4 still presented; honest gap on the "preferably interactive and autonomous" clause [@yovel2023doctor] surfaced more aggressively in the manuscript Discussion |

### What this proposal does NOT do

- It does not delete any head. All four still get built and reported.
- It does not change the locked dataset, encoder, or statistical-validation regime.
- It does not promise that H3 will succeed. If H3's MLM loss is not significantly below the shuffled-sequence baseline (n_perm = 10,000), this proposal *self-falsifies* and the four-head co-equal framing is the correct fallback.
- It does not change the submission deliverables (5-page PDF + 2-min video + public-data link).

---

## Why this raises win probability

Stated honestly (see conversation context that triggered this proposal):

- **Four-head framing baseline.** ~1&ndash;3% win probability for a solo external entrant. The `README.md` "Honest assessment" already states this.
- **One-sharp-claim framing (this proposal).** ~5&ndash;10% conditional on H3 producing a clean above-baseline effect. The probability of H3 producing such an effect, conditional on the methodology in `docs/ai_architecture.md` and the precedent in [@sharma2024; @sainburg2019animal], is moderate-to-high &mdash; killer whales have larger, more clearly structured per-encounter call streams than sperm whale (which already worked), and the DCLDE 2026 corpus is larger than the sperm-whale corpus [@sharma2024] used.

Multiplying: unconditional win probability under this proposal is in the **3&ndash;8% range**, compared to the baseline 1&ndash;3%. Roughly 2&ndash;3&times; the baseline.

This is still a long-odds prize. The proposal does not turn it into a near-certainty. It moves it from "lottery ticket" to "competitive grant with low base rate," which is a different category of effort-to-expected-value ratio.

---

## What would have to be true for the pivot to be wrong

The proposal is wrong if any of the following:

1. **H3 fails its sanity check at the pilot stage.** Specifically: if a small-scale H3 pilot &mdash; one ecotype, 6-layer Transformer MLM on per-encounter call-ID sequences, n_perm = 1,000 &mdash; does not produce an MLM loss below the shuffled-sequence baseline at p &lt; 0.05, the H3-headline framing is empirically not supported and the four-head co-equal framing is the correct fallback.
2. **The coordinator confirms that the panel weights criterion-4 "interactive and autonomous" strictly.** If the answer to the criterion-4 question in `paper/coordinator_email_draft.md` is "we require a new playback experiment," then *no* re-analysis-based head wins the prize, and the framing question is moot &mdash; the question becomes whether to attempt the submission at all (see `README.md` "Honest assessment").
3. **A competing paper publishes orca sequence-LM results mid-cycle.** Risk D in `docs/dataset_plan.md`. If [@sharma2024]-equivalent published on killer whale appears on bioRxiv between now and Stage 4, the H3 novelty argument collapses and the four-head framing's "we did four things, none individually novel but all defensible" position becomes a better hedge.

The first of these is the cheap, fast check. **Run an H3 pilot in Stage 3, scoped explicitly to test this proposal, before committing the paper draft to the H3-headline framing.** That keeps the option value of either framing alive until Stage 3 produces evidence.

---

## Concrete decision the author needs to make

Pick one of three:

- **A. Adopt this proposal.** Add a `## Decision log` entry to `EXECUTION_PLAN.md` (or `docs/ai_architecture.md`) titled "2026-MM-DD: pivot manuscript headline to H3 pending pilot result." Reorder Stage 3 in `EXECUTION_PLAN.md` so H3 runs first. Update `paper/manuscript.md` working title. Keep H1 / H2 / H4 in the paper as supporting evidence.
- **B. Reject this proposal.** Leave the four-head co-equal framing in `docs/ai_architecture.md` and the manuscript outline unchanged. Add a `## Decision log` entry that records the rejection and the reason (e.g. "four-head checklist framing is the right hedge given solo-author risk tolerance").
- **C. Defer.** Run the H3 pilot in Stage 3 (Week 5 of `EXECUTION_PLAN.md`) without committing to either framing. Re-open this proposal once the pilot result is in.

Recommended default: **C.** It costs ~one week of compute and writing, falsifies cheaply, and preserves the option to take either path.

---

## Cross-references

- `docs/ai_architecture.md` &mdash; locked four-head stack; H3 specification (6 layers, 8 heads, d_model 512, MLM with 15% masking, max sequence length 256 per encounter) is the implementation this proposal would headline.
- `docs/dataset_plan.md` &mdash; risk tree; Risks B, D, and E all interact with this proposal as documented above.
- `docs/prize_criteria_mapping.md` &mdash; rows for criteria 2 and 4 would be edited under option A.
- `EXECUTION_PLAN.md` &mdash; Stage 3 order would be edited under option A.
- `paper/manuscript.md` &mdash; working title and abstract priority order would be edited under option A.
- `paper/video_script.md` &mdash; beat 3 ("the result") would be edited under option A.
- `paper/coordinator_email_draft.md` &mdash; the criterion-4 question this email asks is also a precondition for evaluating this proposal.
- `paper/refs.bib` &mdash; [@sharma2024; @paradise2025wham; @vaswani2017attention; @devlin2019bert; @sainburg2019animal] are the citation set this proposal leans on.

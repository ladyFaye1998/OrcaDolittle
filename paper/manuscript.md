<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Manuscript outline &mdash; locked structure, placeholder content

> **Status.** Structural outline aligned with the locked plan as of 2026-05-18 (rev 3). No claims are evidenced yet. All numeric placeholders are explicitly marked `[TBD]`. Drafting begins when Stage 3 of `EXECUTION_PLAN.md` has produced real numbers for heads H1&ndash;H4 (see `docs/ai_architecture.md`).

---

## Working title (one of)

- "Frozen audio foundation models recover behavioural-context structure and predict playback responses in killer whales (*Orcinus orca*)."
- "Acoustic embeddings for killer whales: ecotype, behavioural context, sequence structure, and playback-response prediction from open data."

Final choice in Stage 4.

## Authors

Danielle Lesin (sole author, affiliation: Georgia Institute of Technology, College of Computing).

## Abstract (one paragraph, written last)

To be written last. One paragraph. Will state, in order: substrate ([@palmer2025dclde]), encoder ([@robinson2024naturelm; @hagiwara2023aves]), the four heads, the criterion mapping ([@yovel2023doctor]), and the headline number for each head.

`[TBD]`

## 1. Background (&asymp; &frac34; page)

- One paragraph: Coller-Dolittle / Yovel-Rechavi framework [@yovel2023doctor], including the three obstacles and the Wittgenstein boundary [@wittgenstein1953].
- One paragraph: killer-whale dialect and call-type research [@ford1989; @foote2008; @filatova2015; @riesch2008; @yurk2002] and the published playback corpus [@bowers2018; @cure2026; @filatova2011].
- One paragraph: bioacoustic foundation models [@robinson2024naturelm; @hagiwara2023aves; @hamer2025perch]; closest cetacean precedent is sperm-whale combinatorial structure [@sharma2024].
- One sentence: the scientific question of this paper.

## 2. Method (&asymp; 1 page)

- Dataset: DCLDE 2026 [@palmer2025dclde; @palmer2025dclde_data]. One-paragraph description.
- Encoder: NatureLM-audio [@robinson2024naturelm] primary, AVES2 [@hagiwara2023aves; @chen2022beats] comparator, frozen.
- Four heads (H1&ndash;H4) per `docs/ai_architecture.md`, in plain language. No more than one paragraph per head.
- Counterfactual / control analyses: shuffled-permutation baselines (n_perm = 10,000) for every reported effect.
- Honesty footnote on what was *not* tried and why (no foundation-model pretraining, no fine-tuning unless the encoder fails; no new field playbacks).

## 3. Results (&asymp; 1&frac34; pages, dominated by figures)

- **Figure 1.** Headline figure: UMAP of NatureLM-audio embeddings of DCLDE 2026 calls, coloured by joined behavioural context; with marginal histograms and significance vs. permutation baseline. `[TBD]`
- **Figure 2.** H4 result: scatter of embedding distance vs. per-trial response amplitude across [@bowers2018; @cure2026; @filatova2011], with regression line and shuffled-baseline cloud. `[TBD]`
- **Table 1.** Headline numbers for H1&ndash;H4 with confidence intervals and permutation p-values. `[TBD]`
- Two or three sentences of prose per figure / table.

## 4. Discussion (&asymp; &frac34; page)

- What the result implies for interspecies communication research, in modest terms.
- What it does *not* imply. Paragraph written first. The Wittgenstein boundary [@wittgenstein1953] held explicit.
- One paragraph mapping the four heads to the four Coller-Dolittle criteria [@yovel2023doctor] per `docs/prize_criteria_mapping.md`.

## 5. Limitations (&asymp; &frac12; page, first-class)

The five honest limits already named in `docs/ai_architecture.md`:

1. Frozen encoder may have seen DCLDE-adjacent audio [@robinson2024naturelm; @hagiwara2023aves]. Mitigated by AVES2 comparator + provider-folder hold-out.
2. Behavioural-context join is statistical, not deterministic [@ford1989; @foote2008].
3. Per-trial playback statistics may be incomplete [@bowers2018; @cure2026; @filatova2011].
4. Sequence-LM head is methodologically novel for orca but not for cetaceans [@sharma2024; @paradise2025wham].
5. The Wittgenstein boundary [@wittgenstein1953] remains uncrossed; no "meaning" claim.

## 6. Conclusion (&asymp; 2 sentences)

One sentence of finding. One sentence of next step.

---

## Reminders to self while drafting

1. Strip every "we demonstrate" on the first pass.
2. Strip every "novel" on the second pass.
3. Replace adjectives with numbers wherever possible.
4. Cite primary papers, not blog posts. Every fact gets `[@bibkey]` per `.cursor/rules/citations.mdc`.
5. The Limitations section is part of the paper, not an apology at the end.
6. The video script in `video_script.md` must say the same thing this paper says, not a sexier version.

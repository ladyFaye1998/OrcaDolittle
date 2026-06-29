# A Testable Program for "Decoding" Killer Whale Communication

This document defines what a rigorous, criterion-based claim about killer-whale
communication would require, maps the current pipeline onto that ladder, and
records the verified ceiling of publicly downloadable data. It is the planning
reference for deciding what is worth building next and what must wait for a
field collaborator.

## 1. What "decoding" has to mean to be testable

In the animal-communication literature a signal is treated as *functionally
referential* only with two independent criteria
[@deecke2005; @kershenbaum2024whyanimalstalk]:

1. **Production criterion** - the signal is produced reliably and narrowly in a
   specific external context (context-specificity), not diffusely across all
   behaviours.
2. **Perception criterion** - receivers respond to the signal *alone*, in the
   absence of the original context, as if to the event it denotes. This is
   normally established with controlled playback [@deecke2005].

A broader, "language-like" claim adds a third element:

3. **Combinatorial / compositional structure** - discrete units combine under
   rules so that combinations carry meaning beyond their parts. This is the
   property recently argued for in non-human systems: sperm whale codas
   [@sharma2024], bonobo calls [@berthet2025bonobo], and wild chimpanzee
   vocalisations [@crockford2025].

Consequence: the analysis of our own archival corpora can address the
**production** prerequisites and **combinatorial structure**, but the **perception**
criterion needs an experiment in which a signal is broadcast and the receiver's
response is measured. We do not run new field playbacks. We do, however, address the
perception criterion by **re-analysis of an already-published conspecific playback
experiment** on wild killer whales [@filatova2011playback] (Section 5g): the
behavioural experiment is prior work, and our contribution is the reproducible
statistic plus an embedding model of the associated dialect space. A
full "we decoded orca language" claim in the two-way semantic sense would still
require demonstrating that the *content* of a call (not just its dialect membership)
governs the receiver's response; that remains future work. Everything below is
organised around that boundary.

## 2. The evidence ladder

| Rung | Claim it licenses | Criterion | Status / blocker |
|---|---|---|---|
| 0 | Killer-whale acoustic categories (ecotype) are recoverable from learned embeddings, controlling for recording site | none (structure only) | **Done** - H1/H4, site-controlled [@palmer2025dclde; @hagiwara2023aves] |
| 1 | A discrete, stereotyped **call-type repertoire** exists and is recoverable, site-independently | production (units) | **Done (positive), both resident populations** - Section 5d: within-site SRKW 14-type 0.709 and NRKW 18-type 0.968, plus cross-site transfer [@ford1989; @filatova2015; @wellard2020] |
| 2 | Calls are **non-randomly tied to behavioural context** | production (context-specificity) | **Met (production side), multi-context + call-type-specific** - DTAG H5: communicative calls decode movement-defined context with the individual held out (foraging/non-foraging 0.770; three-way foraging/travelling/resting 0.577, chance 0.333), and **specific call types occur in specific contexts** (call-type × context Cramér's V = 0.40, within-individual null p < 0.001); rate/loudness/echolocation controls rule out the trivial explanations (Section 5f). Remaining: the perception side (Rung 3) and contexts beyond movement state (e.g. alarm/mating) [@holt2024masking_data; @tennessen2019; @wilson2006; @ford1989; @foote2008] |
| 3 | Receivers **respond** to a broadcast conspecific call, selectively by dialect | perception | **Met by re-analysis (Section 5g)** - wild killer whales reply vocally to same-pod playbacks and stay silent to different-pod playbacks (6/6 vs 0/6 after pseudoreplication control, Fisher p = 0.002), naive free-ranging animals, often matching the played type [@filatova2011playback; @miller2004repertoires]; frozen AVES2 recovers the dialect call-type space underlying the response contrast (purity 0.439 vs 0.05 null, p = 1e-3); corroborated across independent broadcast-response datasets [@selbmann2026aversive; @bowers2018]. The behavioural experiments are prior published work re-analysed here; the response tracks dialect, not content [@deecke2005] |
| 4 | Units show **non-random sequential structure**, and in SRKW **structure beyond first order** (combinatorial prerequisite) | sequential / combinatorial structure | **Done (positive), over validated units** - Section 5c (k-means tokens), 5e (catalogue call types, both populations, site-controlled), and 5i (**beyond first order in SRKW S-calls**, second-order info 0.645 bits, p ~= 1e-3 vs first-order Markov surrogates; null in NRKW) [@kershenbaum2024whyanimalstalk; @sharma2024; @berthet2025bonobo; @crockford2025] |

We are credibly at Rung 0, at Rung 1 for both resident populations (validated
catalogue types recovered with a site control *and* cross-site transfer, SRKW and
NRKW; Section 5d), at Rung 2 on the **production side** (an identity-controlled,
multi-context, call-type-specific behavioural-context association from DTAG records,
Section 5f - the perception side of Rung 2 still needs playback), and at the
sequential-structure foot of Rung 4.
Rung 3 (perception/response) is **met by re-analysis** of a published conspecific
playback experiment (Section 5g) and corroborated across independent broadcast-
response datasets: receivers respond selectively to a broadcast endogenous signal.
What is *not* established is that the receiver's response is governed by the call's
*content* rather than its dialect membership - the gate to a full "decoded meaning"
claim - which remains future work.

## 3. Verdicts on the three proposed shortcuts

**"Orcas are dolphins - reuse a prior dolphin/whale study's data."**
Taxonomically correct: killer whales are Delphinidae. But the transferable
asset is the **method, not the corpus**. The contextual/combinatorial analysis
of sperm-whale codas [@sharma2024] ports directly to orca call sequences (it is
essentially what H3 already prototypes); the *recordings* are a different
species and cannot be relabelled as orca without committing exactly the kind of
provenance error the reviewers are equipped to catch. **Port the analysis,
not the data.**

**"Search orca videos and manually label them."**
This maps onto Rung 2 (context-specificity) and is legitimate **only as a
clearly-labelled pilot**. Hand-labelled web video carries unknown provenance,
uncalibrated and often non-synchronous audio, channel compression, and observer
bias. It cannot support a main claim. If used at all, it must be framed as
an exploratory, caveated pilot, and is strictly weaker than using corpora that
already pair audio with documented context. **Allowed as a pilot with explicit
caveats; never as main evidence.**

**"Decode orca language in a legit way."**
Achievable as a **bounded, criterion-named** claim: *we demonstrate the
production-side prerequisites of functional reference in killer whales - a
discrete call-type repertoire (Rung 1) and, in pilot form, context-specificity
(Rung 2) - together with above-chance combinatorial structure in call
sequences (Rung 4).* That is true, testable, and publishable. The unbounded
claim ("we translated orca / two-way communication") is not supportable without
Rung 3 and must not be made.

## 4. Verified public-data ceiling (probed, not assumed)

Checked live via `scripts/fetch_orcasound_labels.py` (anonymous S3) and the
Hugging Face Hub API:

- **Orcasound `acoustic-sandbox` bucket** [@orcasound]:
  - `labeled-data/classification/killer-whales/` is organised by **ecotype**
    (`southern-residents`, `northern-residents`, `biggs-transients`,
    `offshores`, `global-general`) as hour-long WAVs - same label granularity we
    already have.
  - `labeled-data/detection/train/` (Pod.Cast rounds) provides **call-presence**
    labels (`label = "SRKWs"`) with start/duration timestamps - useful for a
    detector, **not** call-type labels.
- **Hugging Face Hub**: no killer-whale call-type-labelled dataset exists.
- **Wellard et al. 2020 (Dryad)** [@wellard2020_data; @wellard2020]: a published
  **call-type catalogue** (acoustic repertoire) for Ross Sea Type C killer
  whales - catalogue call-type labels, downloadable. Scoped to one population.
- **DCLDE 2026 per-provider annotations** [@palmer2025dclde]: **the key finding.**
  The combined/published CSV standardises killer-whale labels to ecotype, but the
  original per-provider annotation files retain a populated `call_type` column
  (Ford/Filatova codes) plus `clan`/`subclan`/`pod`. Verified live with
  `scripts/survey_dclde_calltypes.py`: **10,139 call-type-labelled detections**
  across **256 codes** in three providers (`dfo_crp` 5,992; `vfpa` 3,017;
  `smru` 1,130). After normalisation and an N>=30 filter this is **43 usable
  call types over 7,748 detections** (`scripts/build_calltype_manifest.py`,
  manifest at `data/join_tables/call_type_manifest.csv`).

Conclusion (updated): call-*type* labels are no longer the blocker. We have a
real, catalogue-coded, multi-class call-type dataset on our own corpus, with two
clean designs that control for the recording-site confound:
(a) **within-provider** multi-type discrimination - `dfo_crp` carries 28 NRKW
N-call types and `vfpa` 21 SRKW S-call types under a single hydrophone; and
(b) **cross-provider call-type transfer** - SRKW S-calls (`S01`, `S04`, `S16`,
`S10`, ...) appear in both `vfpa` and `smru`, enabling train-on-one /
test-on-the-other, the exact control the ecotype result failed [@ford1989;
@filatova2015]. Of these labelled detections, **1,954 fall inside files already
encoded in the embedding artifact** and were joined onto AVES2 vectors by
(soundfile, onset) with no re-encoding (the local replication). The **full
catalogue (8,552 detections) has since been encoded** from the public DCLDE
audio via `notebooks/calltype_encode_colab.ipynb`, covering the `dfo_crp` NRKW
N-calls as well; both designs are executed for both resident populations in
Section 5d [@hagiwara2023aves].

## 5. Concrete next steps

1. **Rung 1 - call-type repertoire (primary, solo-achievable).** Acquire the
   Wellard Type C catalogue [@wellard2020_data] and/or run unsupervised
   call-type discovery (HDBSCAN on AVES2 embeddings of presence-labelled
   Pod.Cast segments [@mcinnes2017hdbscan; @hagiwara2023aves]), validating
   recovered clusters against published type catalogues [@ford1989; @filatova2015].
   Deliverable: a recovered repertoire with cluster-stability metrics.
2. **Rung 4 - combinatorial structure (solo-achievable).** **Done (Section 5e):**
   the sequence test now runs over the Rung-1 catalogue call types rather than
   coarse tokens and finds above-chance, rule-like ordering in both resident
   populations, mirroring the coda analysis of [@sharma2024].
3. **Rung 2 - behavioural context.** **Partly done (Section 5f):** the DTAG
   behavioural-context decode (H5) shows communicative calls predict the caller's
   movement-defined foraging state at 0.770 with the individual held out, using a
   context label independent of the decoded audio [@holt2024masking_data;
   @tennessen2019]. This is a behavioural-*state* association, not call-type-level
   event-specificity; closing the latter still needs provenance-controlled,
   audio-synchronised per-call context (field ethogram or finer DTAG behavioural
   coding). Any web-video labelling remains a caveated pilot only.
4. **Rung 3 - perception (collaboration-gated).** Draft the playback protocol
   and approach a field lab. This is the
   only route to a perception-criterion result and cannot be done from archives.

## 5b. Result: unsupervised discovery does not shortcut Rung 1 (tested)

Before assuming call-type labels are required, we tested whether a repertoire
falls out of the embeddings we already have. `scripts/run_calltype_discovery.py`
runs HDBSCAN [@mcinnes2017hdbscan] on AVES2 embeddings [@hagiwara2023aves]
within the SRKW ecotype, with a provider-purity guard:

- **Pooled across providers:** 16 candidate clusters, but the mean
  dominant-provider fraction was 0.93 and 82% of segments fell to noise - the
  clusters track recording site, not call type.
- **Single provider (site confound removed by design):** the solution collapses
  to one dominant cluster plus two tiny ones with 68% noise - no resolved
  multi-type repertoire.

Interpretation: unsupervised clustering of the current 1.7 s segment embeddings
does not recover a discrete stereotyped repertoire, and pooled "structure" is a
site artifact. **Rung 1 therefore requires ground-truth call-type
labels.** Those labels turned out to exist on our own corpus, in the DCLDE
per-provider annotation files (Section 4): the labelled-data path is now open,
not blocked. This negative result is what justified going to find them.

## 5c. Result: call streams carry non-random sequential structure (tested)

`scripts/run_sequence_structure.py` quantises the AVES2 embeddings into a
balanced 40-type k-means vocabulary, builds per-encounter sequences (grouped by
provider+soundfile, ordered by onset), and tests first-order dependence with a
within-encounter order-shuffle null. Because the shuffle keeps each encounter's
call *composition* fixed and only destroys order, recording-site and
SNR composition cannot inflate the result.

- Adjacent-call mutual information I(t; t+1) = **1.91 bits**, versus a shuffled
  null of **1.65 +/- 0.01 bits**, **p < 0.001** (1000 permutations).
- After removing repetition (self-transition rate 0.40), off-diagonal MI is
  still **1.09 bits** - structure is not merely call bouting.
- Out of sample, a bigram model beats a unigram by **1.74 bits/token** held out.

Interpretation: killer-whale call streams have statistically robust first-order
sequential structure beyond simple repetition - the production-side prerequisite
for combinatorial coding, in the spirit of the sperm-whale coda analysis
[@sharma2024]. This is **not** evidence of meaning or compositional semantics;
the tokens are unsupervised, not validated biological call types - a limitation
that Section 5e removes by re-running the same test on the catalogue call types.

Note that the masked-LM variant (H3) returns a null on the same data; the Markov
test is the appropriate, better-powered instrument for first-order structure on
~700 encounters, and both are reported.

## 5d. Result: validated call types are recoverable and transfer across sites (tested)

Two runs establish this. A local replication (`scripts/run_calltype_model.py`)
joins the catalogue `call_type` labels onto the existing AVES2 embeddings (by
soundfile + onset, 1,954 segments matched) and runs the SRKW S-call designs. The
authoritative run (`notebooks/calltype_encode_colab.ipynb`) encodes the **full
catalogue from the public DCLDE audio - 8,552 labelled detections** - so it
covers both resident populations, including the NRKW N-calls absent from the
local artifact [@ford1989; @filatova2015; @hagiwara2023aves]:

- **Within-provider, VFPA, 14 SRKW S-call types, n = 1,489.** Linear-probe
  balanced accuracy **0.709** (macro-F1 0.706; chance 0.071, majority 0.278; MLP
  0.706), 200-fold permutation null 0.072, **p ~= 0.005**. (The local join run
  reproduces this exactly.)
- **Within-provider, DFO_CRP, 18 NRKW N-call types, n = 5,009.** Linear-probe
  balanced accuracy **0.968** (macro-F1 0.966; chance 0.056, majority 0.390; MLP
  0.963), permutation **p ~= 0.005** - 18-way call-type
  discrimination within a fixed hydrophone.
- **Cross-provider transfer, train VFPA -> test SMRU, 5 shared SRKW S-call types
  (`S01`, `S04`, `S16`, `S10`, `S16/S17`), n_test = 267.** Balanced accuracy
  **0.636** (chance 0.200, macro-F1 0.607). The merged/ambiguous `S16/S17` label
  is the hardest of the five; on the four unambiguous shared types the transfer
  is **0.830**.

Interpretation: stereotyped killer-whale call types are recoverable from
self-supervised embeddings in **both** resident populations (SRKW and NRKW), and
- unlike the ecotype boundary, which collapsed to 0.529 across sites (H4) -
**call-type identity transfers across independent recording sites** (0.636 over
five types, 3.2x chance; 0.830 over the four unambiguous types). This supports
the interpretation that the embeddings carry a site-transferable acoustic category
corresponding to the expert catalogue, and it addresses the production-units leg
(Rung 1). It also explains the Section 5b
discovery failure: the categories are real but too fine to fall out of
unsupervised clustering of site-confounded embeddings - supervision with
catalogue labels is what resolves them. Residual within-site confusions are
between catalogue-adjacent types (`S16` / `S16/S17` / `S17`), as expected
biologically. This is call-type discrimination, **not** evidence of meaning or
function.

## 5e. Result: validated call types follow non-random syntax (tested)

Section 5c established sequential structure over an *unsupervised* k-means
vocabulary, which forced the caveat that the tokens are not validated biological
units. With the recovered catalogue labels we remove that caveat:
`scripts/run_calltype_sequence.py` runs the identical first-order test directly
on the **expert catalogue call types**, building per-recording sequences
(grouped by `audio_path`, ordered by onset) with provider held constant and a
within-recording order-shuffle null [@ford1989; @filatova2015; @kershenbaum2024whyanimalstalk]:

- **NRKW N-calls @ `dfo_crp`** (31 catalogue types, 5,273 calls, 142
  recordings, 5,057 adjacent pairs): adjacent-pair MI **2.85 bits** vs an
  order-shuffle null of **1.71 bits**, **p = 1e-3** (1000 permutations). Streams
  are strongly bouted (self-transition rate 0.92), yet **1.60 bits of transition
  structure remain after removing repetition**, and a held-out bigram beats a
  unigram by **2.73 bits/token**.
- **SRKW S-calls @ `vfpa`** (19 catalogue types, 1,553 calls, 28 recordings):
  adjacent-pair MI **1.29 bits** vs a null of **0.78 bits**, **p = 1e-3**;
  self-transition rate 0.52 (less bouted), off-diagonal MI **0.98 bits**, and a
  held-out bigram beats a unigram by **0.31 bits/token**.

Interpretation: the production-side prerequisite for combinatorial coding now
holds over *validated* units, not just quantised tokens, in both resident
populations and with site held constant, in the spirit of the sperm-whale coda
analysis [@sharma2024]. It remains **not** evidence of meaning or compositional
semantics - a compositionality test (does A+B mean more than A,B?) still requires
context labels (Rung 2) and perception (Rung 3). See
`reports/calltype_sequence_summary.json` and `figures/calltype_sequence.png`.

## 5f. Result: communicative calls predict behavioural context, individual held out (tested)

This is the positive, segment-level, **multi-context** result on Rung 2 (production side).
`scripts/dtag_local_extract.py`, `scripts/dtag_context_labels.py`,
`scripts/dtag_context_decode.py`, `scripts/dtag_context_multilabel.py`,
`scripts/dtag_context_multidecode.py`, `scripts/dtag_calltype_context.py`, and
`scripts/dtag_context_controls.py` re-analyse open animal-borne DTAG deployments on fish-eating
killer whales in the Salish Sea [@holt2024masking_data; @tennessen2019; @holt2024masking]. Tag
audio is losslessly decoded; communicative-call clips are cut by an energy detector in the
0.5-10 kHz pulsed-call band (impulsive clicks and >12 kHz echolocation rejected); and each dive
is labelled from the tag's *movement* channel only (calibrated 50 Hz depth and acceleration).
No acoustic variable enters any label, so context is independent of the call stream it is
decoded from.

- **Binary leave-individual-out decode** across 22 tagged whales (10,834 calls; 2,692
  foraging, 8,142 non-foraging): a linear probe on frozen AVES2 call embeddings predicts the
  movement-defined foraging/non-foraging context at **0.770 balanced accuracy**, against a
  label-permutation null of **0.499 +/- 0.007** (**p = 5e-3**).
- **Three-way decode (more than one context)**: resolving **foraging / travelling / resting**
  (travelling/resting split at each individual's median ODBA [@wilson2006]), the same
  leave-individual-out decode reaches **0.577** across the 20 whales carrying all three
  contexts (9,723 calls; chance 0.333; null 0.355 +/- 0.008, p = 5e-3), with per-context recall
  foraging 0.785, travelling 0.517, resting 0.429.
- **Call-type-level context-specificity**: clustering the calls into data-driven types gives a
  call-type × context table with **Cramér's V = 0.40** against a *within-individual* shuffle
  null of 0.08 (p < 0.001); every recovered type is over-represented in a particular context
  (one type ×2.3 in foraging, others ×1.5 in travelling and resting) - the production criterion
  that specific call types occur in specific contexts [@ford1989; @foote2008].
- **Controls** (binary contrast): call rate alone decodes at **0.536**, loudness alone at
  **0.577**, coarse acoustic scalars 0.723, and dropping the 25% most click-like clips leaves
  **0.749**; clips are 16 kHz, so echolocation peak energy is absent by construction.

Interpretation: because every test whale is unseen in training and the label never sees the
audio, the above-chance decode cannot be produced by recognising the individual, the tag, the
recording site, or the acoustic energy used to define the label - the communicative calls
themselves carry information about concurrent behaviour. The result now spans **more than one**
behavioural context, is **call-type-specific**, and is not explained by how often or how loudly
the whale calls or by biosonar. This addresses the **production side** of Rung 2 (context-specific
calling across multiple contexts) - the segment-level behavioural link the archival ecotype and
call-type analyses could not supply. It is **not** the perception side (no evidence that
receivers act on the calls differently by context) and **not** evidence of referential meaning;
the contexts are movement-defined states (not alarm/mating), and the call-type clusters are
soft, data-driven partitions, not catalogue types. See
`reports/context_decode_summary.json`, `reports/context_label_yield.json`,
`reports/context3_decode_summary.json`, `reports/context3_label_yield.json`,
`reports/calltype_context_selectivity.json`, `reports/context_controls_summary.json`, and
`figures/context_decode.png`, `figures/context3_decode.png`, `figures/calltype_context.png`,
`figures/context_controls.png`.

## 5g. Result: receivers respond selectively to broadcast conspecific calls (perception side, Rung 3)

This is the perception-side result the archival heads cannot supply. It is a
**re-analysis of an already-published conspecific playback experiment** on wild
killer whales [@filatova2011playback]: 2-min sequences of same-pod vs different-pod
discrete calls were broadcast to free-ranging Kamchatkan resident killer whales
(FEROP, Avacha Gulf, 2006-2008) and the per-trial response was scored. The
behavioural experiment is prior published work; our contribution is the reproducible
statistic (`scripts/run_playback_response_stats.py`, from the transcribed per-trial
table `data/join_tables/filatova2011_playback_trials.csv`) and an embedding model of
the associated signal space (`scripts/run_playback_response.py`).

- **Selective behavioural response (the perception criterion).** Whales replied
  vocally to **every** same-pod playback and to **none** of the different-pod
  playbacks: 8/8 vs 0/6 across all trials, and **6/6 vs 0/6 after pseudoreplication
  control** (Fisher exact two-sided **p = 0.002**) [@filatova2011playback]. When they
  replied they often **matched the played call type**, the natural-exchange behaviour
  documented in [@miller2004repertoires]. The animals were free-ranging and silent
  for >=30 min before each trial, so the response is to a first-exposure broadcast,
  **not** an associatively conditioned cue (the no-learning sub-criterion).
- **The encoder represents the associated dialect space.** Encoding the public
  FEROP call catalogue [@russianorca_catalogue] with the same frozen AVES2 model
  [@hagiwara2023aves], leave-one-out 1-NN call-type purity is **0.439** across 19
  Kamchatka call types (57 exemplars), against a label-shuffle null of **0.050 +/-
  0.033** (**p = 1e-3**; proportional-chance 0.067). The embeddings recover the
  dialect call types - the prerequisite for a dialect-distance response model.
- **Corroboration across independent broadcast-response datasets.** The response
  criterion does not rest on one study. An independent open dataset shows killer
  whales respond to a broadcast stimulus against matched noise/upsweep controls
  (avoidance, Stimulus p = 0.02) [@selbmann2026aversive]; a second shows that the
  *structure* of broadcast killer-whale calls drives selective heading changes in
  receivers [@bowers2018]; and natural vocal exchanges show receivers match the
  call type of a preceding caller above chance [@miller2004repertoires]. The
  cross-dataset roll-up is in `reports/broadcast_response_criterion.json`
  (`scripts/summarize_broadcast_response.py`, from
  `data/join_tables/broadcast_response_evidence.csv`).

Interpretation: wild killer whales produce a measurable, dialect-selective response
to a broadcast endogenous signal, with naive animals - the response/perception
criterion - and the frozen representation separates the exact call types that carry
the dialect membership the response tracks. This is **not** a claim of referential
meaning: the response is governed by *dialect membership* (same vs different pod),
not demonstrably by the call's *content*. The behavioural experiment was run by
others; the per-trial stimulus->response embedding model (does embedding
dialect-distance predict the response and the matched type?) needs the playback
session audio, which is request-only from FEROP (`docs/data_requests.md`). See
`reports/playback_response_summary.json`, `reports/playback_embedding_summary.json`,
`figures/playback_response.png`, and `figures/playback_embedding.png`.

## 5h. Result: catalogue call types specialize across foraging vs socializing (C2, catalogue level)

The DTAG head (5f) shows context-specific production across *movement* contexts. To
add the functionally distinct **foraging-vs-socializing** contrast at the level of
the *named* catalogue call types recovered in Rung 1, `scripts/run_calltype_context_specialization.py`
cross-references the validated NRKW/SRKW call types against the published field
ethograms in `data/join_tables/call_type_to_context.csv` [@ford1989; @foote2008;
@riesch2008; @yurk2002]. The context labels come from the ethograms, not from our
embeddings, so this is a literature-grounded contextual map of the recovered units
(non-circular), complementing the embedding decode.

Of 18 catalogue call types with a documented foraging or social context, **72%
(13/18) are single-context specialists**: foraging-specialists (e.g. N4, N9 - Ford's
top foraging calls) versus socializing-specialists (e.g. the multi-pod two-voiced
and pod-identity calls - Foote's social calls), with only 5 used in both
(foraging x socializing Fisher p = 0.069, underpowered at n = 18). This supports
the claim that resident killer whales use **distinct named call types across two functionally
distinct contexts** - the production-side reading of the "more than one context"
criterion at the catalogue level. It is not a claim of meaning. See
`reports/calltype_context_specialization_summary.json` and
`figures/calltype_context_specialization.png`.

## 5i. Result: SRKW call sequences carry structure beyond first order (tested)

Sections 5c/5e established *first-order* sequential structure over k-means tokens
and validated catalogue call types. The combinatorial-coding question the
comparative literature actually asks - sperm-whale codas [@sharma2024], bonobo and
chimpanzee compositionality [@berthet2025bonobo; @crockford2025] - is whether
structure goes *beyond* first order. `scripts/run_calltype_compositionality.py`
tests this against **first-order Markov surrogates** that preserve each
population's unigram and bigram statistics, so any excess cannot be a re-detection
of the first-order result and the finite-sample entropy bias cancels between data
and surrogates.

- **SRKW S-calls @ vfpa (19 types, 1,553 calls, 28 recordings): positive.** The
  2-back call reduces conditional entropy by delta = h2 - h3 = **0.645 bits**,
  versus a global first-order-surrogate null of 0.373 (**p ~= 1e-3**) and a tighter
  per-recording null of 0.546 (**p ~= 2e-3**). A held-out interpolated trigram
  beats a bigram by **0.09 bits/token**. The top over-represented 3-call
  motif is **S01->S04->S01** (observed 13 vs 1.87 expected under first order,
  z = 7.95, present in 5 recordings) - a candidate phrase.
- **NRKW N-calls @ dfo_crp (31 types, 5,273 calls): null.** Despite very heavy
  bouting, the second-order reduction is delta = 0.008 bits, indistinguishable
  from the first-order-surrogate null (**p = 1.0**): the strong NRKW first-order
  structure (Section 5e) is *not* accompanied by detectable second-order structure
  on this corpus.

Interpretation: at least one resident population (SRKW) shows a
beyond-first-order combinatorial prerequisite, with recurring candidate phrases;
the other (NRKW) does not, on the public data available. It remains a statement about call *ordering*, **not** semantic
compositionality (does A+B mean more than A,B?), which needs meaning/context labels
(Rung 2) and perception (Rung 3). See
`reports/calltype_compositionality_summary.json` and
`figures/calltype_compositionality.png`.

## 5j. Result: a label-free site-invariance transform partially deconfounds ecotype (methods)

H4 showed the ecotype signal is real but local: pooled decoding is a site shortcut
and cross-site transfer is near chance. `scripts/run_site_invariance.py` asks
whether a **label-free** transform can recover the site-invariant part of the
ecotype signal. It fits StandardScaler + PCA(100) + a site-nuisance subspace
projection on the *training* providers only (the held-out provider's ecotype labels
are never used; the transductive variant uses only its label-free embeddings), then
decodes ecotype.

- Leave-one-provider-out 4-way ecotype rises from **0.402 to 0.445** mean over folds
  (best k = 8 nuisance dimensions removed), against a permutation null of **0.234**
  (p ~= 0.005).
- Cross-site ecotype-pair transfer improves where it can: **SRKW vs TKW
  0.597 -> 0.625**, OKW vs TKW 0.560 -> 0.586 (the SAR-involving pair, which is
  single-provider, does not improve - as expected).
- Within-site ecotype is preserved: SRKW-vs-TKW at VFPA stays **0.883 -> 0.876**
  after removing the 8 nuisance dimensions, so the transform removes site nuisance
  without destroying biology.

Interpretation: a simple, label-free domain-adaptation step recovers part of the
site-invariant ecotype structure that raw embeddings leak away, while leaving the
within-site signal intact. The absolute cross-site number stays modest because
ecotype and recording site are **structurally confounded** in this corpus (e.g. SAR
is recorded at a single provider), a ceiling we report rather than hide. This is a
methods contribution to confound-controlled bioacoustics [@stowell2022; @ghani2023],
**not** a claim of meaning. See `reports/site_invariance_summary.json` and
`figures/site_invariance.png`.

## 5k. Result: validated call types span six behavioural contexts (catalogue level)

Section 5h established the foraging-vs-socializing contrast at the named-unit level.
Context-specific communication is conventionally framed as use across *more than one
context (e.g., alarm, mating, foraging)*, so
`scripts/run_calltype_multicontext.py` maps the validated Rung-1 call types onto the
full set of canonical killer-whale **behavioural** contexts in the published
ethograms, excluding pure identity-signalling associations (which encode *who* is
calling, not the behavioural context) [@ford1989; @foote2008; @riesch2008; @yurk2002].

The 16 NRKW/SRKW types with a documented behavioural context are distributed across
**six** functionally distinct contexts - foraging (8 types), travelling (5),
socializing (4), multi-pod aggregation (3), resting (1), greeting/excitement (1) -
with a specialization index of 0.62 (10/16 single-context). This is the
production-side reading of "more than one context" well beyond the movement-state
axis of the DTAG decode, at the level of the named units. The chi-square for
non-uniform distribution across contexts is suggestive only (chi2 = 9.6, p = 0.086,
small n), and the context labels are literature-grounded (not from embeddings), so
this complements rather than re-states the H5 decode. It is **not** a claim of
meaning. See `reports/calltype_multicontext_summary.json` and
`figures/calltype_multicontext.png`.

## 6. Tools added for this program

- `scripts/fetch_orcasound_labels.py` - anonymous, read-only enumeration and
  single-object download of the Orcasound public buckets, used to produce the
  Section 4 ceiling audit.
- `scripts/run_calltype_discovery.py` - within-ecotype unsupervised call-type
  discovery with a provider-purity guard and subsample-stability check, used to
  produce the Section 5b negative result.
- `scripts/run_sequence_structure.py` - first-order Markov / bigram test of
  sequential structure with a within-encounter order-shuffle null, used to
  produce the Section 5c positive result.
- `scripts/survey_dclde_calltypes.py` - enumerates DCLDE per-provider annotation
  files and quantifies `call_type` coverage (Section 4 call-type finding).
- `scripts/build_calltype_manifest.py` - builds and label-normalises the
  call-type manifest (`data/join_tables/call_type_manifest.csv`) for Rung 1.
- `scripts/run_calltype_model.py` - joins catalogue `call_type` labels onto the
  AVES2 embeddings and runs the within-provider and cross-provider call-type
  classifiers (Section 5d positive result).
- `scripts/run_calltype_sequence.py` - first-order Markov / bigram test over the
  *validated* catalogue call types (site held constant, within-recording shuffle
  null), used to produce the Section 5e positive result.
- `notebooks/calltype_encode_colab.ipynb` - encodes the *full* call-type manifest
  with AVES2 on a Colab GPU (streaming the public DCLDE audio) and runs the
  site-controlled classifiers over the complete 43-type catalogue, including the
  NRKW N-calls absent from the local embedding artifact [@hagiwara2023aves].
- `scripts/dtag_local_extract.py` - downloads public DTAG deposits, losslessly
  decodes each tag archive, detects communicative calls (0.5-10 kHz band, clicks
  and echolocation rejected), and cuts clips for the Section 5f context decode
  [@holt2024masking_data].
- `scripts/dtag_context_labels.py` - builds the movement-only foraging/non-foraging
  label from the calibrated 50 Hz depth/acceleration records and reports
  per-individual yield (`reports/context_label_yield.json`) [@tennessen2019].
- `scripts/dtag_context_decode.py` - frozen-AVES2 encode, leave-individual-out
  decode, and label-permutation null for the binary behavioural-context result
  (`reports/context_decode_summary.json`, `figures/context_decode.png`).
- `scripts/dtag_context_multilabel.py` - movement-only **three-state** context
  labels (foraging/travelling/resting; ODBA split [@wilson2006]).
- `scripts/dtag_context_multidecode.py` - three-way leave-individual-out decode and
  within-individual permutation null (`reports/context3_decode_summary.json`,
  `figures/context3_decode.png`).
- `scripts/dtag_calltype_context.py` - data-driven call-type clustering and
  call-type × context selectivity with a within-individual null
  (`reports/calltype_context_selectivity.json`, `figures/calltype_context.png`).
- `scripts/dtag_context_controls.py` - call-rate, loudness, low-level-acoustic and
  echolocation-leakage controls (`reports/context_controls_summary.json`,
  `figures/context_controls.png`).
- `scripts/run_playback_response_stats.py` - recomputes the differential-response
  contingency (same-pod vs different-pod vocal response) from the transcribed
  per-trial table of the published conspecific playback experiment
  [@filatova2011playback] (`reports/playback_response_summary.json`,
  `figures/playback_response.png`). Section 5g behavioural side.
- `scripts/build_playback_manifest.py` - fetches the public FEROP Kamchatka call
  catalogue [@russianorca_catalogue] and writes
  `data/join_tables/ferop_catalogue_manifest.csv`.
- `scripts/run_playback_response.py` - encodes the FEROP catalogue with frozen AVES2
  and tests dialect call-type separability against a label-shuffle null
  (`reports/playback_embedding_summary.json`, `figures/playback_embedding.png`).
  Section 5g embedding side.
- `scripts/summarize_broadcast_response.py` - rolls up the multi-study broadcast-
  response evidence (`data/join_tables/broadcast_response_evidence.csv`) into an
  explicit C3-criterion determination (`reports/broadcast_response_criterion.json`).
- `scripts/run_calltype_context_specialization.py` - foraging-vs-socializing
  specialization of the recovered catalogue call types from published ethograms
  (`reports/calltype_context_specialization_summary.json`,
  `figures/calltype_context_specialization.png`). Section 5h.
- `scripts/run_calltype_multicontext.py` - behavioural-context breadth of the
  validated catalogue call types across the six canonical ethogram contexts
  (`reports/calltype_multicontext_summary.json`,
  `figures/calltype_multicontext.png`). Section 5k.
- `scripts/run_calltype_compositionality.py` - structure beyond first order over
  the validated catalogue call types, tested against first-order Markov surrogates,
  with held-out trigram-vs-bigram gain and over-represented 3-call motifs
  (`reports/calltype_compositionality_summary.json`,
  `figures/calltype_compositionality.png`). Section 5i.
- `scripts/run_site_invariance.py` - label-free site-nuisance subspace projection
  for frozen embeddings, with leave-one-provider-out ecotype, cross-site pairs, a
  within-site sanity check, and a permutation null
  (`reports/site_invariance_summary.json`, `figures/site_invariance.png`). Section 5j.

## 7. What we can and cannot say

**Supported now:** killer-whale vocalisations carry population-level (ecotype)
identity recoverable with site controls (Rung 0); a discrete, catalogue-validated
**call-type repertoire** is recoverable in both resident populations (SRKW
14-type 0.709, NRKW 18-type 0.968, site held constant) and **transfers across
independent recording sites** (Rung 1, Section 5d); and their call streams carry
non-random first-order sequential structure beyond repetition - over both k-means
tokens and the **validated catalogue call types** in both populations (Rung 4,
Sections 5c and 5e); and **context-specific production of communicative calls
across more than one behavioural context**, with the individual held out - the
production side of Rung 2 (Section 5f): a three-way foraging/travelling/resting
decode (0.577, chance 0.333) on top of the binary foraging contrast (0.770), with
**specific call types occurring in specific contexts** (call-type × context
Cramér's V = 0.40, within-individual p < 0.001) and rate/loudness/echolocation
controls excluding the trivial explanations.

**Also supported (perception side, by re-analysis):** wild killer whales produce a
measurable, **dialect-selective response to broadcast conspecific calls** - they
reply to same-pod and not different-pod playbacks (6/6 vs 0/6, p = 0.002), naive
animals, often matching the played type - and frozen AVES2 recovers the dialect call-type
space underlying this contrast (purity 0.439 vs 0.05 null, p = 1e-3) (Rung 3, Section 5g)
[@filatova2011playback; @russianorca_catalogue]. The playback experiment is prior
published work re-analysed here.

**Not supported:** that the receiver's response is governed by the call's *content*
rather than its *dialect membership* (the step from "responds to same-vs-different
pod" to referential meaning); contexts beyond movement state (e.g. alarm/mating) on
the production side; and a mapping from named *catalogue* call types to specific
external events. "We decoded orca language" in the two-way, semantic sense is
therefore **not** a claim this work makes; the bounded statement is that
we have evidence for the production units, sequential structure, multi-context
context-specific production, **and** a dialect-selective receiver response to
broadcast calls, while the content->response step remains future work.

## 8. The gap to demonstrated call content

A demonstration of call content beyond structured signalling would require that
orcas use specific sounds or sound combinations to convey specific information
and that other orcas understand and act on it. That decomposes into five
documented requirements. For each we state what would test it, what we have, and
the single fact that addresses the gap. None of the open requirements can be addressed
by a larger model or more archival audio; they require behavioural labels and
playback. This is the central boundary of this project.

| # | Requirement | What tests it | Status here | What closes the gap |
|---|---|---|---|---|
| G1 | **Real call units** | Validated, stereotyped call types matching expert catalogues, not just clusters [@ford1989; @filatova2015] | Within-site SRKW 14-type 0.709 and NRKW 18-type 0.968; cross-site transfer 0.636 over 5 types (0.830 over 4 unambiguous), all p ~= 0.005 (Section 5d) | Extending to Bigg's/offshore and to finer matriline-level subtypes |
| G2 | **Meaning / context** | A call reliably maps to an external event (e.g. precedes reunion, occurs during prey pursuit, on calf separation) - the production criterion [@deecke2005] | Production-side evidence, multi-context. DTAG H5: communicative calls decode the caller's movement-defined context with the individual held out across **more than one** context (foraging/non-foraging 0.770; three-way foraging/travelling/resting 0.577, chance 0.333), and **specific call types occur in specific contexts** (call-type × context Cramér's V = 0.40, within-individual p < 0.001); rate/loudness/echolocation controls pass (Section 5f) [@holt2024masking_data; @tennessen2019; @wilson2006; @ford1989; @foote2008]; and at the named-unit level the validated catalogue types are documented across **six** functionally distinct behavioural contexts (Section 5k, specialization index 0.62) [@riesch2008; @yurk2002]. Remaining: the perception side, and mapping *named catalogue* types to events | Receiver-response measurement (G3/G4) and per-call synchronised coding tying *named* call types to specific external events |
| G3 | **Receiver response** | Another orca hears the signal and changes behaviour in the predicted direction - the perception criterion [@deecke2005] | Re-analysis evidence (Section 5g): wild killer whales respond selectively to broadcast conspecific calls (vocal reply to same-pod 6/6, different-pod 0/6, p = 0.002), naive animals, often matching the played type [@filatova2011playback; @miller2004repertoires] | Show the response tracks the call's *content*, not only its *dialect membership* |
| G4 | **Causality** | Controlled playback: a stimulus class raises a response above a matched contrast | Partial evidence. The same-pod vs different-pod contrast is a controlled differential-response design [@filatova2011playback]; an independent open dataset shows killer whales respond to a broadcast stimulus against matched noise/upsweep controls [@selbmann2026aversive] (heterospecific stimulus) | A conspecific playback with matched acoustic controls that isolates call content |
| G5 | **Combination rules** | Sequences carry information beyond their parts: A+B differs from A, B, or B+A [@sharma2024; @berthet2025bonobo] | First-order sequential structure over *validated* call types in both populations (Section 5e), and structure beyond first order in SRKW S-calls (Section 5i: second-order info 0.645 bits, p ~= 1e-3 vs first-order Markov surrogates; candidate phrase S01->S04->S01, z = 7.95), though NRKW shows no detectable second-order structure; compositional *meaning* is still not testable without G1-G2 | A semantic compositionality test (does A+B *mean* more than A, B?), which needs meaning/context labels (G2) and perception (G3/G4) - not a bigger model |

**Short summary.** We have sound structure (Rung 0, site-controlled),
**validated call units in both resident populations that transfer across sites**
(Rung 1, Section 5d), sequence structure (Rung 4 foot): one call tells you
something about the likely next call, **context-specific production across more
than one behavioural context** (Rung 2 production side, Section 5f): communicative
calls track whether the whale is foraging, travelling or resting with the individual
held out, and **a dialect-selective receiver response to broadcast calls** (Rung 3
perception side, Section 5g): wild whales reply to same-pod and not different-pod
playbacks (p = 0.002), naive animals, by re-analysis of a published experiment. What
we do **not** have is evidence that the response is governed by the call's *content*
rather than its *dialect membership* - i.e. referential meaning.
The bridge from here to "orca language" is **not a bigger model** - it is a
controlled playback that isolates call *content* (the content->response step). The AI
can name candidate units and candidate phrases and now shows receivers act on the
broadcast signal; what remains is showing they act on its meaning. This document is
the contract for what each result is allowed to claim.

## 9. Public-data scope vs the fieldwork-gated residual

It is worth separating the gaps into two kinds: those that **public-archival
re-analysis can close** and those that **require new field data**. The first kind
is addressed here; the second remains a single fieldwork item.

**Addressed from public data (no new field collection):**

1. **Real call units (G1).** Validated catalogue call types, both resident
   populations, site-controlled and cross-site-transferable (Sections 5d).
2. **Sequential structure (G5, first order).** Over k-means tokens and validated
   catalogue types, both populations (Sections 5c, 5e).
3. **Structure beyond first order (G5, combinatorial).** SRKW S-calls exceed
   first-order Markov surrogates with recurring candidate phrases; NRKW is null and
   reported as such (Section 5i).
4. **Production-side context-specificity across more than one context (G2,
   production).** The DTAG decode resolves three movement-defined contexts with the
   individual held out and shows call-type x context selectivity (Section 5f), and
   at the named-unit level the catalogue types are documented across **six**
   behavioural contexts (Sections 5h, 5k).
5. **A measurable receiver response to a broadcast endogenous signal (G3, by
   re-analysis).** Wild killer whales respond selectively to broadcast conspecific
   calls, naive animals (Section 5g), corroborated across independent datasets.
6. **Confound control as a reusable method.** Leave-one-provider-out isolation,
   cross-site transfer, a negative-control battery, and a label-free site-invariance
   transform (Section 5j).

**The single fieldwork-gated residual.** Everything still open reduces to **one**
experiment: *a controlled conspecific playback that isolates call **content** and
measures a receiver response across more than one content class* (G3-content + G4).
This is the design of recent context-specific dolphin-signal work, which broadcast
specific non-signature whistle types and measured function-specific responses
[@sayigh2025nsw]. Two apparently separate gaps are in fact the *same* fieldwork
item, because of how the public corpora are distributed:

- **The production<->perception "join on the same unit" is cross-population.** Our
  production-context evidence (DTAG and the Ford/Foote ethograms) is for the Pacific
  Northeast resident populations (N-calls, S-calls); the only conspecific
  playback-response evidence is for the Kamchatka population (K-calls)
  [@filatova2011playback; @russianorca_catalogue]. These are **non-overlapping
  catalogues**, so no public dataset pairs "produced-in-context C" and
  "elicits-response R" on the *same named call type*. Closing it needs either a
  playback on the population where we have context, or per-call behavioural-context
  coding on the population where we have playback - **both are new field/observational
  data**, not re-analysis.
- **Content vs. dialect.** The re-analysed response (Section 5g) tracks *dialect
  membership* (same vs different pod), not call *content*; separating the two needs a
  content-controlled playback [@deecke2005]. Same experiment.

**Beyond this study's scope (an interactive frontier).** Putting the model *in the
loop* - generating or selecting a stimulus and measuring the response per trial -
is an interactive two-way-communication goal, explicitly future work. The nearest
archival step, an embedding stimulus->response predictor on the playback session
audio, is gated on the **request-only** FEROP session recordings
(`docs/data_requests.md`), a data request rather than a model limitation; the public
catalogue supports only the dialect-space recovery already reported.

**Bottom line.** Public-data re-analysis addresses the archival parts of the program. The
sole irreducible residual is a content-isolating first-party playback - field work
that needs a collaborator, and the same step that separates structured signalling
from demonstrated meaning. No larger model or additional archival audio closes it.

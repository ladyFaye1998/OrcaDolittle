<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Literature review — working notes

> **Status.** Working bibliographic notes, in the order I have actually consulted them. Entries marked **(read in detail)** are ones I have read carefully; **(skimmed)** are ones I have only summarised from abstracts. The locked plan now incorporates *all four threads* below.

## 1. Killer-whale acoustic ethology &mdash; the criterion-2 join layer

- [@ford1989] &mdash; Foundational catalogue of matrilineal pulsed-call repertoires in NE Pacific Resident orcas. **(skimmed)**
- [@yurk2002] &mdash; Within-clan vs across-clan playbacks in Alaska Residents. **(skimmed)**
- [@deecke2000] &mdash; Multi-generation dialect drift. **(skimmed)**
- [@foote2008] &mdash; V4 excitement call across contexts. The clearest single-paper case for context-specific orca vocalisation. **(skimmed)** &mdash; correct journal *Ethology*, not *Current Biology*; cite-error corrected 2026-05-18 in `paper/refs.bib`.
- [@filatova2015; @filatova2018biphonic] &mdash; Kamchatka residents; geographic + biphonic-call generalisation. **(skimmed)**
- [@riesch2012] &mdash; Review of cultural evolution evidence in killer whales. **(skimmed)**
- [@riesch2008] &mdash; Discrete-call paper in J. Acoust. Soc. Am. **(unread)**
- [@deecke2005] &mdash; Transient calls played to harbour seals. Cross-species; excluded from primary criterion-3 layer. **(skimmed)**

**Open task (Stage 2 in `EXECUTION_PLAN.md`):** Read [@ford1989; @foote2008; @filatova2015] in full and build the `call_type -> behavioural_context` join CSV.

## 2. Killer-whale playback corpus &mdash; the criterion-3 evidence layer

These are the three corpora the H4 head [@yovel2023doctor] predicts against. Per-paper extraction notes live in `playback_corpus.md`.

- [@bowers2018] &mdash; Cross-species playback (orca calls → pilots + Risso's, DTAG-quantified). **(unread)**
- [@cure2026] &mdash; 15 trials on 8 tagged orcas. **(unread)**
- [@filatova2011] &mdash; Kamchatka resident playback (companion paper to the call-corpus paper of the same group). **(unread)** **VERIFY** that this is the correct Filatova et al. paper.

## 3. Sequence and combinatorial structure in cetaceans &mdash; precedent for head H3

- [@sharma2024] &mdash; Sperm-whale coda combinatorial structure. The closest methodological precedent for the H3 sequence-LM head; ported here from sperm whale to orca. **(skimmed)**
- [@paradise2025wham] &mdash; WhAM translative model of sperm whale vocalization. **(unread)**
- [@bermant2019] &mdash; Deep-learning sperm-whale detection + classification on the same Dominica EC-1 corpus. **(unread)**
- [@sainburg2019animal] &mdash; Birdsong / speech sequence-statistics parallel. **(skimmed)**

## 4. Bioacoustic foundation models &mdash; the encoder layer

- [@robinson2024naturelm] &mdash; NatureLM-audio. **Primary** frozen encoder. **(unread; VERIFY arXiv ID)**.
- [@hagiwara2023aves] &mdash; AVES (HuBERT-style SSL on animal vocalisations). **Comparator** encoder via the AVES2 (BEATs backbone) checkpoint [@chen2022beats]. **(skimmed)**
- [@hamer2025perch] &mdash; Perch 2.0. Held in reserve as a third comparator. **(skimmed)**
- [@hsu2021hubert] &mdash; Speech-domain ancestor of AVES. **(skimmed)**
- [@bergler2019orcaspot] &mdash; ORCA-SPOT killer-whale-specific detector. Useful for the detection sanity check, not for criterion 2.

## 5. Embedding-space analysis methodology &mdash; precedent for heads H1, H2

- [@sainburg2020] &mdash; UMAP + HDBSCAN repertoire-discovery framework. **(skimmed)** &mdash; direct precedent for the H2 head.
- [@mcinnes2018umap; @mcinnes2017hdbscan] &mdash; underlying algorithms.

## 6. Interspecies communication, framing, and panel-relevant theory

- [@yovel2023doctor] &mdash; The three obstacles framework. **(read in detail)** &mdash; primary lens for the entire submission.
- [@wittgenstein1953] &mdash; The Wittgenstein boundary; cited in the philosophical-rigour discussion section.
- [@kershenbaum2024whyanimalstalk] &mdash; Panel member's popular book; sets the tone for the 2-minute video.
- [@sayigh2025nsw] &mdash; 2025 Coller-Dolittle winner. **(read second-hand)** &mdash; benchmark for the level of evidence the panel rewards.
- [@sayigh2022sdwd] &mdash; SDWD database paper. **(skimmed)**

## 7. Why the alternative species were retired

- [@lehnhoff2025essd; @lehnhoff2025scirep] &mdash; Lehnhoff team's DOLPHINFREE data paper + competing AI paper (Nov 2025). Closed the common-dolphin lane.
- [@prat2016bat] &mdash; Yovel-lab Egyptian fruit bat. Closed because Yovel is on the panel.
- [@crockford2025; @berthet2025bonobo; @mathevon2025mouse; @elie2025zebrafinch] &mdash; 2025-26 finalists. Lanes occupied.

## How the locked plan stands against the literature

For the locked plan (frozen encoder + four heads + DCLDE 2026 + behavioural-context join + playback-corpus re-analysis):

### Novelty check (head-by-head)

- **H1 (linear probes for ecotype + context).** [@palmer2025dclde] is the headline benchmark for ecotype classification on this corpus and does *not* address behavioural context. Behavioural-context probes on embedding features have not, to my knowledge, been published for orca. *Confirmation search needed before submission*.
- **H2 (unsupervised clusters).** Foundation-model UMAP+HDBSCAN over DCLDE-scale orca audio has not been published. [@sainburg2020]'s framework has been applied to many species but not orca at this scale.
- **H3 (sequence LM over call-ID streams).** A Transformer language model over orca call-ID streams has not been published. [@sharma2024] did this for sperm whale; this is a direct port to orca.
- **H4 (embedding-distance playback predictor).** A unified re-analysis of [@bowers2018; @cure2026; @filatova2011] as a single off-policy dataset has not been published. *Confirmation search needed*.

## What this section is *not*

- It is not a systematic literature search. A real systematic search runs in Week 1 of `EXECUTION_PLAN.md`.
- It is not a guarantee of novelty; each head's novelty claim above needs a confirmation search before the preprint is posted.
- It is not a substitute for reading the primary papers in full. Several entries above are still **unread**.

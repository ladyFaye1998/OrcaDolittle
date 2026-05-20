<!-- Citation rule .cursor/rules/citations.mdc applies: every numerical or factual claim points to a key in OrcaDolittle/paper/refs.bib. -->

# Head H3 &mdash; implementation notes

> **Status.** Implementation landed 2026-05-20 on branch `cursor/stage-1-concrete-deliverables-946c`. End-to-end runnable on synthetic call-ID streams (CPU, ~1-3 min) and on real DCLDE 2026 [@palmer2025dclde; @palmer2025dclde_data] annotations when the CSV is present. No biological claim is made by this code; it is the pipeline that *would* produce the H3 number defined in `docs/ai_architecture.md` once DCLDE inputs are pulled per Stage 1 of `EXECUTION_PLAN.md`.

This document is the operational README for the code in `src/orcadolittle/`. The locked methodology spec lives in `docs/ai_architecture.md`; the strategic case for promoting H3 to the manuscript headline lives in `docs/h3_headline_pivot.md`; this file only covers *what the code does, how to run it, and how to read its output*.

---

## What this code is

The implementation of head H3 of the locked architecture in `docs/ai_architecture.md`:

- a BERT-style Transformer masked-language-model [@vaswani2017attention; @devlin2019bert] over per-encounter killer-whale call-ID streams, with default hyperparameters mirroring the locked spec (6 layers, 8 heads, `d_model = 512`, 15% mask probability, max sequence length 256);
- a tokenisation + batching layer for per-encounter call streams, with both a real DCLDE 2026 loader and a synthetic Markov emitter on the same interface;
- a shuffled-sequence permutation-test evaluator that produces the n_perm null distribution required by every head in the locked architecture;
- a single CLI entry point (`orca-h3-pilot`) that runs the full pipeline on either substrate.

## What this code is *not*

- It is not a biological result. The synthetic substrate is a Markov emitter; running the pilot on synthetic data tells you whether the *implementation* recovers known bigram structure, nothing more.
- It is not a foundation model. The Transformer is a small, downstream head; encoder embeddings from [@robinson2024naturelm; @hagiwara2023aves] are out of scope for this module and live in their own (not-yet-implemented) pipeline.
- It is not the manuscript's headline figure. That figure requires the DCLDE 2026 substrate, the n_perm = 10,000 spec from the locked plan, and the encoder-embedding inputs implementation. This code is the part of that figure that can be written and tested now.
- It is not scaffolding. Every module has a real implementation, validated against the synthetic substrate in `tests/`.

---

## Repository layout

```
pyproject.toml
src/orcadolittle/
  __init__.py
  cli.py                          # `orca-h3-pilot` entry point
  data/
    call_streams.py               # Vocab, CallStreamDataset, MLM masking
    synthetic.py                  # Markov synthetic streams + shuffle baseline
    dclde_loader.py               # DCLDE Annotations.csv -> per-encounter streams
  models/sequence_lm.py           # BERT-style Transformer MLM
  train/mlm.py                    # AdamW + warmup/cosine + MLM loss
  eval/permutation.py             # n_perm shuffled-sequence controls
scripts/run_h3_pilot.py           # thin alias for `orca-h3-pilot`
tests/                            # 18 pytest tests, run end-to-end on CPU
```

## How to install

```
pip install -e .[dev]
```

## How to run the pilot &mdash; synthetic substrate (sanity check)

```
orca-h3-pilot \
    --substrate synthetic \
    --max-steps 300 --warmup-steps 30 \
    --batch-size 32 --d-model 64 --n-layers 3 --n-heads 4 \
    --max-len 64 \
    --synthetic-encounters 2000 \
    --n-perm 5 \
    --out h3_pilot_synthetic.json
```

This runs in ~1-3 minutes on CPU and writes a JSON summary with the real vs shuffled MLM losses, the gap, and the permutation p-value. The synthetic-substrate run is the validity check on the implementation, not a result about killer whales.

## How to run the pilot &mdash; real DCLDE substrate

Once `Annotations.csv` is pulled per Stage 1 / Week 1 of `docs/dataset_plan.md`:

```
orca-h3-pilot \
    --substrate dclde \
    --dclde-csv /path/to/Annotations.csv \
    --dclde-ecotype SRKW \
    --max-steps 5000 --warmup-steps 200 \
    --batch-size 32 --d-model 512 --n-layers 6 --n-heads 8 \
    --max-len 256 \
    --n-perm 100 \
    --out h3_pilot_dclde.json
```

For the headline number in the manuscript, raise `--n-perm` to the 10,000 specified in `docs/ai_architecture.md`. The DCLDE column-name mapping is configurable via the `DCLDEColumns` dataclass in `src/orcadolittle/data/dclde_loader.py`; the defaults reflect the documented schema at time of writing and the Stage-1 schema-confirmation task pins them for a given pull.

## How to read the output

The pilot writes a JSON file with these fields (all `float`):

| Field | Meaning |
|---|---|
| `real_eval_loss` | Held-out MLM cross-entropy on the real per-encounter call streams. |
| `mean_shuffled_loss` | Mean held-out MLM cross-entropy across the `n_perm` shuffled controls. |
| `gap` | `mean_shuffled_loss - real_eval_loss`. Positive values are consistent with the real sequences carrying order information beyond unigram statistics. |
| `p_value` | One-sided permutation p-value: fraction of shuffled-control losses `<=` the real loss, with the standard `+1/+1` correction. |
| `n_perm` | Number of shuffled controls actually trained. |

A scientifically meaningful H3 result requires both a positive `gap` and a small `p_value` on the *DCLDE* substrate, not the synthetic substrate. The synthetic-substrate result tells you the pipeline works.

## How the synthetic substrate is constructed

The synthetic emitter is a first-order Markov chain over a discrete call-type alphabet. Transition rows are sampled from a sparse Dirichlet (`alpha = 0.1` by default), which produces highly predictable bigram statistics and therefore a large detectable gap to the shuffled-sequence baseline. This is the cleanest available sanity check that the implementation recovers structure when structure is genuinely present; it is *not* a model of killer-whale call sequences. See `src/orcadolittle/data/synthetic.py` for the precise specification.

## Tests

```
python -m pytest tests/
```

Eighteen tests covering vocab/round-trip behaviour, MLM masking ratios, dataset truncation and padding, model forward shape and weight tying, end-to-end training-reduces-loss on the synthetic substrate, permutation p-value math, and an end-to-end small-scale `run_shuffled_baseline` call. All pass on CPU in under ten seconds.

## Mapping to the locked plan

| Locked-plan element | Where implemented |
|---|---|
| Per-encounter call-ID sequences, max length 256 | `data/call_streams.py` (truncation + BOS/EOS) and `data/dclde_loader.py` (gap-based sessionisation) |
| 6L / 8H / d_model=512 Transformer | `models/sequence_lm.py` defaults |
| BERT-style MLM, 15% mask | `data/call_streams.py:mlm_mask` |
| Shuffled-sequence baseline, n_perm = 10,000 | `eval/permutation.py:run_shuffled_baseline` (CLI default is small `n_perm` for the pilot; raise to 10,000 for the submission) |
| `--seed` default 0, mean over seeds 0..4 reported | Honoured by every CLI entry; multi-seed averaging is a wrapper script left for Stage 3 |
| Frozen encoder (NatureLM-audio / AVES2) | **Out of scope for this module.** The H3 pipeline operates on call-ID tokens; the encoder pipeline produces per-call embeddings, not the tokens H3 consumes. The two are joined at the call-clustering step (head H2) before H3 sees its input. |
| Compute envelope (~overnight on 4090) | Validated on CPU at pilot scale (~1-3 min for 300 steps + 5 permutations on the small model). The locked-spec model and n_perm = 10,000 fit the documented overnight estimate. |

## Cross-references

- `docs/ai_architecture.md` &mdash; locked four-head stack; H3 spec.
- `docs/h3_headline_pivot.md` &mdash; standalone proposal to promote H3 to the manuscript headline (not adopted; this code does not assume the pivot has been accepted).
- `docs/dataset_plan.md` &mdash; Stage 1 / Week 1 DCLDE pull; H3 cannot run on real data until that is done.
- `EXECUTION_PLAN.md` &mdash; Stage 3 H3 deliverable; this code is the implementation of that deliverable.
- `paper/refs.bib` &mdash; bibliography source of truth.

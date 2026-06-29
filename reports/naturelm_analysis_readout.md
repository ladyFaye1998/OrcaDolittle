# NatureLM-audio analysis readout

**Analysis status:** `PASS_WITH_PERMUTATION_TESTS`

**Run mode:** `FULL_ANALYSIS`
**Full uncapped data:** `True`
**Permutation tests complete:** `True`

## Metrics

| Check | Result | Baseline | p-value |
|---|---:|---:|---:|
| FEROP K-type separability | 0.366 | 0.050 | 0.001 |
| VFPA/SRKW call types | 0.709 | 0.071 | 0.005 |
| DFO-CRP/NRKW call types | 0.800 | 0.062 | 0.005 |

## Result sentence

The two primary analyses were repeated with a frozen NatureLM-audio encoder: FEROP K-type catalogue exemplars remained separable (leave-one-out 1-NN purity=0.366, proportional chance=0.050), and site-controlled catalogue call-type recovery remained above chance for SRKW/VFPA (balanced accuracy=0.709, chance=0.071) and NRKW/DFO-CRP (balanced accuracy=0.800, chance=0.062). This is a cross-encoder check, not evidence of semantic meaning.

## Boundary

Second-encoder representation check only. Do not claim meaning, translation,
syntax, intention, or playback causality from this notebook.

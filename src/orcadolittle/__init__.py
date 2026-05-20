"""OrcaDolittle head H3: per-encounter Transformer MLM over killer-whale call-ID streams.

This package is the implementation of head H3 of the architecture locked in
``docs/ai_architecture.md``. It does NOT make any biological claim. It provides:

  * a tokenisation + batching layer for per-encounter call-ID streams
    (``orcadolittle.data``);
  * a small Transformer masked-language-model
    (``orcadolittle.models.sequence_lm``);
  * an MLM training loop (``orcadolittle.train.mlm``);
  * a shuffled-sequence permutation-test evaluator
    (``orcadolittle.eval.permutation``).

The package is runnable end-to-end on synthetic call-ID streams (see
``orcadolittle.data.synthetic``) so the implementation can be validated
without DCLDE 2026 audio in hand. The DCLDE loader
(``orcadolittle.data.dclde_loader``) is the seam where the real
``Annotations.csv`` plugs in.
"""

__version__ = "0.1.0"

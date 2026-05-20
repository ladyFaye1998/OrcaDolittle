"""Synthetic per-encounter call-ID streams with controllable structure.

The point of this module is *not* to model killer-whale behaviour. Its single
purpose is to give the H3 implementation a substrate it can be validated
against end-to-end, without DCLDE 2026 audio in hand. The synthetic streams
have a real, controllable bigram structure: a Markov-chain emitter with a
sparse transition matrix. The masked-language-model objective is trivially
above-chance on these streams when the bigram structure is preserved, and
indistinguishable from a unigram-only model when the streams are
within-sequence shuffled. That is the cleanest available sanity check on the
H3 methodology, since it asks the model only to recover structure we put in
on purpose.

Using this module to back any biological claim is incorrect. The DCLDE 2026
loader in ``orcadolittle.data.dclde_loader`` is the substrate for real
analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class SyntheticConfig:
    """Configuration for the synthetic Markov emitter.

    Attributes
    ----------
    num_call_types:
        Number of distinct synthetic call types (does not include special
        tokens; ``Vocab.size`` will be ``NUM_SPECIAL + num_call_types``).
    num_encounters:
        Number of synthetic encounters (sequences) to emit.
    mean_len, std_len:
        Per-encounter length distribution, sampled from a clipped Gaussian
        with these moments. Lengths below ``min_len`` are resampled.
    min_len, max_len:
        Hard bounds on encounter length, in raw call tokens (excluding
        special tokens added at batching).
    transition_concentration:
        Dirichlet concentration parameter for the row distributions of the
        transition matrix. Low values (e.g. 0.1) produce sparse,
        highly-predictable bigram statistics; high values (e.g. 10.0)
        produce nearly-uniform transitions and therefore nearly-unigram
        sequences. The pilot uses 0.1 so that the bigram signal is large
        enough to be detected on small models in tens of training steps.
    seed:
        Numpy random seed. Reproducibility convention follows
        ``docs/ai_architecture.md``: every script accepts ``--seed`` and
        defaults to 0.
    """

    num_call_types: int = 32
    num_encounters: int = 4_000
    mean_len: float = 48.0
    std_len: float = 16.0
    min_len: int = 8
    max_len: int = 200
    transition_concentration: float = 0.1
    seed: int = 0


def _sample_transition_matrix(
    num_call_types: int, concentration: float, rng: np.random.Generator
) -> np.ndarray:
    alpha = np.full(num_call_types, concentration, dtype=np.float64)
    rows = np.stack(
        [rng.dirichlet(alpha) for _ in range(num_call_types)], axis=0
    )
    return rows


def _sample_start_distribution(
    num_call_types: int, concentration: float, rng: np.random.Generator
) -> np.ndarray:
    alpha = np.full(num_call_types, concentration, dtype=np.float64)
    return rng.dirichlet(alpha)


def make_synthetic_streams(cfg: SyntheticConfig) -> tuple[list[list[int]], dict]:
    """Generate synthetic per-encounter call-ID streams.

    Returns
    -------
    streams:
        A list of length ``cfg.num_encounters``, each element a list of
        integer call IDs in ``[NUM_SPECIAL, NUM_SPECIAL + cfg.num_call_types)``.
        IDs are already shifted past the special-token range so the result
        can be fed directly to ``CallStreamDataset`` without any further
        offset.
    meta:
        Dict containing the transition matrix and start distribution that
        produced the streams, for diagnostics.
    """
    from orcadolittle.data.call_streams import NUM_SPECIAL

    rng = np.random.default_rng(cfg.seed)
    transitions = _sample_transition_matrix(
        cfg.num_call_types, cfg.transition_concentration, rng
    )
    start = _sample_start_distribution(
        cfg.num_call_types, cfg.transition_concentration, rng
    )

    streams: list[list[int]] = []
    for _ in range(cfg.num_encounters):
        length = int(round(rng.normal(cfg.mean_len, cfg.std_len)))
        length = max(cfg.min_len, min(cfg.max_len, length))
        seq = np.empty(length, dtype=np.int64)
        seq[0] = rng.choice(cfg.num_call_types, p=start)
        for t in range(1, length):
            seq[t] = rng.choice(cfg.num_call_types, p=transitions[seq[t - 1]])
        streams.append((seq + NUM_SPECIAL).tolist())

    meta = {
        "transitions": transitions,
        "start": start,
        "num_call_types": cfg.num_call_types,
    }
    return streams, meta


def shuffle_within_sequence(
    streams: Sequence[Sequence[int]], seed: int = 0
) -> list[list[int]]:
    """Permute the tokens within each sequence, preserving unigram counts.

    This is the head-H3 null distribution generator: it destroys *order*
    information (bigram and higher n-gram structure) while leaving per-call
    marginal frequencies untouched. A correctly-implemented MLM should fit
    real sequences strictly better than shuffled ones if and only if
    there is order information beyond unigram statistics. On the synthetic
    Markov streams generated by ``make_synthetic_streams``, this is true by
    construction.
    """
    rng = np.random.default_rng(seed)
    out: list[list[int]] = []
    for s in streams:
        arr = np.array(s, dtype=np.int64)
        rng.shuffle(arr)
        out.append(arr.tolist())
    return out

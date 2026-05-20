"""Shuffled-sequence permutation test for head H3.

The H3 question is: does a Transformer MLM fit per-encounter call-ID streams
strictly better than the same model fits the same streams with their tokens
within-sequence shuffled? Within-sequence shuffling preserves unigram
statistics (per-call marginal frequencies) and destroys order statistics
(bigram and higher). A model that wins only because of marginal frequencies
will therefore show no gap; a model that has captured sequence structure
will show a gap whose size is the H3 effect.

The locked plan in ``docs/ai_architecture.md`` specifies ``n_perm = 10,000``
for every reported effect. This module is the implementation that produces
that number. For the pilot, smaller ``n_perm`` is sufficient and faster; for
the headline number reported in the submission paper, use the locked
default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
import torch

from orcadolittle.data.call_streams import CallStreamDataset
from orcadolittle.data.synthetic import shuffle_within_sequence
from orcadolittle.models.sequence_lm import SequenceLM, SequenceLMConfig
from orcadolittle.train.mlm import TrainConfig, evaluate_mlm, train_mlm


@dataclass
class PermutationConfig:
    n_perm: int = 10_000
    pilot_n_perm: int = 100
    eval_only: bool = False
    seed: int = 0


@dataclass
class PermutationResult:
    real_eval_loss: float
    shuffled_eval_losses: list[float] = field(default_factory=list)
    n_perm: int = 0

    @property
    def mean_shuffled_loss(self) -> float:
        return float(np.mean(self.shuffled_eval_losses)) if self.shuffled_eval_losses else float("nan")

    @property
    def gap(self) -> float:
        """Positive value means real sequences fit strictly better than shuffled."""
        return self.mean_shuffled_loss - self.real_eval_loss

    @property
    def p_value(self) -> float:
        """One-sided permutation p-value: P(shuffled loss <= real loss).

        Lower is better evidence that real sequences carry order information
        beyond unigram statistics.
        """
        if not self.shuffled_eval_losses:
            return float("nan")
        wins = int(np.sum(np.asarray(self.shuffled_eval_losses) <= self.real_eval_loss))
        return (1 + wins) / (1 + len(self.shuffled_eval_losses))

    def summary(self) -> dict[str, float]:
        return {
            "real_eval_loss": float(self.real_eval_loss),
            "mean_shuffled_loss": float(self.mean_shuffled_loss),
            "gap": float(self.gap),
            "p_value": float(self.p_value),
            "n_perm": float(self.n_perm),
        }


def _streams_from_dataset(ds: CallStreamDataset) -> list[list[int]]:
    """Recover raw (pre-BOS/EOS) call-ID streams from a ``CallStreamDataset``.

    ``CallStreamDataset`` stores each item as ``[BOS, ..., EOS]``; the
    permutation test shuffles only the interior tokens.
    """
    from orcadolittle.data.call_streams import BOS_ID, EOS_ID

    out: list[list[int]] = []
    for i in range(len(ds)):
        seq = ds[i].tolist()
        if seq and seq[0] == BOS_ID:
            seq = seq[1:]
        if seq and seq[-1] == EOS_ID:
            seq = seq[:-1]
        out.append(seq)
    return out


def run_shuffled_baseline(
    *,
    base_model_cfg: SequenceLMConfig,
    train_dataset: CallStreamDataset,
    eval_dataset: CallStreamDataset,
    train_cfg: TrainConfig,
    perm_cfg: PermutationConfig,
    device: torch.device | str = "cpu",
    use_pilot_n: bool = True,
    log_fn=print,
) -> tuple[PermutationResult, SequenceLM]:
    """Train one real model and ``n_perm`` shuffled-control models.

    Returns
    -------
    result:
        ``PermutationResult`` with the real model's held-out MLM loss, the
        shuffled-model losses, and the one-sided permutation p-value.
    real_model:
        The trained real-data model, returned so the caller can persist
        weights or inspect the embedding table.
    """
    n_perm = perm_cfg.pilot_n_perm if use_pilot_n else perm_cfg.n_perm

    log_fn(f"[H3] training real-sequence model (vocab={base_model_cfg.vocab_size})")
    real_model = SequenceLM(base_model_cfg)
    train_mlm(
        real_model,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        cfg=train_cfg,
        device=device,
        log_fn=log_fn,
    )
    real_eval = evaluate_mlm(
        real_model,
        eval_dataset,
        batch_size=max(64, train_cfg.batch_size),
        mask_prob=train_cfg.mask_prob,
        seed=train_cfg.seed,
        device=device,
    )
    real_loss = real_eval["mlm_loss"]
    log_fn(f"[H3] real eval mlm_loss = {real_loss:.4f}")

    shuffled_losses: list[float] = []
    raw_train_streams = _streams_from_dataset(train_dataset)
    raw_eval_streams = _streams_from_dataset(eval_dataset)
    for p in range(n_perm):
        seed = perm_cfg.seed + 1 + p
        shuffled_train = shuffle_within_sequence(raw_train_streams, seed=seed)
        shuffled_eval = shuffle_within_sequence(raw_eval_streams, seed=seed + 10_000)
        shuf_train_ds = CallStreamDataset(shuffled_train, max_len=train_dataset.max_len)
        shuf_eval_ds = CallStreamDataset(shuffled_eval, max_len=eval_dataset.max_len)
        log_fn(f"[H3] permutation {p + 1}/{n_perm}: training shuffled-sequence model")
        shuf_model = SequenceLM(base_model_cfg)
        shuf_cfg = TrainConfig(
            batch_size=train_cfg.batch_size,
            max_steps=train_cfg.max_steps,
            warmup_steps=train_cfg.warmup_steps,
            lr_peak=train_cfg.lr_peak,
            lr_min=train_cfg.lr_min,
            weight_decay=train_cfg.weight_decay,
            grad_clip=train_cfg.grad_clip,
            eval_every=train_cfg.max_steps + 1,
            mask_prob=train_cfg.mask_prob,
            seed=seed,
            log_every=train_cfg.max_steps + 1,
        )
        train_mlm(
            shuf_model,
            train_dataset=shuf_train_ds,
            eval_dataset=None,
            cfg=shuf_cfg,
            device=device,
            log_fn=lambda *_args, **_kw: None,
        )
        shuf_eval = evaluate_mlm(
            shuf_model,
            shuf_eval_ds,
            batch_size=max(64, train_cfg.batch_size),
            mask_prob=train_cfg.mask_prob,
            seed=seed,
            device=device,
        )
        shuffled_losses.append(float(shuf_eval["mlm_loss"]))
        log_fn(
            f"[H3] permutation {p + 1}/{n_perm}: shuffled eval mlm_loss = "
            f"{shuf_eval['mlm_loss']:.4f}"
        )

    result = PermutationResult(
        real_eval_loss=float(real_loss),
        shuffled_eval_losses=shuffled_losses,
        n_perm=n_perm,
    )
    return result, real_model

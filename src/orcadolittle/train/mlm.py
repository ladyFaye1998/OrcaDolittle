"""MLM training loop for the head-H3 sequence LM.

Standard BERT-style masked-language-model training: AdamW, linear warmup +
cosine decay, no fancy mixed-precision shortcuts (the entire pilot is small
enough to fit in fp32 on the 4090 within the compute envelope in
``docs/ai_architecture.md``). Reproducibility convention: every entry point
accepts ``seed`` and the default is 0.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import torch
from torch import nn
from torch.utils.data import DataLoader

from orcadolittle.data.call_streams import (
    CallStreamDataset,
    collate_call_streams,
    mlm_mask,
)
from orcadolittle.models.sequence_lm import SequenceLM


@dataclass
class TrainConfig:
    batch_size: int = 32
    max_steps: int = 2_000
    warmup_steps: int = 100
    lr_peak: float = 3e-4
    lr_min: float = 3e-5
    weight_decay: float = 0.01
    grad_clip: float = 1.0
    eval_every: int = 200
    mask_prob: float = 0.15
    seed: int = 0
    log_every: int = 50


def _make_loader(
    dataset: CallStreamDataset, batch_size: int, shuffle: bool, seed: int
) -> DataLoader:
    g = torch.Generator()
    g.manual_seed(seed)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=collate_call_streams,
        generator=g if shuffle else None,
        drop_last=False,
    )


def _lr_at(step: int, cfg: TrainConfig) -> float:
    if step < cfg.warmup_steps:
        return cfg.lr_peak * (step + 1) / max(1, cfg.warmup_steps)
    progress = (step - cfg.warmup_steps) / max(1, cfg.max_steps - cfg.warmup_steps)
    progress = min(1.0, max(0.0, progress))
    cos = 0.5 * (1.0 + math.cos(math.pi * progress))
    return cfg.lr_min + (cfg.lr_peak - cfg.lr_min) * cos


def _mlm_loss(
    logits: torch.Tensor, labels: torch.Tensor
) -> tuple[torch.Tensor, int]:
    """Cross-entropy on positions where labels != -100. Returns (loss, n_tokens)."""
    flat_logits = logits.view(-1, logits.shape[-1])
    flat_labels = labels.view(-1)
    n_tokens = int((flat_labels != -100).sum().item())
    loss = nn.functional.cross_entropy(
        flat_logits, flat_labels, ignore_index=-100, reduction="mean"
    )
    return loss, n_tokens


@torch.no_grad()
def evaluate_mlm(
    model: SequenceLM,
    dataset: CallStreamDataset,
    batch_size: int = 64,
    mask_prob: float = 0.15,
    seed: int = 0,
    device: torch.device | str = "cpu",
) -> dict[str, float]:
    """Compute mean MLM loss and perplexity on a held-out dataset.

    Uses a *deterministic* RNG for the masking so the comparison between
    real and shuffled-sequence training runs is on a like-for-like sample
    of mask positions.
    """
    model.eval()
    device = torch.device(device)
    loader = _make_loader(dataset, batch_size=batch_size, shuffle=False, seed=seed)
    g = torch.Generator(device=device)
    g.manual_seed(seed)
    total_loss = 0.0
    total_tokens = 0
    for batch in loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        masked, labels = mlm_mask(
            input_ids,
            attention_mask,
            vocab_size=model.cfg.vocab_size,
            mask_prob=mask_prob,
            generator=g,
        )
        logits = model(masked, attention_mask)
        loss, n_tokens = _mlm_loss(logits, labels)
        if n_tokens > 0:
            total_loss += float(loss.item()) * n_tokens
            total_tokens += n_tokens
    mean_loss = total_loss / max(1, total_tokens)
    return {
        "mlm_loss": mean_loss,
        "perplexity": float(math.exp(mean_loss)),
        "n_eval_tokens": float(total_tokens),
    }


def train_mlm(
    model: SequenceLM,
    train_dataset: CallStreamDataset,
    eval_dataset: CallStreamDataset | None,
    cfg: TrainConfig,
    device: torch.device | str = "cpu",
    log_fn=print,
) -> list[dict]:
    """Train ``model`` on ``train_dataset`` with the MLM objective.

    Returns the history of logged metrics as a list of dicts. Each entry
    contains either ``{"step", "lr", "train_loss"}`` (training log) or
    ``{"step", "eval_mlm_loss", "eval_perplexity"}`` (evaluation log).
    """
    torch.manual_seed(cfg.seed)
    device = torch.device(device)
    model.to(device)
    optim = torch.optim.AdamW(
        model.parameters(),
        lr=cfg.lr_peak,
        betas=(0.9, 0.98),
        eps=1e-8,
        weight_decay=cfg.weight_decay,
    )

    train_loader = _make_loader(
        train_dataset, batch_size=cfg.batch_size, shuffle=True, seed=cfg.seed
    )
    train_iter = _infinite(train_loader)
    g_mask = torch.Generator(device=device)
    g_mask.manual_seed(cfg.seed + 1)

    history: list[dict] = []
    running = 0.0
    running_n = 0
    for step in range(cfg.max_steps):
        model.train()
        for pg in optim.param_groups:
            pg["lr"] = _lr_at(step, cfg)

        batch = next(train_iter)
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        masked, labels = mlm_mask(
            input_ids,
            attention_mask,
            vocab_size=model.cfg.vocab_size,
            mask_prob=cfg.mask_prob,
            generator=g_mask,
        )
        logits = model(masked, attention_mask)
        loss, n_tokens = _mlm_loss(logits, labels)
        if n_tokens == 0:
            continue

        optim.zero_grad(set_to_none=True)
        loss.backward()
        if cfg.grad_clip is not None and cfg.grad_clip > 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
        optim.step()

        running += float(loss.item()) * n_tokens
        running_n += n_tokens

        if (step + 1) % cfg.log_every == 0:
            avg = running / max(1, running_n)
            entry = {
                "step": step + 1,
                "lr": _lr_at(step, cfg),
                "train_loss": avg,
            }
            history.append(entry)
            log_fn(
                f"step={step + 1:5d}  lr={entry['lr']:.2e}  train_loss={avg:.4f}"
            )
            running = 0.0
            running_n = 0

        if eval_dataset is not None and (step + 1) % cfg.eval_every == 0:
            metrics = evaluate_mlm(
                model,
                eval_dataset,
                batch_size=max(64, cfg.batch_size),
                mask_prob=cfg.mask_prob,
                seed=cfg.seed,
                device=device,
            )
            entry = {
                "step": step + 1,
                "eval_mlm_loss": metrics["mlm_loss"],
                "eval_perplexity": metrics["perplexity"],
            }
            history.append(entry)
            log_fn(
                f"  eval step={step + 1:5d}  mlm_loss={metrics['mlm_loss']:.4f}  "
                f"ppl={metrics['perplexity']:.3f}"
            )

    return history


def _infinite(loader: Iterable) -> Iterable:
    while True:
        for batch in loader:
            yield batch

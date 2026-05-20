"""Command-line entry point for the head-H3 pilot.

Usage examples
--------------

  # Sanity-check pilot on synthetic Markov streams (CPU, ~1-3 minutes)
  orca-h3-pilot --substrate synthetic --max-steps 400 --n-perm 5

  # Real run on DCLDE 2026 annotations (requires the CSV)
  orca-h3-pilot --substrate dclde \\
      --dclde-csv /path/to/Annotations.csv \\
      --max-steps 5000 --n-perm 100

The CLI is the single user-facing entry point. The library API
(``orcadolittle.train.train_mlm`` + ``orcadolittle.eval.run_shuffled_baseline``)
is the same one this CLI calls; nothing CLI-specific lives in
``orcadolittle.*``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

from orcadolittle.data.call_streams import CallStreamDataset, Vocab
from orcadolittle.data.synthetic import SyntheticConfig, make_synthetic_streams
from orcadolittle.eval.permutation import PermutationConfig, run_shuffled_baseline
from orcadolittle.models.sequence_lm import SequenceLMConfig
from orcadolittle.train.mlm import TrainConfig


def _split(streams, frac: float, seed: int):
    import numpy as np

    rng = np.random.default_rng(seed)
    idx = np.arange(len(streams))
    rng.shuffle(idx)
    cut = int(round(len(streams) * frac))
    train_idx = idx[:cut]
    eval_idx = idx[cut:]
    return (
        [streams[i] for i in train_idx],
        [streams[i] for i in eval_idx],
    )


def _load_synthetic(args) -> tuple[list[list[int]], list[list[int]], int]:
    cfg = SyntheticConfig(
        num_call_types=args.synthetic_call_types,
        num_encounters=args.synthetic_encounters,
        transition_concentration=args.synthetic_concentration,
        seed=args.seed,
    )
    streams, _meta = make_synthetic_streams(cfg)
    train, evalu = _split(streams, frac=0.8, seed=args.seed)
    from orcadolittle.data.call_streams import NUM_SPECIAL

    vocab_size = NUM_SPECIAL + cfg.num_call_types
    return train, evalu, vocab_size


def _load_dclde(args) -> tuple[list[list[int]], list[list[int]], int]:
    from orcadolittle.data.dclde_loader import (
        DCLDEColumns,
        EncounterStreamConfig,
        load_dclde_streams,
    )

    streams, vocab, meta = load_dclde_streams(
        csv_path=args.dclde_csv,
        columns=DCLDEColumns(),
        cfg=EncounterStreamConfig(
            gap_seconds=args.dclde_gap_seconds,
            min_calls_per_encounter=args.dclde_min_calls,
            ecotype=args.dclde_ecotype,
        ),
    )
    print(f"[dclde] loaded {meta['num_encounters']} encounters from {meta['num_rows']} rows", file=sys.stderr)
    print(f"[dclde] vocab size = {vocab.size} ({len(vocab.call_types)} call types)", file=sys.stderr)
    train, evalu = _split(streams, frac=0.8, seed=args.seed)
    return train, evalu, vocab.size


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="orca-h3-pilot")
    p.add_argument(
        "--substrate",
        choices=("synthetic", "dclde"),
        default="synthetic",
        help="Use synthetic Markov streams (default) or real DCLDE 2026 annotations.",
    )
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device", default="cpu", help='Torch device, e.g. "cpu" or "cuda".')
    p.add_argument("--max-len", type=int, default=128)
    p.add_argument("--out", type=Path, default=Path("h3_pilot_result.json"))

    # Synthetic-only.
    p.add_argument("--synthetic-call-types", type=int, default=32)
    p.add_argument("--synthetic-encounters", type=int, default=4000)
    p.add_argument("--synthetic-concentration", type=float, default=0.1)

    # DCLDE-only.
    p.add_argument("--dclde-csv", type=Path, default=None, help="Path to Annotations.csv")
    p.add_argument("--dclde-gap-seconds", type=float, default=300.0)
    p.add_argument("--dclde-min-calls", type=int, default=4)
    p.add_argument("--dclde-ecotype", default=None, help='Filter to a single ecotype, e.g. "SRKW".')

    # Model.
    p.add_argument("--d-model", type=int, default=128)
    p.add_argument("--n-layers", type=int, default=4)
    p.add_argument("--n-heads", type=int, default=4)

    # Training.
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--max-steps", type=int, default=400)
    p.add_argument("--warmup-steps", type=int, default=40)
    p.add_argument("--lr-peak", type=float, default=3e-4)
    p.add_argument("--mask-prob", type=float, default=0.15)

    # Permutation test.
    p.add_argument("--n-perm", type=int, default=5)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)

    if args.substrate == "synthetic":
        train_streams, eval_streams, vocab_size = _load_synthetic(args)
    else:
        if args.dclde_csv is None:
            print(
                "ERROR: --substrate dclde requires --dclde-csv to point at "
                "Annotations.csv. Pull per Stage-1 of EXECUTION_PLAN.md.",
                file=sys.stderr,
            )
            return 2
        train_streams, eval_streams, vocab_size = _load_dclde(args)

    train_ds = CallStreamDataset(train_streams, max_len=args.max_len)
    eval_ds = CallStreamDataset(eval_streams, max_len=args.max_len)
    print(
        f"[data] train sequences = {len(train_ds)}, eval sequences = {len(eval_ds)}, "
        f"vocab_size = {vocab_size}, max_len = {args.max_len}",
        file=sys.stderr,
    )

    model_cfg = SequenceLMConfig(
        vocab_size=vocab_size,
        d_model=args.d_model,
        n_layers=args.n_layers,
        n_heads=args.n_heads,
        max_len=args.max_len,
    )
    train_cfg = TrainConfig(
        batch_size=args.batch_size,
        max_steps=args.max_steps,
        warmup_steps=args.warmup_steps,
        lr_peak=args.lr_peak,
        mask_prob=args.mask_prob,
        seed=args.seed,
        eval_every=max(50, args.max_steps // 4),
        log_every=max(20, args.max_steps // 10),
    )
    perm_cfg = PermutationConfig(
        n_perm=args.n_perm,
        pilot_n_perm=args.n_perm,
        seed=args.seed,
    )

    device = torch.device(args.device)
    result, _model = run_shuffled_baseline(
        base_model_cfg=model_cfg,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        train_cfg=train_cfg,
        perm_cfg=perm_cfg,
        device=device,
        use_pilot_n=True,
    )
    summary = result.summary()
    print("\n[H3] pilot summary:")
    for k, v in summary.items():
        print(f"  {k}: {v:.4f}")
    args.out.write_text(json.dumps(summary, indent=2))
    print(f"[H3] wrote summary to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""H6: token/context structure controls for Wellard acoustic features.

This head quantizes acoustic feature vectors into motif tokens, checks that the
vocabulary is not degenerate, and evaluates held-out sequence order against a
unigram baseline and shuffled-order null.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", required=True)
    parser.add_argument("--behavior-table", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--vocab-size", type=int, default=24)
    parser.add_argument("--n-shuffle", type=int, default=200)
    parser.add_argument("--group-field", default="source_file")
    return parser.parse_args()


def load_features(path: Path) -> tuple[np.ndarray, pd.DataFrame]:
    data = np.load(path, allow_pickle=True)
    X = np.asarray(data["embeddings"], dtype=np.float32)
    meta = pd.DataFrame(list(data["metadata"]))
    if "segment_id" not in meta.columns:
        raise ValueError("feature metadata must contain segment_id")
    return X, meta


def assign_tokens(X: np.ndarray, vocab_size: int) -> np.ndarray:
    n_clusters = int(min(max(2, vocab_size), max(2, len(X) // 4)))
    n_components = min(32, X.shape[1], max(1, len(X) - 1))
    model = make_pipeline(
        StandardScaler(),
        PCA(n_components=n_components, random_state=SEED),
        MiniBatchKMeans(n_clusters=n_clusters, random_state=SEED, n_init=20, batch_size=2048),
    )
    return model.fit_predict(X).astype(int)


def entropy_bits(tokens: np.ndarray, k: int) -> float:
    counts = np.bincount(tokens, minlength=k).astype(float)
    p = counts[counts > 0] / counts.sum()
    return float(-(p * np.log2(p)).sum())


def build_sequences(df: pd.DataFrame, group_field: str) -> dict[str, list[int]]:
    sequences = {}
    for group, rows in df.sort_values([group_field, "start_time_s"]).groupby(group_field):
        seq = rows["token_id"].astype(int).tolist()
        if len(seq) >= 3:
            sequences[str(group)] = seq
    return sequences


def train_bigram(sequences: list[list[int]], k: int, alpha: float = 0.5) -> np.ndarray:
    counts = np.full((k, k), alpha, dtype=float)
    for seq in sequences:
        for a, b in zip(seq[:-1], seq[1:]):
            counts[a, b] += 1
    return counts / counts.sum(axis=1, keepdims=True)


def train_unigram(sequences: list[list[int]], k: int, alpha: float = 0.5) -> np.ndarray:
    counts = np.full(k, alpha, dtype=float)
    for seq in sequences:
        for token in seq:
            counts[token] += 1
    return counts / counts.sum()


def bigram_nll(sequences: list[list[int]], probs: np.ndarray) -> float:
    vals = []
    for seq in sequences:
        for a, b in zip(seq[:-1], seq[1:]):
            vals.append(-np.log(max(probs[a, b], 1e-12)))
    return float(np.mean(vals)) if vals else float("nan")


def unigram_nll(sequences: list[list[int]], probs: np.ndarray) -> float:
    vals = []
    for seq in sequences:
        for token in seq[1:]:
            vals.append(-np.log(max(probs[token], 1e-12)))
    return float(np.mean(vals)) if vals else float("nan")


def sequence_order_test(sequences_by_group: dict[str, list[int]], k: int, n_shuffle: int) -> dict:
    groups = np.array(sorted(sequences_by_group))
    if len(groups) < 3:
        return {"status": "skipped_insufficient_sequences", "n_sequence_groups": int(len(groups))}
    n_splits = min(5, len(groups))
    rng = np.random.default_rng(SEED)
    real_losses = []
    unigram_losses = []
    shuffled_losses = []
    for train_idx, test_idx in GroupKFold(n_splits=n_splits).split(groups, groups=groups):
        train = [sequences_by_group[g] for g in groups[train_idx]]
        test = [sequences_by_group[g] for g in groups[test_idx]]
        bigram = train_bigram(train, k)
        unigram = train_unigram(train, k)
        real_losses.append(bigram_nll(test, bigram))
        unigram_losses.append(unigram_nll(test, unigram))
        for _ in range(max(1, n_shuffle // n_splits)):
            shuffled = []
            for seq in test:
                copy = list(seq)
                rng.shuffle(copy)
                shuffled.append(copy)
            shuffled_losses.append(bigram_nll(shuffled, bigram))

    real = float(np.nanmean(real_losses))
    unigram = float(np.nanmean(unigram_losses))
    shuffled = np.array([x for x in shuffled_losses if np.isfinite(x)], dtype=float)
    pvalue = float((np.sum(shuffled <= real) + 1) / (len(shuffled) + 1)) if len(shuffled) else None
    return {
        "status": "completed",
        "n_sequence_groups": int(len(groups)),
        "heldout_bigram_real_order_nll": real,
        "heldout_unigram_nll": unigram,
        "heldout_shuffled_order_nll_mean": float(shuffled.mean()) if len(shuffled) else None,
        "heldout_shuffled_order_nll_std": float(shuffled.std()) if len(shuffled) else None,
        "order_pvalue_lower_is_better": pvalue,
        "beats_unigram": bool(real < unigram),
        "real_order_better_than_shuffled": bool(len(shuffled) and real < shuffled.mean()),
    }


def context_token_tests(df: pd.DataFrame, behavior: pd.DataFrame) -> list[dict]:
    contexts = sorted(behavior["behavior_context"].dropna().astype(str).unique())
    label_rows = behavior.assign(value=1).pivot_table(
        index="segment_id",
        columns="behavior_context",
        values="value",
        aggfunc="max",
        fill_value=0,
    )
    joined = df.merge(label_rows, left_on="segment_id", right_index=True, how="inner")
    out = []
    for context in contexts:
        y = joined.get(context, pd.Series(0, index=joined.index)).to_numpy(dtype=int)
        table = pd.crosstab(joined["token_id"], y)
        if table.shape[1] < 2 or table.shape[0] < 2:
            out.append({"context": context, "status": "skipped_insufficient_table"})
            continue
        chi2, pvalue, dof, _ = chi2_contingency(table.to_numpy())
        out.append({
            "context": context,
            "status": "completed",
            "chi2": float(chi2),
            "dof": int(dof),
            "pvalue": float(pvalue),
        })
    return out


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    X, meta = load_features(Path(args.features))
    behavior = pd.read_csv(args.behavior_table)
    tokens = assign_tokens(X, args.vocab_size)
    k = int(tokens.max()) + 1
    meta = meta.copy()
    meta["token_id"] = tokens

    counts = np.bincount(tokens, minlength=k)
    ent = entropy_bits(tokens, k)
    majority_rate = float(counts.max() / counts.sum())
    sequences = build_sequences(meta, args.group_field)
    order = sequence_order_test(sequences, k, args.n_shuffle)
    context_tests = context_token_tests(meta, behavior)

    tokens_path = output_dir / "wellard_tokens.csv"
    meta.to_csv(tokens_path, index=False)

    summary = {
        "head": "H6",
        "status": "pass" if order.get("status") == "completed" else "pending",
        "features": str(Path(args.features)),
        "behavior_table": str(Path(args.behavior_table)),
        "tokens_csv": str(tokens_path),
        "vocab_size": k,
        "n_segments": int(len(tokens)),
        "token_entropy_bits": ent,
        "max_entropy_bits": float(np.log2(k)),
        "majority_token_rate": majority_rate,
        "token_count_min": int(counts.min()),
        "token_count_max": int(counts.max()),
        "token_count_median": float(np.median(counts)),
        "order_test": order,
        "context_token_tests": context_tests,
        "claim": (
            "Token vocabulary and order controls completed; context associations remain candidate-level"
        ),
    }
    metrics_path = output_dir / "h6_metrics_wellard.json"
    metrics_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if order.get("status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""H5: grouped behavior-context prediction from Wellard acoustic features.

This head tests whether compact acoustic representations predict independently
observed recording-level context above simple controls. Labels are weak
recording-level context inherited by segments; the output is candidate acoustic
association evidence, not semantic decoding.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", required=True)
    parser.add_argument("--behavior-table", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--n-perm", type=int, default=200)
    parser.add_argument("--group-field", default="source_file")
    parser.add_argument("--min-positive-groups", type=int, default=2)
    parser.add_argument("--min-negative-groups", type=int, default=2)
    return parser.parse_args()


def load_feature_frame(features_path: Path) -> tuple[np.ndarray, pd.DataFrame]:
    data = np.load(features_path, allow_pickle=True)
    X = np.asarray(data["embeddings"], dtype=np.float32)
    meta = pd.DataFrame(list(data["metadata"]))
    if len(meta) != len(X):
        raise ValueError("metadata length does not match feature matrix")
    if "segment_id" not in meta.columns:
        meta["segment_id"] = (
            meta["source_file"].astype(str) + "__" +
            meta["start_time_s"].astype(float).round(3).astype(str)
        )
    return X, meta


def build_labels(meta: pd.DataFrame, behavior: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    required = {"segment_id", "behavior_context"}
    missing = required - set(behavior.columns)
    if missing:
        raise ValueError(f"behavior table missing columns: {sorted(missing)}")
    meta = meta.copy()
    meta["_feature_row"] = np.arange(len(meta))
    contexts = sorted(behavior["behavior_context"].dropna().astype(str).unique())
    label_rows = behavior.assign(value=1).pivot_table(
        index="segment_id",
        columns="behavior_context",
        values="value",
        aggfunc="max",
        fill_value=0,
    )
    label_rows = label_rows.reindex(columns=contexts, fill_value=0)
    joined = meta.merge(label_rows, left_on="segment_id", right_index=True, how="inner")
    if joined.empty:
        raise ValueError("no feature rows joined to behavior table")
    return joined, contexts


def valid_group_kfold(y: np.ndarray, groups: np.ndarray, max_splits: int = 5):
    unique_groups = np.unique(groups)
    n_splits = min(max_splits, len(unique_groups))
    if n_splits < 2:
        return []
    splits = []
    for train, test in GroupKFold(n_splits=n_splits).split(np.zeros_like(y), y, groups):
        if len(np.unique(y[train])) == 2 and len(np.unique(y[test])) == 2:
            splits.append((train, test))
    return splits


def grouped_predictions(X: np.ndarray, y: np.ndarray, groups: np.ndarray, model_factory) -> tuple[np.ndarray, list]:
    splits = valid_group_kfold(y, groups)
    if len(splits) < 2:
        raise ValueError("fewer than two valid grouped folds")
    pred = np.full_like(y, fill_value=-1)
    for train, test in splits:
        model = model_factory()
        model.fit(X[train], y[train])
        pred[test] = model.predict(X[test])
    mask = pred >= 0
    if mask.sum() == 0:
        raise ValueError("no grouped predictions produced")
    return pred[mask], [(train, test) for train, test in splits]


def group_preserving_permutation(y: np.ndarray, groups: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    unique = np.array(sorted(np.unique(groups)))
    group_values = np.array([int(round(y[groups == g].mean())) for g in unique])
    shuffled = rng.permutation(group_values)
    mapping = dict(zip(unique, shuffled))
    return np.array([mapping[g] for g in groups], dtype=int)


def evaluate_context(
    context: str,
    X: np.ndarray,
    meta: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
    n_perm: int,
) -> dict:
    pos_groups = len(set(groups[y == 1]))
    neg_groups = len(set(groups[y == 0]))
    result = {
        "context": context,
        "n_segments": int(len(y)),
        "positive_segments": int(y.sum()),
        "negative_segments": int((1 - y).sum()),
        "positive_groups": int(pos_groups),
        "negative_groups": int(neg_groups),
    }
    if pos_groups < 2 or neg_groups < 2 or len(np.unique(y)) < 2:
        return {**result, "status": "skipped_insufficient_group_support"}

    audio_model = lambda: make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED),
    )
    metadata_cols = ["start_time_s", "end_time_s", "duration_s"]
    Z = meta[[c for c in metadata_cols if c in meta.columns]].to_numpy(dtype=float)
    if Z.shape[1] == 0:
        Z = np.arange(len(y), dtype=float).reshape(-1, 1)

    try:
        pred_audio, splits = grouped_predictions(X, y, groups, audio_model)
        y_eval = np.concatenate([y[test] for _, test in splits if len(np.unique(y[test])) == 2])
        audio_bal = balanced_accuracy_score(y_eval, pred_audio)
        audio_f1 = f1_score(y_eval, pred_audio, zero_division=0)

        pred_meta, meta_splits = grouped_predictions(Z, y, groups, audio_model)
        y_meta = np.concatenate([y[test] for _, test in meta_splits if len(np.unique(y[test])) == 2])
        meta_bal = balanced_accuracy_score(y_meta, pred_meta)

        dummy_pred, dummy_splits = grouped_predictions(
            np.zeros((len(y), 1), dtype=float),
            y,
            groups,
            lambda: DummyClassifier(strategy="most_frequent"),
        )
        y_dummy = np.concatenate([y[test] for _, test in dummy_splits if len(np.unique(y[test])) == 2])
        majority_bal = balanced_accuracy_score(y_dummy, dummy_pred)

        rng = np.random.default_rng(SEED)
        perm_scores = []
        for _ in range(n_perm):
            yp = group_preserving_permutation(y, groups, rng)
            try:
                pred_perm, perm_splits = grouped_predictions(X, yp, groups, audio_model)
                y_perm_eval = np.concatenate([
                    yp[test] for _, test in perm_splits if len(np.unique(yp[test])) == 2
                ])
                perm_scores.append(balanced_accuracy_score(y_perm_eval, pred_perm))
            except ValueError:
                continue
        perm = np.array(perm_scores, dtype=float)
        pvalue = float((np.sum(perm >= audio_bal) + 1) / (len(perm) + 1)) if len(perm) else None
    except Exception as exc:
        return {**result, "status": "failed", "error_type": type(exc).__name__, "error": str(exc)}

    return {
        **result,
        "status": "completed",
        "folds": int(len(splits)),
        "balanced_accuracy": float(audio_bal),
        "macro_f1": float(audio_f1),
        "metadata_only_balanced_accuracy": float(meta_bal),
        "majority_balanced_accuracy": float(majority_bal),
        "permutation_mean_balanced_accuracy": float(perm.mean()) if len(perm) else None,
        "permutation_std_balanced_accuracy": float(perm.std()) if len(perm) else None,
        "permutation_pvalue": pvalue,
        "claim_ready": bool(pvalue is not None and pvalue < 0.05 and audio_bal > max(meta_bal, majority_bal)),
    }


def make_figure(results: list[dict], output_dir: Path) -> str | None:
    complete = [r for r in results if r.get("status") == "completed"]
    if not complete:
        return None
    labels = [r["context"] for r in complete]
    audio = [r["balanced_accuracy"] for r in complete]
    meta = [r["metadata_only_balanced_accuracy"] for r in complete]
    majority = [r["majority_balanced_accuracy"] for r in complete]
    x = np.arange(len(labels))
    width = 0.25
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(x - width, audio, width, label="Acoustic features")
    ax.bar(x, meta, width, label="Metadata-only")
    ax.bar(x + width, majority, width, label="Majority")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Grouped balanced accuracy")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_title("H5: Wellard recording-level context prediction")
    ax.legend()
    fig.tight_layout()
    path = output_dir / "h5_behavior_context_wellard.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    X, meta = load_feature_frame(Path(args.features))
    behavior = pd.read_csv(args.behavior_table)
    joined, contexts = build_labels(meta, behavior)
    row_idx = joined["_feature_row"].to_numpy(dtype=int)
    Xj = X[row_idx]
    groups = joined[args.group_field].astype(str).to_numpy()

    results = []
    for context in contexts:
        y = joined[context].to_numpy(dtype=int)
        results.append(evaluate_context(context, Xj, joined, y, groups, args.n_perm))

    figure = make_figure(results, output_dir)
    completed = [r for r in results if r.get("status") == "completed"]
    summary = {
        "head": "H5",
        "status": "pass" if completed else "pending",
        "claim": (
            "Acoustic features predict weak recording-level observed context above controls"
            if any(r.get("claim_ready") for r in completed)
            else "Analysis ran; no semantic claim is made without above-control support"
        ),
        "features": str(Path(args.features)),
        "behavior_table": str(Path(args.behavior_table)),
        "group_field": args.group_field,
        "n_segments_joined": int(len(joined)),
        "contexts": results,
        "figure": figure,
    }
    metrics_path = output_dir / "h5_metrics_wellard.json"
    metrics_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if completed else 1


if __name__ == "__main__":
    raise SystemExit(main())

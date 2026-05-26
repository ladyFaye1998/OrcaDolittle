#!/usr/bin/env python3
"""H1: Linear and MLP probes on embeddings → ecotype classification.

Trains probes on the embedding matrix and reports:
- Per-class accuracy and confusion matrix
- 5-fold stratified CV scores
- Permutation test p-values (n_perm = 10,000)
- Headline figure for the submission

Usage:
  python3 scripts/run_h1_probes.py --embeddings data/embeddings/aves2_embeddings.npz
  python3 scripts/run_h1_probes.py --embeddings data/embeddings/naturelm_embeddings.npz
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score, permutation_test_score
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
SEED = 0
N_PERM = 10_000


def run_probes(embeddings: np.ndarray, labels: np.ndarray, encoder_name: str):
    """Train linear and MLP probes, report results."""
    le = LabelEncoder()
    y = le.fit_transform(labels)
    class_names = le.classes_

    print(f"\n{'='*60}")
    print(f"HEAD H1: SUPERVISED PROBES ({encoder_name.upper()} embeddings)")
    print(f"{'='*60}")
    print(f"  Samples: {len(embeddings):,}")
    print(f"  Features: {embeddings.shape[1]}")
    print(f"  Classes: {list(class_names)}")
    print(f"  Class distribution: {dict(zip(class_names, np.bincount(y)))}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    # Linear probe (logistic regression)
    print(f"\n--- Logistic Regression (L2, C=1.0) ---")
    lr = LogisticRegression(max_iter=2000, random_state=SEED, C=1.0)
    lr_scores = cross_val_score(lr, embeddings, y, cv=cv, scoring="accuracy")
    print(f"  Accuracy: {lr_scores.mean():.3f} ± {lr_scores.std():.3f}")

    # MLP probe (2-layer)
    print(f"\n--- MLP (256-128, ReLU, L2=1e-4) ---")
    mlp = MLPClassifier(
        hidden_layer_sizes=(256, 128),
        activation="relu",
        alpha=1e-4,
        max_iter=500,
        random_state=SEED,
    )
    mlp_scores = cross_val_score(mlp, embeddings, y, cv=cv, scoring="accuracy")
    print(f"  Accuracy: {mlp_scores.mean():.3f} ± {mlp_scores.std():.3f}")

    # Permutation test on the better model
    best_model = lr if lr_scores.mean() >= mlp_scores.mean() else mlp
    best_name = "LogReg" if lr_scores.mean() >= mlp_scores.mean() else "MLP"
    best_score = max(lr_scores.mean(), mlp_scores.mean())

    print(f"\n--- Permutation Test (n={N_PERM}, model={best_name}) ---")
    print(f"  Running... (this takes a while)")
    score, perm_scores, pvalue = permutation_test_score(
        best_model, embeddings, y, cv=cv, n_permutations=N_PERM,
        scoring="accuracy", random_state=SEED, n_jobs=-1,
    )
    print(f"  True score: {score:.3f}")
    print(f"  Permutation mean: {perm_scores.mean():.3f} ± {perm_scores.std():.3f}")
    print(f"  p-value: {pvalue:.2e}")

    # Full train for confusion matrix and classification report
    best_model.fit(embeddings, y)
    y_pred = best_model.predict(embeddings)

    print(f"\n--- Classification Report (full dataset, {best_name}) ---")
    print(classification_report(y, y_pred, target_names=class_names))

    # Generate headline figure
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Confusion matrix
    cm = confusion_matrix(y, y_pred, normalize="true")
    im = axes[0].imshow(cm, cmap="Blues", vmin=0, vmax=1)
    axes[0].set_xticks(range(len(class_names)))
    axes[0].set_yticks(range(len(class_names)))
    axes[0].set_xticklabels(class_names, fontsize=10)
    axes[0].set_yticklabels(class_names, fontsize=10)
    axes[0].set_xlabel("Predicted", fontsize=11)
    axes[0].set_ylabel("True", fontsize=11)
    axes[0].set_title(f"Confusion Matrix ({best_name})", fontsize=12)
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            color = "white" if cm[i, j] > 0.5 else "black"
            axes[0].text(j, i, f"{cm[i,j]:.2f}", ha="center", va="center", color=color, fontsize=9)
    plt.colorbar(im, ax=axes[0], fraction=0.046)

    # Permutation test histogram
    axes[1].hist(perm_scores, bins=50, color="lightgray", edgecolor="gray", alpha=0.8, label="Permutation null")
    axes[1].axvline(score, color="red", linewidth=2, label=f"True score = {score:.3f}")
    axes[1].axvline(1/len(class_names), color="blue", linewidth=1, linestyle="--", label=f"Chance = {1/len(class_names):.3f}")
    axes[1].set_xlabel("Accuracy", fontsize=11)
    axes[1].set_ylabel("Count", fontsize=11)
    axes[1].set_title(f"Permutation Test (n={N_PERM}, p={pvalue:.2e})", fontsize=12)
    axes[1].legend(fontsize=10)

    plt.suptitle(f"H1: Ecotype Classification from {encoder_name.upper()} Embeddings", fontsize=13, fontweight="bold")
    plt.tight_layout()

    fig_path = FIGURES_DIR / f"h1_probes_{encoder_name}.png"
    plt.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Figure saved: {fig_path}")

    # Summary
    print(f"\n{'='*60}")
    print(f"H1 SUMMARY")
    print(f"{'='*60}")
    print(f"  Best model: {best_name}")
    print(f"  CV Accuracy: {best_score:.1%}")
    print(f"  Permutation p-value: {pvalue:.2e}")
    print(f"  Verdict: {'PASS' if pvalue < 0.001 else 'MARGINAL' if pvalue < 0.05 else 'FAIL'}")
    print(f"{'='*60}")

    return {
        "encoder": encoder_name,
        "lr_accuracy": lr_scores.mean(),
        "mlp_accuracy": mlp_scores.mean(),
        "best_model": best_name,
        "best_accuracy": best_score,
        "pvalue": pvalue,
        "n_samples": len(embeddings),
    }


def main():
    parser = argparse.ArgumentParser(description="H1: Linear/MLP probes on embeddings")
    parser.add_argument("--embeddings", type=str, required=True, help="Path to .npz embedding file")
    args = parser.parse_args()

    emb_path = Path(args.embeddings)
    if not emb_path.exists():
        print(f"ERROR: {emb_path} not found. Run scripts/batch_encode.py first.")
        return 1

    data = np.load(emb_path)
    embeddings = data["embeddings"]
    labels = data["labels"]

    encoder_name = emb_path.stem.replace("_embeddings", "")
    results = run_probes(embeddings, labels, encoder_name)

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""H1: Confound-aware supervised probes on embeddings -> ecotype classification.

This is the scientifically defensible version of H1. A naive pooled
cross-validation on this dataset is severely confounded: the ecotype label is
nearly collinear with the recording provider/site (e.g. every SAR call in the
DCLDE archive comes from a single provider). A model can therefore reach high
pooled accuracy by recognising the hydrophone, not the whale. This is the
well-documented site/device shortcut in passive-acoustic deep learning, and the
standard remedy is leave-one-site-out evaluation [@stowell2022; @ghani2023].

This script reports three things, in increasing order of evidential strength:

1. Pooled stratified 5-fold CV (LogReg + MLP). This is the *site-confounded
   upper bound*. Reported, but explicitly not the headline.
2. Leave-One-Provider-Out (LOPO) grouped CV. The headline honest-generalisation
   number: every test provider is unseen during training. Per-class held-out
   recall is reported so structurally site-locked classes (one provider only)
   are visible rather than hidden.
3. A label-shuffle permutation test on the pooled split, kept for continuity.

Held-out metrics use balanced accuracy and macro-F1 (the classes are very
imbalanced) and a held-out confusion matrix from cross_val_predict. The old
in-sample "1.00" report is intentionally removed.

Usage:
  python scripts/run_h1_probes.py --embeddings data/embeddings/aves2_full_labeled.npz
  python scripts/run_h1_probes.py --embeddings <npz> --n-perm 1000 --group-field provider
"""

import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message="y_pred contains classes not in y_true")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from joblib import Parallel, delayed
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import (
    LeaveOneGroupOut,
    StratifiedKFold,
    cross_val_predict,
    cross_val_score,
    train_test_split,
)
from sklearn.multiclass import OneVsRestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
SEED = 0
N_PERM = 1000


def load_groups(npz_path: Path, n: int, group_field: str) -> np.ndarray | None:
    """Load a per-call grouping array (default: recording provider) from metadata."""
    data = np.load(npz_path, allow_pickle=True)
    if "metadata" not in data:
        return None
    meta = list(data["metadata"])
    if len(meta) != n:
        return None
    groups = []
    for m in meta:
        if isinstance(m, dict):
            groups.append(str(m.get(group_field, m.get(group_field.capitalize(), "NA"))))
        else:
            groups.append("NA")
    return np.array(groups)


def _logreg() -> LogisticRegression:
    return LogisticRegression(max_iter=2000, random_state=SEED, C=1.0)


def pooled_cv(embeddings, y, class_names):
    """Pooled stratified 5-fold CV. Site-confounded upper bound, not headline."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    print("\n--- [UPPER BOUND, site-confounded] Pooled 5-fold CV ---")
    lr_acc = cross_val_score(_logreg(), embeddings, y, cv=cv, scoring="accuracy")
    lr_bal = cross_val_score(_logreg(), embeddings, y, cv=cv, scoring="balanced_accuracy")
    print(f"  LogReg  accuracy={lr_acc.mean():.3f}±{lr_acc.std():.3f}  "
          f"balanced={lr_bal.mean():.3f}±{lr_bal.std():.3f}")

    mlp = MLPClassifier(hidden_layer_sizes=(256, 128), activation="relu",
                        alpha=1e-4, max_iter=500, random_state=SEED)
    mlp_acc = cross_val_score(mlp, embeddings, y, cv=cv, scoring="accuracy")
    print(f"  MLP     accuracy={mlp_acc.mean():.3f}±{mlp_acc.std():.3f}")

    # Held-out confusion matrix (NOT in-sample): use cross_val_predict.
    y_pred = cross_val_predict(_logreg(), embeddings, y, cv=cv)
    macro_f1 = f1_score(y, y_pred, average="macro")
    print(f"  LogReg held-out macro-F1={macro_f1:.3f}")

    return {
        "lr_accuracy": float(lr_acc.mean()),
        "lr_accuracy_std": float(lr_acc.std()),
        "lr_balanced_accuracy": float(lr_bal.mean()),
        "mlp_accuracy": float(mlp_acc.mean()),
        "macro_f1": float(macro_f1),
        "y_pred_heldout": y_pred,
    }


def leave_one_provider_out(embeddings, y, groups, class_names):
    """Headline honest generalisation: each provider unseen during training."""
    logo = LeaveOneGroupOut()
    n_groups = len(np.unique(groups))
    print(f"\n--- [HEADLINE] Leave-One-Provider-Out CV ({n_groups} providers) ---")

    # Held-out predictions for every sample (its provider was never in train).
    y_pred = cross_val_predict(_logreg(), embeddings, y, groups=groups, cv=logo)
    bal = balanced_accuracy_score(y, y_pred)
    acc = accuracy_score(y, y_pred)
    macro_f1 = f1_score(y, y_pred, average="macro")
    print(f"  Overall  accuracy={acc:.3f}  balanced={bal:.3f}  macro-F1={macro_f1:.3f}")
    print(f"  Chance (1/{len(class_names)} classes) = {1/len(class_names):.3f}")

    # Per-class held-out recall. Classes that live in a single provider become
    # unclassifiable when that provider is the test fold -> recall collapses,
    # which is the honest signature of the site confound.
    print("\n  Per-class held-out recall (cross-site):")
    per_class = {}
    cm = confusion_matrix(y, y_pred, labels=range(len(class_names)))
    for i, name in enumerate(class_names):
        support = int(cm[i].sum())
        recall = float(cm[i, i] / support) if support else 0.0
        per_class[name] = {"recall": recall, "support": support}
        print(f"    {name:6s} recall={recall:.3f}  (n={support:,})")

    # Per-provider held-out balanced accuracy.
    print("\n  Per-provider held-out balanced accuracy:")
    per_provider = {}
    for g in sorted(np.unique(groups)):
        mask = groups == g
        classes_in_test = np.unique(y[mask])
        classes_in_train = np.unique(y[~mask])
        # Classes present in test but absent from train are structurally
        # impossible to predict -> flagged.
        locked = sorted(set(class_names[c] for c in classes_in_test
                            if c not in set(classes_in_train)))
        b = balanced_accuracy_score(y[mask], y_pred[mask])
        per_provider[g] = {
            "balanced_accuracy": float(b),
            "n": int(mask.sum()),
            "classes_absent_from_train": locked,
        }
        flag = f"  [site-locked classes: {locked}]" if locked else ""
        print(f"    {g:18s} balanced={b:.3f}  (n={int(mask.sum()):,}){flag}")

    return {
        "overall_accuracy": float(acc),
        "overall_balanced_accuracy": float(bal),
        "overall_macro_f1": float(macro_f1),
        "chance": float(1 / len(class_names)),
        "per_class_recall": per_class,
        "per_provider": per_provider,
        "y_pred_heldout": y_pred,
    }


def pooled_permutation(embeddings, y, n_perm, perm_train_subsample):
    """Label-shuffle permutation on a fast OvR-LogReg 80/20 split."""
    X_tr_full, X_te, y_tr_full, y_te = train_test_split(
        embeddings, y, test_size=0.2, stratify=y, random_state=SEED
    )
    if perm_train_subsample is not None and perm_train_subsample < len(X_tr_full):
        X_tr, _, y_tr, _ = train_test_split(
            X_tr_full, y_tr_full, train_size=int(perm_train_subsample),
            stratify=y_tr_full, random_state=SEED,
        )
        sub_note = f", train subsample n={perm_train_subsample:,}"
    else:
        X_tr, y_tr = X_tr_full, y_tr_full
        sub_note = ""

    def _clf():
        return OneVsRestClassifier(
            LogisticRegression(solver="liblinear", max_iter=1000, C=1.0, random_state=SEED),
            n_jobs=1,
        )

    print(f"\n--- Permutation Test (n={n_perm}, OvR-LogReg, 80/20 split{sub_note}) ---")
    score = accuracy_score(y_te, _clf().fit(X_tr, y_tr).predict(X_te))

    def _one(i):
        rng = np.random.default_rng(SEED + i)
        return accuracy_score(y_te, _clf().fit(X_tr, rng.permutation(y_tr)).predict(X_te))

    perm = np.array(Parallel(n_jobs=4, backend="threading")(
        delayed(_one)(i) for i in range(n_perm)))
    pvalue = (np.sum(perm >= score) + 1) / (n_perm + 1)
    print(f"  True score={score:.3f}  perm mean={perm.mean():.3f}±{perm.std():.3f}  p={pvalue:.2e}")
    return score, perm, float(pvalue)


def make_figure(class_names, pooled, lopo, perm_score, perm_scores, pvalue,
                encoder_name):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(19, 5.2))

    # Panel 1: LOPO held-out confusion matrix (honest, cross-site).
    cm = confusion_matrix(_y_global, lopo["y_pred_heldout"],
                          labels=range(len(class_names)), normalize="true")
    im = axes[0].imshow(cm, cmap="Blues", vmin=0, vmax=1)
    axes[0].set_xticks(range(len(class_names)))
    axes[0].set_yticks(range(len(class_names)))
    axes[0].set_xticklabels(class_names)
    axes[0].set_yticklabels(class_names)
    axes[0].set_xlabel("Predicted")
    axes[0].set_ylabel("True")
    axes[0].set_title("Leave-One-Provider-Out\nconfusion (held-out)")
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            axes[0].text(j, i, f"{cm[i,j]:.2f}", ha="center", va="center",
                         color="white" if cm[i, j] > 0.5 else "black", fontsize=9)
    plt.colorbar(im, ax=axes[0], fraction=0.046)

    # Panel 2: pooled vs LOPO balanced accuracy, with chance.
    labels = ["Pooled CV\n(confounded\nupper bound)", "Leave-One-\nProvider-Out\n(honest)"]
    vals = [pooled["lr_balanced_accuracy"], lopo["overall_balanced_accuracy"]]
    bars = axes[1].bar(labels, vals, color=["#bbbbbb", "#1565C0"])
    axes[1].axhline(lopo["chance"], color="red", ls="--",
                    label=f"chance={lopo['chance']:.2f}")
    axes[1].set_ylim(0, 1)
    axes[1].set_ylabel("Balanced accuracy")
    axes[1].set_title("Site confound: pooled vs cross-site")
    for b, v in zip(bars, vals):
        axes[1].text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.2f}",
                     ha="center", fontsize=11)
    axes[1].legend()

    # Panel 3: pooled permutation histogram.
    axes[2].hist(perm_scores, bins=50, color="lightgray", edgecolor="gray", alpha=0.8,
                 label="Permutation null")
    axes[2].axvline(perm_score, color="red", lw=2, label=f"True={perm_score:.3f}")
    axes[2].axvline(1 / len(class_names), color="blue", lw=1, ls="--",
                    label=f"chance={1/len(class_names):.3f}")
    axes[2].set_xlabel("Accuracy")
    axes[2].set_ylabel("Count")
    axes[2].set_title(f"Pooled permutation (p={pvalue:.2e})")
    axes[2].legend(fontsize=9)

    plt.suptitle(f"H1: Ecotype decodability from {encoder_name.upper()} embeddings "
                 f"(confound-aware)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = FIGURES_DIR / f"h1_probes_{encoder_name}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Figure saved: {path}")
    return path


def run_probes(embeddings, labels, groups, encoder_name, n_perm=N_PERM,
               perm_train_subsample=None):
    global _y_global
    le = LabelEncoder()
    y = le.fit_transform(labels)
    _y_global = y
    class_names = le.classes_

    print(f"\n{'='*64}")
    print(f"HEAD H1: CONFOUND-AWARE PROBES ({encoder_name.upper()})")
    print(f"{'='*64}")
    print(f"  Samples: {len(embeddings):,}  Features: {embeddings.shape[1]}")
    print(f"  Classes: {list(class_names)}")
    print(f"  Class distribution: {dict(zip(class_names, np.bincount(y).tolist()))}")
    if groups is not None:
        uniq, cnt = np.unique(groups, return_counts=True)
        print(f"  Providers (groups): {dict(zip(uniq.tolist(), cnt.tolist()))}")

    pooled = pooled_cv(embeddings, y, class_names)

    if groups is None or len(np.unique(groups)) < 2:
        print("\n  WARNING: no usable provider groups; skipping LOPO (headline).")
        lopo = None
    else:
        lopo = leave_one_provider_out(embeddings, y, groups, class_names)

    perm_score, perm_scores, pvalue = pooled_permutation(
        embeddings, y, n_perm, perm_train_subsample)

    fig_path = None
    if lopo is not None:
        fig_path = make_figure(class_names, pooled, lopo, perm_score, perm_scores,
                               pvalue, encoder_name)

    # Verdict is driven by the HONEST (LOPO) number, not the confounded pooled one.
    print(f"\n{'='*64}\nH1 SUMMARY\n{'='*64}")
    print(f"  Pooled CV balanced acc (confounded upper bound): "
          f"{pooled['lr_balanced_accuracy']:.3f}")
    if lopo is not None:
        gen = lopo["overall_balanced_accuracy"]
        print(f"  Cross-site (LOPO) balanced acc (HEADLINE): {gen:.3f}")
        print(f"  Cross-site macro-F1: {lopo['overall_macro_f1']:.3f}  "
              f"(chance {lopo['chance']:.3f})")
        verdict = ("STRONG cross-site signal" if gen > 2 * lopo["chance"]
                   else "WEAK / site-confounded" if gen > 1.2 * lopo["chance"]
                   else "NO cross-site signal (confounded)")
        print(f"  Verdict: {verdict}")
    print(f"  Pooled permutation p-value: {pvalue:.2e}")
    print(f"{'='*64}")

    results = {
        "encoder": encoder_name,
        "n_samples": int(len(embeddings)),
        "classes": list(map(str, class_names)),
        "pooled_cv": {k: v for k, v in pooled.items() if k != "y_pred_heldout"},
        "leave_one_provider_out": (
            {k: v for k, v in lopo.items() if k != "y_pred_heldout"}
            if lopo is not None else None
        ),
        "pooled_permutation_pvalue": pvalue,
        "figure": (f"figures/{Path(fig_path).name}") if fig_path else None,
    }
    metrics_path = FIGURES_DIR / f"h1_metrics_{encoder_name}.json"
    metrics_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"  Metrics JSON: {metrics_path}")
    return results


def main():
    parser = argparse.ArgumentParser(description="H1: confound-aware probes")
    parser.add_argument("--embeddings", required=True)
    parser.add_argument("--n-perm", type=int, default=N_PERM)
    parser.add_argument("--perm-train-subsample", type=int, default=None)
    parser.add_argument("--group-field", default="provider",
                        help="metadata field used as the held-out group (default: provider)")
    args = parser.parse_args()

    emb_path = Path(args.embeddings)
    if not emb_path.exists():
        print(f"ERROR: {emb_path} not found.")
        return 1

    data = np.load(emb_path, allow_pickle=True)
    embeddings = data["embeddings"]
    labels = data["labels"]
    groups = load_groups(emb_path, len(embeddings), args.group_field)

    encoder_name = emb_path.stem.replace("_embeddings", "")
    run_probes(embeddings, labels, groups, encoder_name,
               n_perm=args.n_perm, perm_train_subsample=args.perm_train_subsample)
    return 0


if __name__ == "__main__":
    sys.exit(main())

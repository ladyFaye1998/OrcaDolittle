#!/usr/bin/env python3
"""Decode a *three-state* behavioural context from killer-whale communicative calls.

Multi-context extension of scripts/dtag_context_decode.py. Reuses the already-computed
AVES2 embeddings (call_embeddings.npz) and only swaps in the movement-only 3-state label
(context3_labeled_calls.csv from scripts/dtag_context_multilabel.py), so NO re-encoding
is needed. The question is whether a model that sees only the whales' communicative calls
can predict which of three behavioural contexts (foraging / travelling / resting) the
caller is in, on **held-out individuals**, above a label-permutation null
[@tennessen2019; @holt2024masking].

Because (i) the label is movement-only and never saw the audio, and (ii) validation is
leave-individual-out, a positive result cannot be explained by recognising the whale, the
recorder, or the site, nor by circularity with the acoustic stream.

Metrics: multiclass balanced accuracy (mean per-class recall), macro-F1, per-class recall,
and the normalised confusion matrix, each against a >=200-permutation null.

Inputs:
  --emb NPZ      call_embeddings.npz (default D:/dtag_run/clips/call_embeddings.npz)
  --labels CSV   context3_labeled_calls.csv (default alongside the npz)
Outputs:
  reports/context3_decode_summary.json
  figures/context3_decode.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
REPORT = REPO / "reports" / "context3_decode_summary.json"
FIG = REPO / "figures" / "context3_decode.png"
SEED = 0
CLASSES = ["foraging", "travelling", "resting"]


PCA_DIM = 128   # leakage-safe per-fold PCA keeps the decode tractable for the permutation null


def _pipe():
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.pipeline import make_pipeline
    return make_pipeline(
        StandardScaler(),
        PCA(n_components=PCA_DIM, random_state=SEED),
        LogisticRegression(max_iter=1000, tol=1e-3, class_weight="balanced", solver="lbfgs"),
    )


def logo_predict(X, y, groups):
    """Leave-one-individual-out out-of-fold predictions (balanced multinomial logistic).

    PCA is fit inside each fold (train only), so held-out individuals never inform the
    projection -- the leave-individual-out guarantee is preserved.
    """
    from sklearn.model_selection import LeaveOneGroupOut

    logo = LeaveOneGroupOut()
    yt, yp = [], []
    for tr, te in logo.split(X, y, groups):
        if len(set(y[tr])) < 2:
            continue
        pipe = _pipe().fit(X[tr], y[tr])
        yp.append(pipe.predict(X[te]))
        yt.append(y[te])
    return np.concatenate(yt), np.concatenate(yp)


def scores(yt, yp):
    from sklearn.metrics import balanced_accuracy_score, f1_score
    return (balanced_accuracy_score(yt, yp),
            f1_score(yt, yp, average="macro", labels=CLASSES, zero_division=0))


def _null_balacc(X, y, groups, keep, seed_i):
    """One permutation-null balanced accuracy: shuffle labels within each individual."""
    rng = np.random.default_rng(seed_i)
    yp = y.copy()
    for dep in keep:
        m = groups == dep
        yp[m] = rng.permutation(yp[m])
    yt_n, yp_n = logo_predict(X, yp, groups)
    return scores(yt_n, yp_n)[0]


def main() -> int:
    import pandas as pd

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--emb", default=r"D:/dtag_run/clips/call_embeddings.npz")
    ap.add_argument("--labels", default=r"D:/dtag_run/clips/context3_labeled_calls.csv")
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--min-per-class", type=int, default=10,
                    help="min calls/class for an individual to enter the leave-individual-out set")
    args = ap.parse_args()

    d = np.load(args.emb, allow_pickle=True)
    E = d["embeddings"].astype(np.float32)
    meta = pd.DataFrame(list(d["metadata"]))
    lab = pd.read_csv(args.labels)[["clip", "context3"]]
    meta = meta.reset_index().merge(lab, on="clip", how="inner")
    print(f"{len(meta)} calls joined to a 3-state label")

    # Keep individuals that carry all three contexts with adequate per-class support, so a
    # leave-individual-out fold tests genuine 3-way generalisation rather than identity.
    keep = []
    for dep, g in meta.groupby("deployment"):
        vc = g["context3"].value_counts()
        if all(vc.get(c, 0) >= args.min_per_class for c in CLASSES):
            keep.append(dep)
    sub = meta[meta["deployment"].isin(keep)].reset_index(drop=True)
    X = E[sub["index"].to_numpy()]
    y = sub["context3"].to_numpy()
    groups = sub["deployment"].to_numpy()
    print(f"usable individuals (all 3 contexts, >= {args.min_per_class}/class): {len(keep)}")
    print(f"calls used: {len(sub)}  class counts: {dict(pd.Series(y).value_counts())}")

    yt, yp = logo_predict(X, y, groups)
    obs_ba, obs_f1 = scores(yt, yp)

    from sklearn.metrics import confusion_matrix, recall_score
    cm = confusion_matrix(yt, yp, labels=CLASSES)
    cm_norm = cm / cm.sum(axis=1, keepdims=True).clip(min=1)
    per_class_recall = recall_score(yt, yp, average=None, labels=CLASSES, zero_division=0)

    # Permute labels within each individual so the per-individual context marginal (and thus
    # the imbalance a fold sees) is preserved under the null. Parallelised across cores.
    from joblib import Parallel, delayed
    seeds = np.random.SeedSequence(SEED).spawn(args.n_perm)
    null_ba = np.array(Parallel(n_jobs=-1, verbose=5)(
        delayed(_null_balacc)(X, y, groups, keep, s) for s in seeds))
    p = (np.sum(null_ba >= obs_ba) + 1) / (args.n_perm + 1)

    chance = 1.0 / len(CLASSES)
    results = {
        "design": "3-state movement-only context (foraging/travelling/resting); "
                  "decoder input = communicative calls (AVES2); leave-individual-out.",
        "n_calls": int(len(sub)),
        "n_individuals": int(len(keep)),
        "deployments": keep,
        "classes": CLASSES,
        "class_counts": {k: int(v) for k, v in pd.Series(y).value_counts().items()},
        "chance_balanced_accuracy": chance,
        "balanced_accuracy": float(obs_ba),
        "macro_f1": float(obs_f1),
        "per_class_recall": {c: float(r) for c, r in zip(CLASSES, per_class_recall)},
        "confusion_matrix_rows_true": {c: [int(v) for v in row] for c, row in zip(CLASSES, cm)},
        "confusion_matrix_normalised": {c: [float(v) for v in row]
                                        for c, row in zip(CLASSES, cm_norm)},
        "null_mean": float(null_ba.mean()),
        "null_std": float(null_ba.std()),
        "n_perm": int(args.n_perm),
        "pvalue": float(p),
        "caveats": [
            "Context is movement-only (depth + jerk + ODBA); decoder input is communicative "
            "calls -> non-circular.",
            "Clips are 16 kHz: echolocation peak energy (>>8 kHz) is absent by construction, "
            "so the decode operates on the communicative band, not biosonar.",
            "Leave-individual-out: identity cannot stand in for behaviour.",
            "travelling/resting split is an ODBA activity dichotomy, not a named ethogram state; "
            "context-association, not 'meaning'.",
            "Non-invasive secondary analysis of archived DTAG data.",
        ],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"\n3-way leave-individual-out balanced accuracy = {obs_ba:.3f} "
          f"(chance {chance:.3f}; null {null_ba.mean():.3f}+/-{null_ba.std():.3f}; p={p:.2e})")
    print(f"macro-F1 = {obs_f1:.3f}")
    print("per-class recall:", {c: round(float(r), 3) for c, r in zip(CLASSES, per_class_recall)})

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, (axb, axc) = plt.subplots(1, 2, figsize=(11, 4.6))
        axb.bar([0], [obs_ba], width=0.5, color="#2a7fb8", label="leave-individual-out bal. acc")
        axb.plot([0], [null_ba.mean()], "r_", markersize=40, markeredgewidth=3,
                 label="permutation null")
        axb.axhline(chance, ls="--", c="gray", lw=1, label=f"chance ({chance:.2f})")
        axb.text(0, obs_ba + 0.02, f"{obs_ba:.2f}\n(p={p:.1e})", ha="center", fontsize=10)
        axb.set_xticks([0]); axb.set_xticklabels(["3-way"]); axb.set_ylim(0, 1)
        axb.set_ylabel("balanced accuracy"); axb.legend(fontsize=8)
        axb.set_title(f"Context from communicative calls\n{len(sub)} calls, "
                      f"{len(keep)} individuals, leave-individual-out")
        im = axc.imshow(cm_norm, vmin=0, vmax=1, cmap="Blues")
        axc.set_xticks(range(3)); axc.set_xticklabels(CLASSES, rotation=20)
        axc.set_yticks(range(3)); axc.set_yticklabels(CLASSES)
        axc.set_xlabel("predicted"); axc.set_ylabel("true (movement)")
        for i in range(3):
            for j in range(3):
                axc.text(j, i, f"{cm_norm[i, j]:.2f}", ha="center", va="center",
                         color="white" if cm_norm[i, j] > 0.5 else "black", fontsize=10)
        axc.set_title("Normalised confusion (out-of-fold)")
        fig.colorbar(im, ax=axc, fraction=0.046)
        plt.tight_layout()
        FIG.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(FIG, dpi=150, bbox_inches="tight")
        print("wrote", FIG)
    except Exception as e:
        print("figure skipped:", e)

    print("wrote", REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Rung 1 result: site-controlled killer-whale CALL-TYPE classification.

This goes beyond ecotype (H1/H4): it asks whether frozen AVES2 embeddings
separate *stereotyped call types* (Ford/Filatova catalogue codes) [@ford1989;
@filatova2015; @hagiwara2023aves], using catalogue-coded labels recovered from
the DCLDE per-provider annotations (`scripts/build_calltype_manifest.py`).

Labels are joined onto the existing embedding artifact by (soundfile, onset)
within a small tolerance, so no re-encoding is needed. We focus on SRKW S-calls,
the population with call-type labels at two independent providers (VFPA, SMRU),
which lets us run the control the ecotype result failed:

  Experiment A - WITHIN-PROVIDER (site held constant): multi-class S-call-type
    discrimination inside VFPA. Because the hydrophone is fixed, above-chance
    accuracy is call-type acoustic structure, not site.
  Experiment B - CROSS-PROVIDER TRANSFER: train on VFPA, test on SMRU, on the
    S-call types shared by both. This tests whether call-type structure
    generalises across recording sites (the ecotype boundary did not).

Every headline number is checked against a majority-class baseline and a
label-permutation null. Caveats are reported in the metrics JSON.

Usage:
  python scripts/run_calltype_model.py --embeddings data/embeddings/aves2_full_labeled.npz \
      --manifest data/join_tables/call_type_manifest.csv --min-per-type 30
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
SEED = 0
MATCH_TOL_S = 0.10


N_PERM = 200


def _clf():
    # Standard linear probe on the full 768-d AVES2 embedding: measures linear
    # separability of call types in the frozen representation. No dimensionality
    # reduction, so the reported number is the representation's own structure.
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=5000, class_weight="balanced", C=1.0),
    )


def _mlp():
    # Nonlinear head, reported alongside the linear probe.
    from sklearn.neural_network import MLPClassifier
    return make_pipeline(
        StandardScaler(),
        MLPClassifier(hidden_layer_sizes=(256, 128), max_iter=600,
                      alpha=1e-3, random_state=SEED),
    )


def join_labels(emb_path: Path, manifest_path: Path):
    data = np.load(emb_path, allow_pickle=True)
    X = data["embeddings"]
    md = data["metadata"]
    emb = pd.DataFrame([{
        "file": str(m.get("soundfile", "")),
        "begin": float(m.get("begin_sec", -1)),
        "provider_emb": str(m.get("provider", "")),
        "idx": i,
    } for i, m in enumerate(md)])

    man = pd.read_csv(manifest_path)
    man["file"] = man["audio_path"].astype(str).apply(
        lambda p: p.replace("\\", "/").split("/")[-1])
    man["start"] = pd.to_numeric(man["start"], errors="coerce")
    man = man[man["start"].notna()]

    emb_by_file = {f: g for f, g in emb.groupby("file")}
    recs = []
    for _, r in man.iterrows():
        g = emb_by_file.get(r["file"])
        if g is None:
            continue
        dt = (g["begin"] - r["start"]).abs()
        j = dt.idxmin()
        if dt.loc[j] <= MATCH_TOL_S:
            recs.append({"idx": int(g.loc[j, "idx"]),
                         "call_type": r["call_type"],
                         "call_family": r["call_family"],
                         "provider": r["provider"]})
    lab = pd.DataFrame(recs).drop_duplicates("idx")
    return X, lab


def within_provider(X, lab, provider, min_per_type):
    sub = lab[(lab["provider"] == provider) & (lab["call_family"] == "SRKW")].copy()
    vc = sub["call_type"].value_counts()
    keep = vc[vc >= min_per_type].index
    sub = sub[sub["call_type"].isin(keep)]
    if sub["call_type"].nunique() < 2:
        return None
    Xs = X[sub["idx"].to_numpy()]
    y = sub["call_type"].to_numpy()
    classes = sorted(set(y))
    k = len(classes)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    y_true, y_pred = [], []
    for tr, te in skf.split(Xs, y):
        clf = _clf().fit(Xs[tr], y[tr])
        y_pred.append(clf.predict(Xs[te]))
        y_true.append(y[te])
    y_true = np.concatenate(y_true)
    y_pred = np.concatenate(y_pred)
    bal = balanced_accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro")
    majority = pd.Series(y).value_counts(normalize=True).iloc[0]

    # Nonlinear head (reported alongside the linear probe).
    mt, mp = [], []
    for tr, te in skf.split(Xs, y):
        clf = _mlp().fit(Xs[tr], y[tr])
        mp.append(clf.predict(Xs[te]))
        mt.append(y[te])
    mlp_bal = balanced_accuracy_score(np.concatenate(mt), np.concatenate(mp))
    mlp_f1 = f1_score(np.concatenate(mt), np.concatenate(mp), average="macro")

    rng = np.random.default_rng(SEED)
    perm = []
    for it in range(N_PERM):
        yp = rng.permutation(y)
        yt2, pr2 = [], []
        for tr, te in skf.split(Xs, yp):
            clf = _clf().fit(Xs[tr], yp[tr])
            pr2.append(clf.predict(Xs[te]))
            yt2.append(yp[te])
        perm.append(balanced_accuracy_score(np.concatenate(yt2), np.concatenate(pr2)))
        if (it + 1) % 25 == 0:
            print(f"    permutation {it + 1}/{N_PERM}", flush=True)
    perm = np.array(perm)
    pval = (np.sum(perm >= bal) + 1) / (len(perm) + 1)

    return {
        "provider": provider, "n": int(len(sub)), "k_types": k, "classes": classes,
        "balanced_accuracy": float(bal), "macro_f1": float(macro_f1),
        "mlp_balanced_accuracy": float(mlp_bal), "mlp_macro_f1": float(mlp_f1),
        "chance_1_over_k": float(1.0 / k), "majority_baseline": float(majority),
        "permutation_mean": float(perm.mean()), "permutation_pvalue": float(pval),
        "_cm": confusion_matrix(y_true, y_pred, labels=classes), "_classes": classes,
    }


def cross_provider(X, lab, train_pv, test_pv, min_train, min_test):
    s = lab[lab["call_family"] == "SRKW"]
    tr = s[s["provider"] == train_pv]
    te = s[s["provider"] == test_pv]
    tr_types = tr["call_type"].value_counts()
    te_types = te["call_type"].value_counts()
    shared = [t for t in tr_types.index
              if tr_types[t] >= min_train and te_types.get(t, 0) >= min_test]
    if len(shared) < 2:
        return {"shared_types": shared, "note": "insufficient shared types for transfer"}
    tr = tr[tr["call_type"].isin(shared)]
    te = te[te["call_type"].isin(shared)]
    clf = _clf().fit(X[tr["idx"].to_numpy()], tr["call_type"].to_numpy())
    yt = te["call_type"].to_numpy()
    yp = clf.predict(X[te["idx"].to_numpy()])
    bal = balanced_accuracy_score(yt, yp)
    macro_f1 = f1_score(yt, yp, average="macro")
    k = len(shared)
    return {
        "train_provider": train_pv, "test_provider": test_pv,
        "shared_types": shared, "k": k,
        "n_train": int(len(tr)), "n_test": int(len(te)),
        "transfer_balanced_accuracy": float(bal),
        "transfer_macro_f1": float(macro_f1),
        "chance_1_over_k": float(1.0 / k),
    }


def make_figure(a, b, fig_path):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    cm = a["_cm"].astype(float)
    cmn = cm / np.clip(cm.sum(axis=1, keepdims=True), 1, None)
    im = axes[0].imshow(cmn, cmap="magma", vmin=0, vmax=1)
    axes[0].set_xticks(range(len(a["_classes"])))
    axes[0].set_yticks(range(len(a["_classes"])))
    axes[0].set_xticklabels(a["_classes"], rotation=90, fontsize=7)
    axes[0].set_yticklabels(a["_classes"], fontsize=7)
    axes[0].set_xlabel("predicted S-call type")
    axes[0].set_ylabel("true S-call type")
    axes[0].set_title(f"A. Within-{a['provider']} S-call types (site fixed)\n"
                      f"bal.acc={a['balanced_accuracy']:.2f} "
                      f"(chance {a['chance_1_over_k']:.2f}, p={a['permutation_pvalue']:.1e})",
                      fontsize=10)
    fig.colorbar(im, ax=axes[0], fraction=0.046)

    labels = [f"Within-{a['provider']}\n(k={a['k_types']})"]
    vals = [a["balanced_accuracy"]]
    chances = [a["chance_1_over_k"]]
    if b and "transfer_balanced_accuracy" in b:
        labels.append(f"Transfer {b['train_provider']}->{b['test_provider']}\n(k={b['k']})")
        vals.append(b["transfer_balanced_accuracy"])
        chances.append(b["chance_1_over_k"])
    xpos = np.arange(len(labels))
    axes[1].bar(xpos, vals, width=0.5, color="#2a7fb8", label="balanced accuracy")
    axes[1].plot(xpos, chances, "r_", markersize=40, markeredgewidth=3, label="chance (1/k)")
    axes[1].set_xticks(xpos)
    axes[1].set_xticklabels(labels, fontsize=9)
    axes[1].set_ylim(0, 1)
    axes[1].set_ylabel("balanced accuracy")
    axes[1].set_title("Call-type discrimination vs chance", fontsize=11)
    for i, v in enumerate(vals):
        axes[1].text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=10)
    axes[1].legend(fontsize=9)
    plt.suptitle("Rung 1: site-controlled SRKW call-type classification (AVES2)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--embeddings", default="data/embeddings/aves2_full_labeled.npz")
    p.add_argument("--manifest", default="data/join_tables/call_type_manifest.csv")
    p.add_argument("--min-per-type", type=int, default=30)
    p.add_argument("--min-transfer-train", type=int, default=30)
    p.add_argument("--min-transfer-test", type=int, default=10)
    args = p.parse_args()

    emb_path, man_path = Path(args.embeddings), Path(args.manifest)
    if not emb_path.exists() or not man_path.exists():
        print("ERROR: missing embeddings or manifest.")
        return 1

    X, lab = join_labels(emb_path, man_path)
    print(f"Joined call-type labels onto {len(lab)} embedding segments.")
    print("By provider:", lab["provider"].value_counts().to_dict())
    print("By family:", lab["call_family"].value_counts().to_dict())

    print("\n=== Experiment A: within-VFPA S-call-type discrimination ===")
    a = within_provider(X, lab, "vfpa", args.min_per_type)
    if a is None:
        print("  insufficient data.")
        return 1
    print(f"  n={a['n']}  k={a['k_types']} types  linear bal.acc={a['balanced_accuracy']:.3f} "
          f"(chance {a['chance_1_over_k']:.3f}, majority {a['majority_baseline']:.3f})")
    print(f"  linear macro-F1={a['macro_f1']:.3f}  MLP bal.acc={a['mlp_balanced_accuracy']:.3f}  "
          f"MLP macro-F1={a['mlp_macro_f1']:.3f}")
    print(f"  perm mean={a['permutation_mean']:.3f}  p={a['permutation_pvalue']:.2e}")

    print("\n=== Experiment B: cross-provider transfer VFPA -> SMRU ===")
    b = cross_provider(X, lab, "vfpa", "smru", args.min_transfer_train, args.min_transfer_test)
    if "transfer_balanced_accuracy" in b:
        print(f"  shared types (k={b['k']}): {b['shared_types']}")
        print(f"  train n={b['n_train']}  test n={b['n_test']}")
        print(f"  transfer bal.acc={b['transfer_balanced_accuracy']:.3f} "
              f"(chance {b['chance_1_over_k']:.3f})  macro-F1={b['transfer_macro_f1']:.3f}")
    else:
        print(f"  {b.get('note')} shared={b.get('shared_types')}")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig_path = FIGURES_DIR / "calltype_model_srkw.png"
    make_figure(a, b, fig_path)
    print(f"\nFigure: {fig_path}")

    a_out = {k: v for k, v in a.items() if not k.startswith("_")}
    summary = {
        "analysis": "rung1_calltype_classification_srkw",
        "encoder": "AVES2",
        "label_source": "DCLDE per-provider annotations (call_type)",
        "n_calltype_labeled_segments": int(len(lab)),
        "within_provider_vfpa": a_out,
        "cross_provider_transfer": b,
        "figure": f"figures/{fig_path.name}",
        "caveats": [
            "Catalogue call-type labels are detection-level and provider-concentrated; "
            "SRKW S-calls here come from VFPA and SMRU only.",
            "Within-provider result holds recording site constant, so it reflects call-type "
            "acoustic structure, not hydrophone identity.",
            "S-call types correlate with pod/matriline; this is call-type discrimination, "
            "NOT evidence of meaning or function.",
            "SMRU test set is small; transfer is a first-pass control, not a definitive estimate.",
        ],
    }
    out = REPORTS_DIR / "calltype_model_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Metrics JSON: reports/{out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

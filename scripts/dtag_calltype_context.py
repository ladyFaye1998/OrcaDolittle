#!/usr/bin/env python3
"""Test call-type x context selectivity: are specific call types produced in specific contexts?

This is the step that turns a behavioural-*state* decode into evidence of *context-specific
communication*. A state decode shows "the calls differ by context"; this shows the stronger,
literature-standard production criterion: **specific call types are produced preferentially
in specific behavioural contexts** [@ford1989; @foote2008], which is what "communication in
more than one context" means operationally.

Method (self-contained, reuses the existing AVES2 embeddings -- no re-encode):
  1. Cluster the communicative-call embeddings into K putative call types (KMeans on
     standardised AVES2 features; K chosen by silhouette over a small grid).
  2. Build the call-type x context contingency table.
  3. Test association with a **within-individual** label-permutation null: context labels are
     shuffled within each deployment (preserving each whale's own context marginal), so a
     significant association cannot be produced by between-individual differences in either
     repertoire or activity budget. Statistic = Cramer's V of the table.
  4. Per-cluster selectivity: observed/expected enrichment per (type, context) with a
     per-cell two-sided permutation p-value from the same within-individual shuffle.

Clusters are *putative* types discovered in the on-animal tag domain, not the named DCLDE
catalogue types; we therefore speak of "call types (data-driven clusters)".

Inputs:
  --emb NPZ      call_embeddings.npz
  --labels CSV   context3_labeled_calls.csv (3-state) or context_labeled_calls.csv (binary)
Outputs:
  reports/calltype_context_selectivity.json
  figures/calltype_context.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
REPORT = REPO / "reports" / "calltype_context_selectivity.json"
FIG = REPO / "figures" / "calltype_context.png"
SEED = 0


def cramers_v(table: np.ndarray) -> float:
    """Bias-uncorrected Cramer's V from a contingency table."""
    n = table.sum()
    if n == 0:
        return 0.0
    row = table.sum(axis=1, keepdims=True)
    col = table.sum(axis=0, keepdims=True)
    expected = row @ col / n
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum((table - expected) ** 2 / np.where(expected > 0, expected, np.nan))
    k = min(table.shape)
    return float(np.sqrt(chi2 / (n * (k - 1)))) if k > 1 else 0.0


def contingency(types: np.ndarray, ctx: np.ndarray, n_types: int, classes):
    t = np.zeros((n_types, len(classes)), dtype=float)
    cidx = {c: j for j, c in enumerate(classes)}
    for ti, cc in zip(types, ctx):
        t[ti, cidx[cc]] += 1
    return t


def choose_k(Xs, log=print):
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    best = None
    rng = np.random.default_rng(SEED)
    samp = rng.choice(len(Xs), size=min(3000, len(Xs)), replace=False)  # silhouette on a subsample
    for k in (6, 8, 10, 12, 14):
        km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(Xs)
        s = silhouette_score(Xs[samp], km.labels_[samp])
        log(f"  K={k}: silhouette={s:.3f}")
        if best is None or s > best[1]:
            best = (k, s, km)
    return best


def main() -> int:
    import pandas as pd

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--emb", default=r"D:/dtag_run/clips/call_embeddings.npz")
    ap.add_argument("--labels", default=r"D:/dtag_run/clips/context3_labeled_calls.csv")
    ap.add_argument("--label-col", default="context3")
    ap.add_argument("--n-perm", type=int, default=1000)
    ap.add_argument("--k", type=int, default=0, help="fixed K (0 = choose by silhouette)")
    args = ap.parse_args()

    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans

    d = np.load(args.emb, allow_pickle=True)
    E = d["embeddings"].astype(np.float32)
    meta = pd.DataFrame(list(d["metadata"])).reset_index()
    lab = pd.read_csv(args.labels)
    col = args.label_col if args.label_col in lab.columns else "context"
    meta = meta.merge(lab[["clip", col]], on="clip", how="inner")
    classes = sorted(meta[col].unique())
    X = E[meta["index"].to_numpy()]
    ctx = meta[col].to_numpy()
    groups = meta["deployment"].to_numpy()
    print(f"{len(meta)} calls; contexts {classes}; {meta['deployment'].nunique()} individuals")

    Xs = StandardScaler().fit_transform(X)
    if args.k > 0:
        km = KMeans(n_clusters=args.k, n_init=10, random_state=SEED).fit(Xs)
        K, sil = args.k, None
    else:
        K, sil, km = choose_k(Xs)
        print(f"chosen K={K} (silhouette={sil:.3f})")
    types = km.labels_

    obs_tbl = contingency(types, ctx, K, classes)
    obs_v = cramers_v(obs_tbl)

    row = obs_tbl.sum(axis=1, keepdims=True)
    coln = obs_tbl.sum(axis=0, keepdims=True)
    n = obs_tbl.sum()
    expected = row @ coln / n
    enrich = np.divide(obs_tbl, expected, out=np.ones_like(obs_tbl), where=expected > 0)

    # within-individual permutation null
    rng = np.random.default_rng(SEED)
    null_v = np.empty(args.n_perm)
    ge = np.zeros_like(obs_tbl)  # count perms with enrichment >= observed (per cell, two-sided via abs)
    obs_dev = np.abs(np.log(np.clip(enrich, 1e-6, None)))
    deps = np.unique(groups)
    for i in range(args.n_perm):
        cperm = ctx.copy()
        for dep in deps:
            m = groups == dep
            cperm[m] = rng.permutation(cperm[m])
        tbl = contingency(types, cperm, K, classes)
        null_v[i] = cramers_v(tbl)
        ex = tbl.sum(axis=1, keepdims=True) @ tbl.sum(axis=0, keepdims=True) / tbl.sum()
        en = np.divide(tbl, ex, out=np.ones_like(tbl), where=ex > 0)
        ge += (np.abs(np.log(np.clip(en, 1e-6, None))) >= obs_dev).astype(float)
    p_v = (np.sum(null_v >= obs_v) + 1) / (args.n_perm + 1)
    p_cell = (ge + 1) / (args.n_perm + 1)

    selective = []
    for ti in range(K):
        for j, c in enumerate(classes):
            if p_cell[ti, j] < 0.05 and enrich[ti, j] > 1.0:
                selective.append({"call_type": int(ti), "context": c,
                                  "enrichment": float(enrich[ti, j]),
                                  "n_calls": int(obs_tbl[ti, j]),
                                  "pvalue": float(p_cell[ti, j])})
    selective.sort(key=lambda r: -r["enrichment"])

    results = {
        "design": "KMeans call-type clusters on AVES2 embeddings x movement-only context; "
                  "within-individual permutation null preserves each whale's context marginal.",
        "label_column": col,
        "classes": classes,
        "n_calls": int(len(meta)),
        "n_individuals": int(len(deps)),
        "n_call_types": int(K),
        "silhouette": (None if sil is None else float(sil)),
        "cramers_v": float(obs_v),
        "cramers_v_null_mean": float(null_v.mean()),
        "cramers_v_null_std": float(null_v.std()),
        "n_perm": int(args.n_perm),
        "pvalue_association": float(p_v),
        "n_context_selective_types": len({r["call_type"] for r in selective}),
        "selective_cells": selective,
        "enrichment_matrix": {int(ti): {classes[j]: float(enrich[ti, j]) for j in range(len(classes))}
                              for ti in range(K)},
        "type_counts": {int(ti): int(obs_tbl[ti].sum()) for ti in range(K)},
        "caveats": [
            "Clusters are data-driven putative types in the on-animal tag domain, not named "
            "DCLDE catalogue types.",
            "Context is movement-only; within-individual null controls for repertoire and "
            "activity-budget differences between whales.",
            "Production criterion (context-specific production), not receiver response.",
        ],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"\nCramer's V = {obs_v:.3f} (null {null_v.mean():.3f}+/-{null_v.std():.3f}, "
          f"p={p_v:.2e})")
    print(f"context-selective call types: {results['n_context_selective_types']}/{K}")
    for r in selective[:12]:
        print(f"  type {r['call_type']:2d} -> {r['context']:11s} "
              f"enrich x{r['enrichment']:.2f}  (n={r['n_calls']}, p={r['pvalue']:.1e})")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        order = np.argsort(-enrich.max(axis=1))
        em = enrich[order]
        fig, ax = plt.subplots(figsize=(1.6 + 1.1 * len(classes), 0.45 * K + 1.5))
        im = ax.imshow(em, cmap="RdBu_r", vmin=0, vmax=2, aspect="auto")
        ax.set_xticks(range(len(classes))); ax.set_xticklabels(classes, rotation=20)
        ax.set_yticks(range(K)); ax.set_yticklabels([f"type {order[i]}" for i in range(K)])
        for i in range(K):
            for j in range(len(classes)):
                star = "*" if p_cell[order[i], j] < 0.05 and em[i, j] > 1 else ""
                ax.text(j, i, f"{em[i, j]:.2f}{star}", ha="center", va="center", fontsize=8,
                        color="white" if abs(em[i, j] - 1) > 0.6 else "black")
        ax.set_title(f"Call-type x context enrichment (obs/exp)\nCramer's V={obs_v:.2f}, "
                     f"p={p_v:.1e}; * within-individual p<0.05")
        fig.colorbar(im, ax=ax, fraction=0.046, label="enrichment")
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

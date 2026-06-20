#!/usr/bin/env python3
"""Rung 4 (validated units): sequential structure of *catalogue* call types.

The Rung-4 Markov test in `run_sequence_structure.py` measures sequential
dependence over an unsupervised k-means call vocabulary, which the manuscript
must caveat ("tokens are not validated biological call types"). This script
removes that caveat: it runs the identical first-order test over the **expert
catalogue call types** recovered from the DCLDE per-provider annotations
[@ford1989; @filatova2015], using the call-type manifest
(`data/join_tables/call_type_manifest.csv`).

For each population subset (site held constant), it:
  1. Builds per-recording call-type sequences (grouped by `audio_path`, ordered
     by onset `start`).
  2. Measures first-order structure two ways:
       (a) mutual information I(call_t ; call_{t+1}) between adjacent calls;
       (b) held-out add-alpha bigram vs unigram cross-entropy (predictive gain).
  3. Tests significance with a within-recording order-shuffle null, which
     destroys order while preserving each recording's call composition (so the
     result cannot be explained by which calls a site/encounter contains)
     [@kershenbaum2024whyanimalstalk].
  4. Separates genuine transitions from repetition (self-transition rate and
     repetition-removed MI).

A positive result is evidence of rule-like sequential structure over *validated*
call units -- the production-side prerequisite for combinatorial coding, NOT
evidence of meaning. Reported honestly whichever way it comes out.

Usage:
  python scripts/run_calltype_sequence.py \
      --manifest data/join_tables/call_type_manifest.csv --n-perm 1000
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = REPO_ROOT / "figures"
REPORTS_DIR = REPO_ROOT / "reports"
SEED = 0
VAL_FRACTION = 0.2
MIN_LEN = 3

# Site-controlled subsets: (label, call_family, provider). Provider held constant
# so structure cannot be a cross-site artifact.
SUBSETS = [
    ("NRKW N-calls @ dfo_crp", "NRKW", "dfo_crp"),
    ("SRKW S-calls @ vfpa", "SRKW", "vfpa"),
]


def build_sequences(df_subset: pd.DataFrame, type_to_idx: dict) -> list[list[int]]:
    seqs = []
    for _, grp in df_subset.groupby("audio_path", sort=False):
        ordered = grp.sort_values(["start", "end"])
        ids = [type_to_idx[t] for t in ordered["call_type"]]
        if len(ids) >= MIN_LEN:
            seqs.append(ids)
    return seqs


def transition_counts(sequences, k):
    M = np.zeros((k, k), dtype=float)
    for s in sequences:
        for a, b in zip(s[:-1], s[1:]):
            M[a, b] += 1
    return M


def mutual_information(M):
    total = M.sum()
    if total == 0:
        return 0.0
    P = M / total
    px = P.sum(axis=1, keepdims=True)
    py = P.sum(axis=0, keepdims=True)
    denom = px @ py
    mask = (P > 0) & (denom > 0)
    return float(np.sum(P[mask] * np.log2(P[mask] / denom[mask])))


def bigram_unigram_heldout(train_seqs, val_seqs, k, alpha=0.5):
    tc = transition_counts(train_seqs, k)
    uni = np.zeros(k)
    for s in train_seqs:
        for t in s:
            uni[t] += 1
    uni_p = (uni + alpha) / (uni.sum() + alpha * k)
    bg_row = tc + alpha
    bg_p = bg_row / bg_row.sum(axis=1, keepdims=True)
    ll_bg, ll_uni, n = 0.0, 0.0, 0
    for s in val_seqs:
        for a, b in zip(s[:-1], s[1:]):
            ll_bg += np.log2(bg_p[a, b])
            ll_uni += np.log2(uni_p[b])
            n += 1
    if n == 0:
        return None, None, 0
    return -ll_bg / n, -ll_uni / n, n


def analyze_subset(label, df_subset, n_perm, min_type_count, seed=SEED):
    counts = df_subset["call_type"].value_counts()
    keep = counts[counts >= min_type_count].index.tolist()
    df_subset = df_subset[df_subset["call_type"].isin(keep)].copy()
    types = sorted(df_subset["call_type"].unique())
    type_to_idx = {t: i for i, t in enumerate(types)}
    k = len(types)
    if k < 2:
        return {"label": label, "status": "skipped_too_few_types", "k": k}, None, None

    seqs = build_sequences(df_subset, type_to_idx)
    if len(seqs) < 5:
        return {"label": label, "status": "skipped_too_few_recordings",
                "k": k, "n_recordings": len(seqs)}, None, None

    lens = [len(s) for s in seqs]
    n_pairs = sum(l - 1 for l in lens)

    M = transition_counts(seqs, k)
    mi_real = mutual_information(M)
    self_rate = float(np.trace(M) / M.sum()) if M.sum() else 0.0
    M_off = M.copy()
    np.fill_diagonal(M_off, 0.0)
    mi_off = mutual_information(M_off)

    rng = np.random.default_rng(seed)
    perm_mi = np.empty(n_perm)
    for i in range(n_perm):
        shuffled = []
        for s in seqs:
            t = list(s)
            rng.shuffle(t)
            shuffled.append(t)
        perm_mi[i] = mutual_information(transition_counts(shuffled, k))
    p_mi = float((np.sum(perm_mi >= mi_real) + 1) / (n_perm + 1))

    perm_idx = rng.permutation(len(seqs))
    n_val = max(1, int(len(seqs) * VAL_FRACTION))
    val_set = set(perm_idx[:n_val].tolist())
    train_seqs = [s for i, s in enumerate(seqs) if i not in val_set]
    val_seqs = [s for i, s in enumerate(seqs) if i in val_set]
    bg_ce, uni_ce, n_eval = bigram_unigram_heldout(train_seqs, val_seqs, k)
    gain = (uni_ce - bg_ce) if (bg_ce is not None and uni_ce is not None) else None

    structure = (p_mi < 0.05) and (gain is not None and gain > 0)
    result = {
        "label": label,
        "status": "completed",
        "k_call_types": k,
        "call_types": types,
        "n_calls": int(len(df_subset)),
        "n_recordings": len(seqs),
        "n_adjacent_pairs": int(n_pairs),
        "adjacent_mi_bits": mi_real,
        "self_transition_rate": self_rate,
        "off_diagonal_mi_bits": mi_off,
        "shuffled_mi_mean_bits": float(perm_mi.mean()),
        "shuffled_mi_std_bits": float(perm_mi.std()),
        "mi_permutation_pvalue": p_mi,
        "heldout_bigram_ce_bits": (float(bg_ce) if bg_ce is not None else None),
        "heldout_unigram_ce_bits": (float(uni_ce) if uni_ce is not None else None),
        "predictive_gain_bits_per_token": (float(gain) if gain is not None else None),
        "heldout_pairs": int(n_eval),
        "sequential_structure": bool(structure),
    }
    return result, M, perm_mi


def make_figure(panels, path):
    n = len(panels)
    fig, axes = plt.subplots(n, 3, figsize=(17, 5 * n))
    if n == 1:
        axes = axes.reshape(1, 3)
    for r, (res, M, perm_mi) in enumerate(panels):
        types = res["call_types"]
        Mn = M / np.clip(M.sum(axis=1, keepdims=True), 1, None)
        im = axes[r, 0].imshow(Mn, aspect="auto", cmap="magma", vmin=0, vmax=1)
        axes[r, 0].set_title(f"{res['label']}\nrow-normalised call-type transitions")
        axes[r, 0].set_xticks(range(len(types)))
        axes[r, 0].set_yticks(range(len(types)))
        axes[r, 0].set_xticklabels(types, rotation=90, fontsize=6)
        axes[r, 0].set_yticklabels(types, fontsize=6)
        axes[r, 0].set_xlabel("next call type")
        axes[r, 0].set_ylabel("current call type")
        fig.colorbar(im, ax=axes[r, 0], fraction=0.046)

        axes[r, 1].hist(perm_mi, bins=40, color="lightgray", edgecolor="gray",
                        label="within-recording order-shuffle null")
        axes[r, 1].axvline(res["adjacent_mi_bits"], color="red", lw=2.5,
                           label=f"real MI={res['adjacent_mi_bits']:.3f}")
        axes[r, 1].set_xlabel("adjacent-pair MI (bits)")
        axes[r, 1].set_ylabel("count")
        axes[r, 1].set_title(f"MI permutation (p={res['mi_permutation_pvalue']:.1e})")
        axes[r, 1].legend(fontsize=8)

        uni_ce = res["heldout_unigram_ce_bits"]
        bg_ce = res["heldout_bigram_ce_bits"]
        axes[r, 2].bar(["unigram", "bigram"], [uni_ce, bg_ce],
                       color=["#888888", "#2a7fb8"])
        axes[r, 2].set_ylabel("held-out cross-entropy (bits/token)")
        axes[r, 2].set_title(f"Predictive gain = {res['predictive_gain_bits_per_token']:.3f} bits/token")
        for i, v in enumerate([uni_ce, bg_ce]):
            axes[r, 2].text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=10)

    plt.suptitle("Rung 4 (validated units): sequential structure of catalogue call types",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default="data/join_tables/call_type_manifest.csv")
    ap.add_argument("--n-perm", type=int, default=1000)
    ap.add_argument("--min-type-count", type=int, default=10)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    man_path = (REPO_ROOT / args.manifest) if not Path(args.manifest).is_absolute() else Path(args.manifest)
    df = pd.read_csv(man_path)
    df = df.dropna(subset=["call_type", "audio_path", "start"])
    df = df[df["call_type"].astype(str).str.strip() != ""]

    print(f"\n{'='*66}")
    print("RUNG 4 (VALIDATED UNITS): CALL-TYPE SEQUENTIAL STRUCTURE")
    print(f"{'='*66}")
    print(f"  manifest rows (labelled): {len(df)}")

    results, panels = [], []
    for label, family, provider in SUBSETS:
        sub = df[(df["call_family"] == family) & (df["provider"] == provider)]
        res, M, perm_mi = analyze_subset(label, sub, args.n_perm, args.min_type_count, args.seed)
        results.append(res)
        print(f"\n  [{label}]  status={res['status']}")
        if res["status"] == "completed":
            print(f"    call types={res['k_call_types']}  calls={res['n_calls']}  "
                  f"recordings={res['n_recordings']}  adjacent pairs={res['n_adjacent_pairs']}")
            print(f"    adjacent-pair MI = {res['adjacent_mi_bits']:.4f} bits  "
                  f"(shuffle null {res['shuffled_mi_mean_bits']:.4f}, p={res['mi_permutation_pvalue']:.1e})")
            print(f"    self-transition rate = {res['self_transition_rate']:.3f}  "
                  f"off-diagonal MI = {res['off_diagonal_mi_bits']:.4f} bits")
            print(f"    held-out bigram {res['heldout_bigram_ce_bits']:.3f} vs unigram "
                  f"{res['heldout_unigram_ce_bits']:.3f} bits/token  "
                  f"(gain {res['predictive_gain_bits_per_token']:.3f})")
            print(f"    VERDICT: sequential structure = {res['sequential_structure']}")
            panels.append((res, M, perm_mi))

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fig_rel = "figures/calltype_sequence.png"
    if panels:
        make_figure(panels, REPO_ROOT / fig_rel)
        print(f"\n  Figure saved: {fig_rel}")

    summary = {
        "rung": 4,
        "analysis": "validated_calltype_first_order_structure",
        "label_source": "DCLDE per-provider annotations (call_type)",
        "n_perm": args.n_perm,
        "min_type_count": args.min_type_count,
        "subsets": results,
        "figure": fig_rel if panels else None,
        "caveat": ("Sequential structure over VALIDATED catalogue call types is the "
                   "production-side prerequisite for combinatorial coding, NOT evidence "
                   "of meaning. Within-recording order-shuffle null holds call composition "
                   "fixed; provider held constant holds recording site fixed."),
    }
    out = REPORTS_DIR / "calltype_sequence_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"  Metrics JSON: reports/calltype_sequence_summary.json")
    print(f"{'='*66}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

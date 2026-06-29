#!/usr/bin/env python3
"""Rung 4: first-order sequential structure in call streams (Markov test).

The masked-LM order test in H3 is underpowered on ~700 encounters and answers a
blurry question. The sharper, standard test for sequential structure in animal
call sequences is whether *consecutive* calls are statistically dependent:
does knowing the current call type reduce uncertainty about the next one beyond
what the marginal (unigram) distribution already explains? [@kershenbaum2024whyanimalstalk]

This script:
  1. Quantises AVES2 embeddings into a balanced k-means call-type vocabulary
     (same scheme as H3) [@hagiwara2023aves].
  2. Builds per-encounter call sequences (grouped by provider+soundfile, ordered
     by onset time).
  3. Measures first-order transition structure two ways:
       (a) mutual information I(call_t ; call_{t+1}) between adjacent calls;
       (b) held-out bigram vs unigram cross-entropy (predictive gain).
  4. Tests significance with a within-encounter order-shuffle permutation null,
     which destroys sequence while preserving each encounter's call composition.

A positive result (MI above the shuffled null, bigram beating unigram out of
sample) is evidence of rule-like sequential structure -- a prerequisite for any
combinatorial / "language-like" claim, NOT evidence of meaning. It is reported
with both positive and null outcomes reported.

Usage:
  python scripts/run_sequence_structure.py --embeddings data/embeddings/aves2_full_labeled.npz \
      --vocab-size 40 --n-perm 1000
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
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
SEED = 0
PCA_COMPONENTS = 32
VAL_FRACTION = 0.2


def quantize(embeddings, k, seed=SEED):
    n_comp = min(PCA_COMPONENTS, embeddings.shape[1], embeddings.shape[0] - 1)
    reduced = PCA(n_components=n_comp, random_state=seed).fit_transform(embeddings)
    km = MiniBatchKMeans(n_clusters=k, random_state=seed, n_init=10,
                         batch_size=4096, max_iter=300)
    return km.fit_predict(reduced).astype(int)


def start_seconds(m, fallback):
    if isinstance(m, dict):
        for f in ("begin_sec", "start_time_s", "FileBeginSec"):
            if f in m:
                try:
                    return float(m[f])
                except (TypeError, ValueError):
                    pass
    return float(fallback)


def build_sequences(call_ids, metadata, min_len=3):
    n = len(call_ids)
    enc = {}
    if metadata is not None and len(metadata) == n:
        for i, m in enumerate(metadata):
            sf = m.get("soundfile", "") if isinstance(m, dict) else ""
            prov = m.get("provider", "") if isinstance(m, dict) else ""
            enc.setdefault(f"{prov}::{sf}", []).append((start_seconds(m, i), i))
    else:
        enc = {"all": [(float(i), i) for i in range(n)]}
    seqs = []
    for rows in enc.values():
        ordered = [i for _, i in sorted(rows, key=lambda r: (r[0], r[1]))]
        if len(ordered) >= min_len:
            seqs.append([int(call_ids[i]) for i in ordered])
    return seqs


def transition_counts(sequences, k):
    M = np.zeros((k, k), dtype=float)
    for s in sequences:
        for a, b in zip(s[:-1], s[1:]):
            M[a, b] += 1
    return M


def mutual_information(M):
    """MI (bits) of the joint adjacent-pair distribution from a count matrix."""
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
    """Held-out cross-entropy (bits/token) of add-alpha bigram vs unigram models."""
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


def main():
    p = argparse.ArgumentParser(description="Rung 4: first-order sequential structure test")
    p.add_argument("--embeddings", required=True)
    p.add_argument("--vocab-size", type=int, default=40)
    p.add_argument("--n-perm", type=int, default=1000)
    p.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args()

    emb_path = Path(args.embeddings)
    if not emb_path.exists():
        print(f"ERROR: {emb_path} not found.")
        return 1

    data = np.load(emb_path, allow_pickle=True)
    embeddings = data["embeddings"]
    metadata = list(data["metadata"]) if "metadata" in data else None
    encoder_name = emb_path.stem.replace("_embeddings", "")

    print(f"\n{'='*64}")
    print(f"RUNG 4: SEQUENTIAL STRUCTURE (MARKOV) -- {encoder_name.upper()}")
    print(f"{'='*64}")
    print(f"  embeddings: {embeddings.shape}")

    k = args.vocab_size
    call_ids = quantize(embeddings, k, args.seed)
    seqs = build_sequences(call_ids, metadata, min_len=3)
    if not seqs:
        print("  ERROR: no sequences.")
        return 1
    lens = [len(s) for s in seqs]
    n_pairs = sum(l - 1 for l in lens)
    print(f"  vocabulary: {k} call types")
    print(f"  encounters: {len(seqs)}  adjacent pairs: {n_pairs}")
    print(f"  seq length: min={min(lens)} max={max(lens)} mean={np.mean(lens):.1f}")

    M = transition_counts(seqs, k)
    mi_real = mutual_information(M)
    print(f"\n  Adjacent-pair mutual information I(t; t+1) = {mi_real:.4f} bits")

    # Is the structure just repetition (bouting), or transitions between DIFFERENT
    # types? Report self-transition rate and MI with the diagonal removed.
    self_rate = float(np.trace(M) / M.sum()) if M.sum() else 0.0
    M_off = M.copy()
    np.fill_diagonal(M_off, 0.0)
    mi_off = mutual_information(M_off)
    print(f"  Self-transition (repeat) rate = {self_rate:.3f}")
    print(f"  Off-diagonal MI (repetition removed) = {mi_off:.4f} bits")

    rng = np.random.default_rng(args.seed)
    perm_mi = np.empty(args.n_perm)
    for i in range(args.n_perm):
        shuffled = []
        for s in seqs:
            t = list(s)
            rng.shuffle(t)
            shuffled.append(t)
        perm_mi[i] = mutual_information(transition_counts(shuffled, k))
    p_mi = (np.sum(perm_mi >= mi_real) + 1) / (args.n_perm + 1)
    print(f"  Order-shuffle null MI = {perm_mi.mean():.4f} +/- {perm_mi.std():.4f}")
    print(f"  Permutation p-value = {p_mi:.2e}")

    perm_idx = rng.permutation(len(seqs))
    n_val = max(1, int(len(seqs) * VAL_FRACTION))
    val_set = set(perm_idx[:n_val].tolist())
    train_seqs = [s for i, s in enumerate(seqs) if i not in val_set]
    val_seqs = [s for i, s in enumerate(seqs) if i in val_set]
    bg_ce, uni_ce, n_eval = bigram_unigram_heldout(train_seqs, val_seqs, k)
    print(f"\n  Held-out bigram CE = {bg_ce:.4f} bits/token")
    print(f"  Held-out unigram CE = {uni_ce:.4f} bits/token")
    gain = (uni_ce - bg_ce) if bg_ce is not None else None
    print(f"  Predictive gain (unigram - bigram) = {gain:.4f} bits/token")

    structure = (p_mi < 0.05) and (gain is not None and gain > 0)
    verdict = ("sequential structure present (transitions non-random AND bigram "
               "predicts out of sample)" if structure
               else "no robust first-order sequential structure detected")
    print(f"\n  VERDICT: {verdict}")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    Mn = M / np.clip(M.sum(axis=1, keepdims=True), 1, None)
    im = axes[0].imshow(Mn, aspect="auto", cmap="magma")
    axes[0].set_title("Row-normalised transition matrix")
    axes[0].set_xlabel("next call type"); axes[0].set_ylabel("current call type")
    fig.colorbar(im, ax=axes[0], fraction=0.046)

    axes[1].hist(perm_mi, bins=40, color="lightgray", edgecolor="gray", label="order-shuffled null")
    axes[1].axvline(mi_real, color="red", lw=2.5, label=f"real MI={mi_real:.3f}")
    axes[1].set_xlabel("adjacent-pair MI (bits)"); axes[1].set_ylabel("count")
    axes[1].set_title(f"Transition MI permutation (p={p_mi:.2e})")
    axes[1].legend(fontsize=8)

    axes[2].bar(["unigram", "bigram"], [uni_ce, bg_ce],
                color=["#888888", "#2a7fb8"])
    axes[2].set_ylabel("held-out cross-entropy (bits/token)")
    axes[2].set_title(f"Predictive gain = {gain:.3f} bits/token")
    for i, v in enumerate([uni_ce, bg_ce]):
        axes[2].text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=10)

    plt.suptitle(f"Rung 4: first-order sequential structure -- {encoder_name.upper()} "
                 f"({k} call types)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig_path = FIGURES_DIR / f"sequence_structure_{encoder_name}.png"
    plt.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Figure saved: {fig_path}")

    results = {
        "rung": 4,
        "analysis": "first_order_markov_structure",
        "encoder": encoder_name,
        "vocab_size": k,
        "n_encounters": len(seqs),
        "n_adjacent_pairs": int(n_pairs),
        "adjacent_mi_bits": mi_real,
        "self_transition_rate": self_rate,
        "off_diagonal_mi_bits": mi_off,
        "shuffled_mi_mean_bits": float(perm_mi.mean()),
        "shuffled_mi_std_bits": float(perm_mi.std()),
        "mi_permutation_pvalue": float(p_mi),
        "heldout_bigram_ce_bits": (float(bg_ce) if bg_ce is not None else None),
        "heldout_unigram_ce_bits": (float(uni_ce) if uni_ce is not None else None),
        "predictive_gain_bits_per_token": (float(gain) if gain is not None else None),
        "sequential_structure": bool(structure),
        "verdict": verdict,
        "caveat": ("Sequential structure is a prerequisite for combinatorial coding, "
                   "NOT evidence of meaning. Tokens are unsupervised k-means call types, "
                   "not validated biological call types."),
        "figure": f"figures/{fig_path.name}",
    }
    out = FIGURES_DIR / f"sequence_structure_{encoder_name}.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"  Metrics JSON: {out}")
    print(f"{'='*64}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

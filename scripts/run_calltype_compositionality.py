#!/usr/bin/env python3
"""Compositional structure beyond first order in validated catalogue call-type
sequences (the combinatorial-structure frontier).

`run_calltype_sequence.py` established *first-order* structure over the validated
catalogue call types (adjacent-pair MI; bigram beats unigram), site held constant
[@ford1989; @filatova2015]. The combinatorial-coding question the comparative
animal-communication literature actually asks - sperm-whale codas [@sharma2024], bonobo and chimpanzee
compositionality [@berthet2025bonobo; @crockford2025] - is whether structure goes
*beyond* first order: does the call two steps back carry information about the next
call that a first-order (Markov) model cannot explain, and are there recurring
multi-call motifs ("candidate phrases") above what pairwise transitions predict?

The decisive methodological point is the NULL. To test for structure *beyond*
first order we compare against **first-order Markov surrogates**: sequences sampled
from the fitted first-order transition matrix, with each recording's length
preserved. These surrogates have, by construction, the same unigram and bigram
statistics as the data, so any excess higher-order structure cannot be a
re-detection of the first-order result, and the (downward) finite-sample bias of
plug-in entropy cancels between data and surrogates.

For each population subset (site held constant) it reports:
  1. Plug-in conditional entropies h1 = H(X), h2 = H(X_t | X_{t-1}),
     h3 = H(X_t | X_{t-1}, X_{t-2}); the second-order reduction delta = h2 - h3 is
     the information the 2-back symbol adds, tested against the Markov-surrogate null.
  2. Held-out predictive gain of an interpolated trigram over a bigram model
     (bits/token), an interpretable effect size for "beyond first order".
  3. Over-represented 3-gram motifs (observed count vs first-order-surrogate
     expectation, z-scored) - candidate multi-call phrases.

Structure beyond first order is a STRONGER combinatorial prerequisite than the
first-order result; it is still NOT semantic compositionality (A+B *means* more
than A,B), which needs meaning/context labels and is out of scope here. Reported
honestly whichever way it comes out.

Usage:
  python scripts/run_calltype_compositionality.py --n-surrogate 1000
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
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
MIN_LEN = 3
VAL_FRACTION = 0.2
N_SPLITS = 10

SUBSETS = [
    ("NRKW N-calls @ dfo_crp", "NRKW", "dfo_crp"),
    ("SRKW S-calls @ vfpa", "SRKW", "vfpa"),
]


def build_sequences(df_subset, type_to_idx):
    seqs = []
    for _, grp in df_subset.groupby("audio_path", sort=False):
        ids = [type_to_idx[t] for t in grp.sort_values(["start", "end"])["call_type"]]
        if len(ids) >= MIN_LEN:
            seqs.append(ids)
    return seqs


def motif_recording_span(seqs, g):
    """How many distinct recordings contain the consecutive 3-gram g (guards
    against a motif being driven by a single encounter)."""
    a, b, c = g
    n = 0
    for s in seqs:
        if any(s[i] == a and s[i + 1] == b and s[i + 2] == c for i in range(len(s) - 2)):
            n += 1
    return n


def counts_123(seqs, k):
    uni = np.zeros(k)
    bi = np.zeros((k, k))
    tri = np.zeros((k, k, k))
    for s in seqs:
        for t in s:
            uni[t] += 1
        for a, b in zip(s[:-1], s[1:]):
            bi[a, b] += 1
        for a, b, c in zip(s[:-2], s[1:-1], s[2:]):
            tri[a, b, c] += 1
    return uni, bi, tri


def _H(counts):
    p = counts[counts > 0]
    p = p / p.sum()
    return float(-(p * np.log2(p)).sum())


def conditional_entropies(uni, bi, tri):
    h1 = _H(uni)
    # h2 = sum_a P(a) H(b|a) = -sum P(a,b) log2 P(b|a)
    Pab = bi / bi.sum() if bi.sum() else bi
    Pb_a = bi / np.clip(bi.sum(1, keepdims=True), 1, None)
    m2 = (Pab > 0) & (Pb_a > 0)
    h2 = float(-(Pab[m2] * np.log2(Pb_a[m2])).sum())
    # h3 = -sum P(a,b,c) log2 P(c|a,b)
    Pabc = tri / tri.sum() if tri.sum() else tri
    Pc_ab = tri / np.clip(tri.sum(2, keepdims=True), 1, None)
    m3 = (Pabc > 0) & (Pc_ab > 0)
    h3 = float(-(Pabc[m3] * np.log2(Pc_ab[m3])).sum())
    return h1, h2, h3


def markov_surrogate(seqs, k, bi, rng):
    """Sample sequences from the fitted first-order transition matrix, preserving
    each recording's length and starting-symbol distribution. Uses cumulative
    transitions + searchsorted for speed."""
    T = bi / np.clip(bi.sum(1, keepdims=True), 1, None)
    uni = bi.sum(0) + 1e-9
    uni = uni / uni.sum()
    dead = bi.sum(1) == 0
    T[dead] = uni
    cumT = np.cumsum(T, axis=1)
    cumT[:, -1] = 1.0
    starts = np.array([s[0] for s in seqs])
    out = []
    for s in seqs:
        n = len(s)
        cur = int(rng.choice(starts))
        seq = [cur]
        u = rng.random(n - 1)
        for j in range(n - 1):
            cur = int(np.searchsorted(cumT[cur], u[j]))
            if cur >= k:
                cur = k - 1
            seq.append(cur)
        out.append(seq)
    return out


def markov_surrogate_per_recording(seqs, k, global_bi, rng):
    """Tighter null: sample each recording from ITS OWN first-order transition
    matrix (backing off to the global matrix for unseen rows), preserving its
    length and starting symbol. Exceeding this null cannot be explained by
    recording-level heterogeneity in first-order dynamics - it requires genuine
    within-recording second-order structure."""
    Tg = global_bi / np.clip(global_bi.sum(1, keepdims=True), 1, None)
    ug = global_bi.sum(0) + 1e-9
    Tg[global_bi.sum(1) == 0] = ug / ug.sum()
    out = []
    for s in seqs:
        br = np.zeros((k, k))
        for a, b in zip(s[:-1], s[1:]):
            br[a, b] += 1
        Tr = br / np.clip(br.sum(1, keepdims=True), 1, None)
        dead = br.sum(1) == 0
        Tr[dead] = Tg[dead]
        cumTr = np.cumsum(Tr, axis=1)
        cumTr[:, -1] = 1.0
        cur = s[0]
        seq = [cur]
        u = rng.random(len(s) - 1)
        for j in range(len(s) - 1):
            cur = int(np.searchsorted(cumTr[cur], u[j]))
            if cur >= k:
                cur = k - 1
            seq.append(cur)
        out.append(seq)
    return out


def interp_trigram_heldout(train, val, k, lam=(0.6, 0.3, 0.1), alpha=0.1, seed=SEED):
    uni, bi, tri = counts_123(train, k)
    uni_p = (uni + alpha) / (uni.sum() + alpha * k)
    bi_p = (bi + alpha) / (bi.sum(1, keepdims=True) + alpha * k)
    tri_p = (tri + alpha) / (tri.sum(2, keepdims=True) + alpha * k)
    l3, l2, l1 = lam
    ll_tri, ll_bi, n = 0.0, 0.0, 0
    for s in val:
        for i in range(2, len(s)):
            a, b, c = s[i - 2], s[i - 1], s[i]
            p_tri = l3 * tri_p[a, b, c] + l2 * bi_p[b, c] + l1 * uni_p[c]
            ll_tri += np.log2(p_tri)
            ll_bi += np.log2(0.7 * bi_p[b, c] + 0.3 * uni_p[c])
            n += 1
    if n == 0:
        return None, None, 0
    return -ll_tri / n, -ll_bi / n, n


def analyze(label, df_subset, n_surr, min_type_count, seed=SEED):
    counts = df_subset["call_type"].value_counts()
    keep = counts[counts >= min_type_count].index.tolist()
    df_subset = df_subset[df_subset["call_type"].isin(keep)].copy()
    types = sorted(df_subset["call_type"].unique())
    t2i = {t: i for i, t in enumerate(types)}
    k = len(types)
    if k < 2:
        return {"label": label, "status": "skipped_too_few_types", "k": k}, None
    seqs = build_sequences(df_subset, t2i)
    if len(seqs) < 5:
        return {"label": label, "status": "skipped_too_few_recordings", "n_recordings": len(seqs)}, None

    uni, bi, tri = counts_123(seqs, k)
    h1, h2, h3 = conditional_entropies(uni, bi, tri)
    delta_obs = h2 - h3

    rng = np.random.default_rng(seed)
    deltas = np.empty(n_surr)        # global first-order null
    deltas_pr = np.empty(n_surr)     # per-recording first-order null (tighter)
    obs_tri = Counter()
    for s in seqs:
        for a, b, c in zip(s[:-2], s[1:-1], s[2:]):
            obs_tri[(a, b, c)] += 1
    obs_keys = list(obs_tri.keys())
    key_idx = np.array(obs_keys) if obs_keys else np.zeros((0, 3), int)
    ssum = np.zeros(len(obs_keys))
    ssq = np.zeros(len(obs_keys))
    for i in range(n_surr):
        sg = markov_surrogate(seqs, k, bi, rng)
        u3, b3, t3 = counts_123(sg, k)
        _, h2s, h3s = conditional_entropies(u3, b3, t3)
        deltas[i] = h2s - h3s
        if len(obs_keys):
            vals = t3[key_idx[:, 0], key_idx[:, 1], key_idx[:, 2]]
            ssum += vals
            ssq += vals * vals
        sgp = markov_surrogate_per_recording(seqs, k, bi, rng)
        up, bp, tp = counts_123(sgp, k)
        _, h2p, h3p = conditional_entropies(up, bp, tp)
        deltas_pr[i] = h2p - h3p
    p_delta = float((np.sum(deltas >= delta_obs) + 1) / (n_surr + 1))
    p_delta_pr = float((np.sum(deltas_pr >= delta_obs) + 1) / (n_surr + 1))

    # held-out interpolated trigram vs bigram (descriptive effect size)
    rng2 = np.random.default_rng(seed + 1)
    tri_ce, bi_ce, gains = [], [], []
    for _ in range(N_SPLITS):
        idx = rng2.permutation(len(seqs))
        nval = max(1, int(len(seqs) * VAL_FRACTION))
        val = [seqs[i] for i in idx[:nval]]
        tr = [seqs[i] for i in idx[nval:]]
        tce, bce, n = interp_trigram_heldout(tr, val, k)
        if tce is not None:
            tri_ce.append(tce); bi_ce.append(bce); gains.append(bce - tce)
    tri_ce_m = float(np.mean(tri_ce)) if tri_ce else None
    bi_ce_m = float(np.mean(bi_ce)) if bi_ce else None
    gain_m = float(np.mean(gains)) if gains else None

    # over-represented 3-gram motifs vs first-order surrogate expectation
    motifs = []
    for j, g in enumerate(obs_keys):
        obs = obs_tri[g]
        mean = ssum[j] / n_surr
        var = max(ssq[j] / n_surr - mean ** 2, 1e-9)
        z = (obs - mean) / np.sqrt(var)
        if obs >= 8 and z > 0:
            motifs.append((g, int(obs), float(mean), float(z)))
    motifs.sort(key=lambda x: -x[3])
    top_motifs = [{"motif": "->".join(types[i] for i in g), "observed": o,
                   "expected_first_order": round(m, 2), "z": round(z, 2),
                   "n_recordings_present": motif_recording_span(seqs, g)}
                  for g, o, m, z in motifs[:10]]

    beyond = (p_delta < 0.05) and (p_delta_pr < 0.05) and (gain_m is not None and gain_m > 0)
    res = {
        "label": label, "status": "completed",
        "k_call_types": k, "n_calls": int(len(df_subset)), "n_recordings": len(seqs),
        "entropy_h1_unigram_bits": round(h1, 4),
        "cond_entropy_h2_first_order_bits": round(h2, 4),
        "cond_entropy_h3_second_order_bits": round(h3, 4),
        "second_order_reduction_delta_bits": round(delta_obs, 4),
        "markov_surrogate_delta_mean": round(float(deltas.mean()), 4),
        "markov_surrogate_delta_std": round(float(deltas.std()), 4),
        "delta_pvalue_vs_markov_global": p_delta,
        "perrec_surrogate_delta_mean": round(float(deltas_pr.mean()), 4),
        "perrec_surrogate_delta_std": round(float(deltas_pr.std()), 4),
        "delta_pvalue_vs_markov_perrecording": p_delta_pr,
        "heldout_trigram_ce_bits": (round(tri_ce_m, 4) if tri_ce_m else None),
        "heldout_bigram_ce_bits": (round(bi_ce_m, 4) if bi_ce_m else None),
        "heldout_gain_beyond_first_order_bits_per_token": (round(gain_m, 4) if gain_m else None),
        "n_surrogate": n_surr,
        "top_motifs_3gram": top_motifs,
        "structure_beyond_first_order": bool(beyond),
    }
    return res, deltas


def make_figure(panels, path, types_by_label):
    n = len(panels)
    fig, axes = plt.subplots(n, 2, figsize=(13, 4.8 * n))
    if n == 1:
        axes = axes.reshape(1, 2)
    for r, (res, deltas) in enumerate(panels):
        axes[r, 0].hist(deltas, bins=40, color="lightgray", edgecolor="gray",
                        label="first-order Markov surrogate")
        axes[r, 0].axvline(res["second_order_reduction_delta_bits"], color="red", lw=2.5,
                           label=f"observed delta={res['second_order_reduction_delta_bits']:.3f}")
        axes[r, 0].set_title(f"{res['label']}\nsecond-order info delta=h2-h3 "
                             f"(global p={res['delta_pvalue_vs_markov_global']:.1e}, "
                             f"per-rec p={res['delta_pvalue_vs_markov_perrecording']:.1e})")
        axes[r, 0].set_xlabel("h2 - h3 (bits)  [info from the 2-back call]")
        axes[r, 0].set_ylabel("count"); axes[r, 0].legend(fontsize=8)

        ms = res["top_motifs_3gram"][:8]
        if ms:
            ax = axes[r, 1]
            ylab = [m["motif"] for m in ms][::-1]
            zs = [m["z"] for m in ms][::-1]
            ax.barh(range(len(zs)), zs, color="#2a7fb8")
            ax.set_yticks(range(len(zs))); ax.set_yticklabels(ylab, fontsize=7)
            ax.set_xlabel("z vs first-order surrogate"); ax.set_title("Top candidate 3-call motifs")
    plt.suptitle("Compositional structure beyond first order in catalogue call types",
                 fontsize=13, fontweight="bold")
    plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default="data/join_tables/call_type_manifest.csv")
    ap.add_argument("--n-surrogate", type=int, default=1000)
    ap.add_argument("--min-type-count", type=int, default=10)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    man = (REPO_ROOT / args.manifest) if not Path(args.manifest).is_absolute() else Path(args.manifest)
    df = pd.read_csv(man).dropna(subset=["call_type", "audio_path", "start"])
    df = df[df["call_type"].astype(str).str.strip() != ""]

    print("\n" + "=" * 70)
    print("COMPOSITIONALITY: STRUCTURE BEYOND FIRST ORDER (catalogue call types)")
    print("=" * 70, flush=True)

    results, panels = [], []
    for label, fam, prov in SUBSETS:
        sub = df[(df["call_family"] == fam) & (df["provider"] == prov)]
        res, deltas = analyze(label, sub, args.n_surrogate, args.min_type_count, args.seed)
        results.append(res)
        print(f"\n[{label}] status={res['status']}", flush=True)
        if res["status"] == "completed":
            print(f"  k={res['k_call_types']} calls={res['n_calls']} recordings={res['n_recordings']}")
            print(f"  h1={res['entropy_h1_unigram_bits']}  h2={res['cond_entropy_h2_first_order_bits']}"
                  f"  h3={res['cond_entropy_h3_second_order_bits']}")
            print(f"  second-order reduction delta=h2-h3 = {res['second_order_reduction_delta_bits']} bits")
            print(f"    vs GLOBAL first-order null {res['markov_surrogate_delta_mean']}"
                  f"+/-{res['markov_surrogate_delta_std']}  p={res['delta_pvalue_vs_markov_global']:.1e}")
            print(f"    vs PER-RECORDING first-order null {res['perrec_surrogate_delta_mean']}"
                  f"+/-{res['perrec_surrogate_delta_std']}  p={res['delta_pvalue_vs_markov_perrecording']:.1e}")
            print(f"  held-out trigram {res['heldout_trigram_ce_bits']} vs bigram {res['heldout_bigram_ce_bits']}"
                  f" bits/token  (gain beyond 1st order = {res['heldout_gain_beyond_first_order_bits_per_token']})")
            print(f"  VERDICT structure_beyond_first_order = {res['structure_beyond_first_order']}")
            if res["top_motifs_3gram"]:
                print("  top candidate 3-call motifs:")
                for m in res["top_motifs_3gram"][:5]:
                    print(f"    {m['motif']:<28} obs={m['observed']} exp={m['expected_first_order']} "
                          f"z={m['z']} in {m['n_recordings_present']}/{res['n_recordings']} recordings")
            panels.append((res, deltas))

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fig_rel = "figures/calltype_compositionality.png"
    if panels:
        make_figure(panels, REPO_ROOT / fig_rel, None)
        print(f"\nFigure: {fig_rel}")

    summary = {
        "analysis": "calltype_compositionality_beyond_first_order",
        "label_source": "DCLDE per-provider annotations (call_type)",
        "null": "first-order Markov surrogates (preserve unigram+bigram stats; bias cancels)",
        "n_surrogate": args.n_surrogate,
        "subsets": results,
        "figure": fig_rel if panels else None,
        "boundary": ("Structure beyond first order is a stronger combinatorial prerequisite "
                     "than the first-order result, tested against first-order Markov surrogates "
                     "so it is not a re-detection of pairwise structure. It is NOT semantic "
                     "compositionality (A+B meaning more than A,B), which needs meaning/context "
                     "labels and is out of scope. Motifs are CANDIDATE phrases, not words."),
    }
    (REPORTS_DIR / "calltype_compositionality_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print("Metrics JSON: reports/calltype_compositionality_summary.json")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Distributional-semantic structure of killer-whale call types: does a call type's
*sequential company* carry information about its *behavioural context*?

Recent comparative work assigns "meaning" to animal calls by distributional semantics
- a call's meaning is inferred from the contexts/company it keeps - in bonobos
[@berthet2025bonobo] and chimpanzees [@crockford2025]. Those studies had per-utterance
context annotations. The public DCLDE corpus does not (it has no behavioural-context
field), so we cannot annotate each call's context directly. Instead we *test the core
distributional hypothesis non-circularly*:

  1. DISTRIBUTIONAL vectors come from SEQUENCE only - each catalogue call type is
     represented by its PPMI-weighted co-occurrence with neighbouring call types within
     a window, built from the validated call-type sequences (site held constant). This
     uses no context labels.
  2. CONTEXT vectors come from INDEPENDENT published field ethograms
     (`call_type_to_context.csv`) [@ford1989; @foote2008; @riesch2008; @yurk2002] - the
     behavioural contexts in which each named call type is documented. This uses no
     acoustics and no sequence.
  3. The BRIDGE: a Mantel test asks whether the distributional-similarity matrix and the
     context-similarity matrix agree above a label-permutation null. A positive result
     means call types that occur in similar sequential company also tend to occur in
     similar behavioural contexts - the distributional hypothesis the finalist primate
     studies *assume*, here *tested* on orca, with the two sides derived from disjoint,
     non-circular sources.

This is a structure<->context association. It is NOT a claim of referential meaning, and
the context labels are human-projected (the umwelt caveat [@kershenbaum2024whyanimalstalk]);
they enter only as an INDEPENDENT validation target, never as a training signal, which is
the unsupervised-plus-validation design recommended for animal-communication decoding.

Usage:
  python scripts/run_calltype_distributional_semantics.py --n-perm 1000 --window 2
"""

from __future__ import annotations

import argparse
import json
import re
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

SUBSETS = [
    ("NRKW N-calls @ dfo_crp", "NRKW", "dfo_crp"),
    ("SRKW S-calls @ vfpa", "SRKW", "vfpa"),
]


def normalize_type(code: str) -> str | None:
    """Map a manifest call-type code (e.g. 'N04', 'N09iii', 'S02i', 'S16/S17') to the
    coarse catalogue label used in the ethogram table (e.g. 'N4', 'N9', 'S2'). Returns
    None for non-standard entries (whistles, transient codes, merged labels)."""
    if not isinstance(code, str):
        return None
    code = code.strip().split("/")[0]  # drop merged 'S16/S17' -> 'S16'
    m = re.match(r"^([NS])0*([0-9]+)", code)  # letter + number, strip leading zeros + subtype suffix
    if not m:
        return None
    return f"{m.group(1)}{int(m.group(2))}"


def build_sequences(df_subset):
    seqs = []
    for _, grp in df_subset.groupby("audio_path", sort=False):
        codes = list(grp.sort_values(["start", "end"])["call_type"])
        if len(codes) >= MIN_LEN:
            seqs.append(codes)
    return seqs


def ppmi_vectors(seqs, types, window):
    """PPMI co-occurrence vectors over a symmetric neighbour window (distance 1..window,
    both directions), excluding the centre token itself."""
    idx = {t: i for i, t in enumerate(types)}
    k = len(types)
    co = np.zeros((k, k))
    for s in seqs:
        n = len(s)
        for i in range(n):
            ci = idx.get(s[i])
            if ci is None:
                continue
            for d in range(1, window + 1):
                for j in (i - d, i + d):
                    if 0 <= j < n:
                        cj = idx.get(s[j])
                        if cj is not None:
                            co[ci, cj] += 1.0
    total = co.sum()
    if total == 0:
        return None
    Pij = co / total
    Pi = Pij.sum(1, keepdims=True)
    Pj = Pij.sum(0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        pmi = np.log2(Pij / (Pi * Pj))
    ppmi = np.where(np.isfinite(pmi) & (pmi > 0), pmi, 0.0)
    return ppmi


def cosine_matrix(X):
    norm = np.linalg.norm(X, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    Xn = X / norm
    return Xn @ Xn.T


def load_context_vectors(path, population):
    """Build a context-feature vector per coarse call type from the published ethogram
    table. Only behavioural contexts are used; pure identity-signalling rows are kept as
    their own feature so identity calls do not masquerade as behavioural context."""
    ctx = pd.read_csv(path)
    ctx = ctx[ctx["population"].isin([population, "both"])] if "population" in ctx.columns else ctx
    vecs: dict[str, dict[str, float]] = {}
    for _, r in ctx.iterrows():
        t = normalize_type(str(r.get("call_type", "")))
        if t is None:
            continue
        for col, w in (("primary_context", 1.0), ("secondary_context", 0.5)):
            val = r.get(col)
            if isinstance(val, str) and val.strip():
                vecs.setdefault(t, {}).setdefault(val.strip(), 0.0)
                vecs[t][val.strip()] += w
    return vecs


def mantel(D1, D2, n_perm, rng):
    """Mantel test on the upper triangle of two similarity matrices (Pearson r),
    label-permutation null on one matrix."""
    k = D1.shape[0]
    iu = np.triu_indices(k, k=1)
    a = D1[iu]
    b = D2[iu]
    if a.std() == 0 or b.std() == 0:
        return None, None
    r_obs = float(np.corrcoef(a, b)[0, 1])
    count = 0
    for _ in range(n_perm):
        p = rng.permutation(k)
        bp = D2[np.ix_(p, p)][iu]
        if np.corrcoef(a, bp)[0, 1] >= r_obs:
            count += 1
    p_val = (count + 1) / (n_perm + 1)
    return r_obs, float(p_val)


def analyze(label, population, df_subset, ctx_path, window, n_perm, min_count, seed):
    counts = df_subset["call_type"].value_counts()
    keep = counts[counts >= min_count].index.tolist()
    df_subset = df_subset[df_subset["call_type"].isin(keep)].copy()
    # normalise to coarse codes and keep only standard discrete call types
    df_subset["coarse"] = df_subset["call_type"].map(normalize_type)
    df_subset = df_subset.dropna(subset=["coarse"])
    seqs_coarse = [
        [normalize_type(c) for c in s if normalize_type(c) is not None]
        for s in build_sequences(df_subset)
    ]
    seqs_coarse = [s for s in seqs_coarse if len(s) >= MIN_LEN]
    dist_types = sorted({t for s in seqs_coarse for t in s})
    if len(dist_types) < 4:
        return {"label": label, "status": "skipped_too_few_types", "n_types": len(dist_types)}, None

    ppmi = ppmi_vectors(seqs_coarse, dist_types, window)
    if ppmi is None:
        return {"label": label, "status": "skipped_no_cooccurrence"}, None
    Dist = cosine_matrix(ppmi)

    ctx_vecs = load_context_vectors(ctx_path, population)
    shared = [t for t in dist_types if t in ctx_vecs]
    if len(shared) < 4:
        return {"label": label, "status": "skipped_too_few_shared_context_types",
                "n_distributional_types": len(dist_types), "n_shared": len(shared),
                "shared_types": shared}, None

    ctx_feats = sorted({f for t in shared for f in ctx_vecs[t]})
    Cmat = np.array([[ctx_vecs[t].get(f, 0.0) for f in ctx_feats] for t in shared])
    Ctx = cosine_matrix(Cmat)

    sidx = [dist_types.index(t) for t in shared]
    Dist_s = Dist[np.ix_(sidx, sidx)]

    rng = np.random.default_rng(seed)
    r_obs, p_val = mantel(Dist_s, Ctx, n_perm, rng)

    iu = np.triu_indices(len(shared), k=1)
    res = {
        "label": label, "status": "completed", "population": population,
        "window": window, "n_perm": n_perm,
        "n_distributional_types": len(dist_types),
        "n_shared_context_types": len(shared),
        "shared_types": shared,
        "context_features": ctx_feats,
        "mantel_r_distribution_vs_context": (round(r_obs, 4) if r_obs is not None else None),
        "mantel_pvalue": p_val,
        "n_pairs": int(len(iu[0])),
        "distribution_vs_context_positive": bool(r_obs is not None and p_val is not None and p_val < 0.05 and r_obs > 0),
        "_dist_pairs": Dist_s[iu].tolist(),
        "_ctx_pairs": Ctx[iu].tolist(),
        "_null_r": None,
    }
    return res, (Dist_s, Ctx, shared)


def make_figure(panels, path):
    n = len(panels)
    fig, axes = plt.subplots(n, 2, figsize=(12, 4.6 * n))
    if n == 1:
        axes = axes.reshape(1, 2)
    for r, (res, mats) in enumerate(panels):
        a = np.array(res["_dist_pairs"]); b = np.array(res["_ctx_pairs"])
        axes[r, 0].scatter(a, b, s=18, alpha=0.6, color="#2a7fb8")
        axes[r, 0].set_xlabel("distributional similarity (PPMI cosine, from sequence)")
        axes[r, 0].set_ylabel("behavioural-context similarity\n(independent ethograms)")
        axes[r, 0].set_title(f"{res['label']}\nMantel r={res['mantel_r_distribution_vs_context']} "
                             f"(p={res['mantel_pvalue']:.1e}, {res['n_shared_context_types']} types)")
        # context-similarity heatmap over shared types
        _, Ctx, shared = mats
        im = axes[r, 1].imshow(Ctx, cmap="magma", vmin=0, vmax=1)
        axes[r, 1].set_xticks(range(len(shared))); axes[r, 1].set_xticklabels(shared, rotation=90, fontsize=7)
        axes[r, 1].set_yticks(range(len(shared))); axes[r, 1].set_yticklabels(shared, fontsize=7)
        axes[r, 1].set_title("context similarity (shared types)")
        fig.colorbar(im, ax=axes[r, 1], fraction=0.046)
    plt.suptitle("Distributional structure vs. independent behavioural context (call types)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default="data/join_tables/call_type_manifest.csv")
    ap.add_argument("--context", default="data/join_tables/call_type_to_context.csv")
    ap.add_argument("--window", type=int, default=2)
    ap.add_argument("--n-perm", type=int, default=1000)
    ap.add_argument("--min-type-count", type=int, default=10)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    man = (REPO_ROOT / args.manifest) if not Path(args.manifest).is_absolute() else Path(args.manifest)
    ctx_path = (REPO_ROOT / args.context) if not Path(args.context).is_absolute() else Path(args.context)
    df = pd.read_csv(man).dropna(subset=["call_type", "audio_path", "start"])
    df = df[df["call_type"].astype(str).str.strip() != ""]

    print("\n" + "=" * 72)
    print("DISTRIBUTIONAL SEMANTICS: call-type sequential structure vs. behavioural context")
    print("=" * 72, flush=True)

    results, panels = [], []
    for label, fam, prov in SUBSETS:
        sub = df[(df["call_family"] == fam) & (df["provider"] == prov)]
        res, mats = analyze(label, fam, sub, ctx_path, args.window, args.n_perm,
                            args.min_type_count, args.seed)
        results.append(res)
        print(f"\n[{label}] status={res['status']}", flush=True)
        if res["status"] == "completed":
            print(f"  distributional types: {res['n_distributional_types']}  "
                  f"shared with ethogram: {res['n_shared_context_types']}  ({', '.join(res['shared_types'])})")
            print(f"  context features: {', '.join(res['context_features'])}")
            print(f"  Mantel r(distribution, context) = {res['mantel_r_distribution_vs_context']}  "
                  f"p = {res['mantel_pvalue']:.1e}  over {res['n_pairs']} type-pairs")
            print(f"  VERDICT distribution<->context association: {res['distribution_vs_context_positive']}")
            panels.append((res, mats))

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fig_rel = "figures/calltype_distributional_semantics.png"
    if panels:
        make_figure(panels, REPO_ROOT / fig_rel)
        print(f"\nFigure: {fig_rel}")

    # strip large helper arrays from the persisted summary
    clean = []
    for res in results:
        clean.append({k: v for k, v in res.items() if not k.startswith("_")})
    summary = {
        "analysis": "calltype_distributional_semantics",
        "method": ("PPMI co-occurrence vectors from validated call-type sequences (site held "
                   "constant) vs. independent published-ethogram behavioural-context vectors; "
                   "Mantel test with a label-permutation null."),
        "distributional_source": "DCLDE per-provider annotations (call_type sequences)",
        "context_source": "published field ethograms (call_type_to_context.csv) [@ford1989; @foote2008; @riesch2008; @yurk2002]",
        "window": args.window, "n_perm": args.n_perm, "min_type_count": args.min_type_count,
        "subsets": clean,
        "boundary": ("Tests the distributional hypothesis (similar sequential company -> similar "
                     "behavioural context) NON-CIRCULARLY: distribution from sequence only, context "
                     "from independent ethograms only. A positive Mantel r is a structure<->context "
                     "ASSOCIATION, NOT referential meaning. Context labels are human-projected (umwelt "
                     "caveat) and coarse (type-level, not per-utterance), and the shared-type sample is "
                     "small; reported honestly whichever way it comes out."),
    }
    (REPORTS_DIR / "calltype_distributional_semantics_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print("Metrics JSON: reports/calltype_distributional_semantics_summary.json")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

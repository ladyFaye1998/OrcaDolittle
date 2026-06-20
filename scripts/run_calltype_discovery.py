#!/usr/bin/env python3
"""Rung 1 prototype: unsupervised call-type discovery WITHIN one ecotype.

Ecotype discrimination (H1/H4) only shows that populations are acoustically
separable. The next rung toward a production-criterion claim is showing that a
single population carries a *discrete, stereotyped repertoire* -- candidate
call types -- in the sense of the Ford/Filatova catalogues [@ford1989;
@filatova2015]. This script discovers that structure unsupervised, but it does
NOT assert biological call types: without ground-truth type labels the clusters
are candidates only, and the dominant risk is that they encode recording site
rather than call type.

So the script does two things that make the result interpretable:
  1. Restricts to one ecotype (default SRKW), and optionally to one provider,
     so cross-population and cross-site variance cannot masquerade as types.
  2. Reports a PROVIDER-PURITY guard: if discovered clusters collapse onto
     single providers (high cluster->provider NMI, high mean dominant-provider
     fraction), they are site artifacts, not a repertoire.

It also reports subsample stability (mean pairwise ARI across resamples).

Usage:
  python scripts/run_calltype_discovery.py --embeddings data/embeddings/aves2_full_labeled.npz --ecotype SRKW
  python scripts/run_calltype_discovery.py --embeddings data/embeddings/aves2_full_labeled.npz --ecotype SRKW --single-provider
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.preprocessing import LabelEncoder, StandardScaler

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
SEED = 0


def load_corpus(emb_path: Path):
    data = np.load(emb_path, allow_pickle=True)
    emb = data["embeddings"]
    labels = np.array([str(x) for x in data["labels"]])
    if "metadata" in data and len(data["metadata"]) == len(emb):
        providers = np.array([str(m.get("provider", "NA")) for m in data["metadata"]])
    else:
        providers = np.array(["NA"] * len(emb))
    return emb, labels, providers


def provider_purity(cluster_labels: np.ndarray, providers: np.ndarray):
    """Mean dominant-provider fraction over real clusters (noise excluded)."""
    fracs = []
    per_cluster = {}
    for c in sorted(set(cluster_labels)):
        if c == -1:
            continue
        prov = providers[cluster_labels == c]
        top, cnt = Counter(prov.tolist()).most_common(1)[0]
        frac = cnt / len(prov)
        fracs.append(frac)
        per_cluster[int(c)] = {"size": int(len(prov)), "dominant_provider": top,
                               "dominant_fraction": float(frac)}
    return (float(np.mean(fracs)) if fracs else None), per_cluster


def subsample_stability(reduced, min_cluster_size, min_samples, frac=0.8, reps=5):
    import hdbscan
    rng = np.random.default_rng(SEED)
    n = len(reduced)
    aris = []
    base = hdbscan.HDBSCAN(min_cluster_size=int(min_cluster_size),
                           min_samples=int(min_samples)).fit_predict(reduced)
    for _ in range(reps):
        idx = rng.choice(n, size=int(frac * n), replace=False)
        sub = hdbscan.HDBSCAN(min_cluster_size=int(min_cluster_size),
                              min_samples=int(min_samples)).fit_predict(reduced[idx])
        aris.append(adjusted_rand_score(base[idx], sub))
    return float(np.mean(aris)), float(np.std(aris))


def discover(emb_path: Path, ecotype: str, single_provider: bool,
             min_cluster_size: int, min_samples: int, n_components: int):
    import hdbscan

    emb, labels, providers = load_corpus(emb_path)
    mask = labels == ecotype
    if mask.sum() == 0:
        print(f"ERROR: no rows for ecotype={ecotype}. Available: {sorted(set(labels))}")
        return 1

    X = emb[mask]
    prov = providers[mask]
    chosen_provider = None
    if single_provider:
        top, _ = Counter(prov.tolist()).most_common(1)[0]
        chosen_provider = top
        sub = prov == top
        X, prov = X[sub], prov[sub]

    print(f"\n{'='*64}")
    print(f"RUNG 1: CALL-TYPE DISCOVERY WITHIN ECOTYPE={ecotype}")
    print(f"{'='*64}")
    print(f"  segments: {len(X):,}   providers present: {dict(Counter(prov.tolist()))}")
    if chosen_provider:
        print(f"  restricted to single provider: {chosen_provider} (site confound removed)")

    Xs = StandardScaler().fit_transform(X)
    n_comp = min(n_components, Xs.shape[1], Xs.shape[0] - 1)
    reduced = PCA(n_components=n_comp, random_state=SEED).fit_transform(Xs)

    cl = hdbscan.HDBSCAN(min_cluster_size=int(min_cluster_size),
                         min_samples=int(min_samples)).fit_predict(reduced)
    n_clusters = len(set(cl)) - (1 if -1 in cl else 0)
    n_noise = int((cl == -1).sum())
    print(f"\n  PCA(nc={n_comp}) + HDBSCAN(mcs={min_cluster_size}, ms={min_samples})")
    print(f"  candidate clusters = {n_clusters}   noise = {n_noise} ({n_noise/len(cl):.1%})")

    sizes = sorted((cnt for c, cnt in Counter(cl.tolist()).items() if c != -1), reverse=True)
    print(f"  cluster sizes (top 10): {sizes[:10]}")

    mean_purity, per_cluster = provider_purity(cl, prov)
    n_prov = len(set(prov.tolist()))
    if n_prov > 1:
        prov_enc = LabelEncoder().fit_transform(prov)
        cl_all = cl.copy()
        if (cl_all == -1).any():
            cl_all[cl_all == -1] = cl_all.max() + 1
        nmi_prov = normalized_mutual_info_score(prov_enc, cl_all)
        print(f"\n  PROVIDER-PURITY GUARD ({n_prov} providers):")
        print(f"    cluster->provider NMI = {nmi_prov:.3f}  (high => clusters track site, not call type)")
        print(f"    mean dominant-provider fraction = {mean_purity:.3f}")
    else:
        nmi_prov = None
        print(f"\n  PROVIDER-PURITY GUARD: single provider only -> site confound removed by design.")

    stab_mean, stab_std = subsample_stability(reduced, min_cluster_size, min_samples)
    print(f"\n  STABILITY (subsample ARI, 80%, 5 reps) = {stab_mean:.3f} +/- {stab_std:.3f}")

    fig_path = make_figure(reduced, cl, ecotype, chosen_provider, n_clusters,
                           nmi_prov, mean_purity, stab_mean)

    interp = []
    if chosen_provider is None and mean_purity is not None and mean_purity > 0.8:
        interp.append(f"clusters are {mean_purity:.0%} dominated by a single provider; "
                      "they track recording site, not call type")
    if chosen_provider is None and nmi_prov is not None and nmi_prov > 0.5:
        interp.append("high cluster->provider NMI; site confound present")
    if n_clusters > 0 and sizes and sizes[0] / max(int(len(X) - n_noise), 1) > 0.7:
        interp.append("one cluster dominates the non-noise mass; no resolved multi-type repertoire")
    if n_noise / len(cl) > 0.6:
        interp.append(f"{n_noise/len(cl):.0%} of segments are noise; most calls are unclustered")
    if stab_mean < 0.5:
        interp.append("low subsample stability; cluster solution is unstable")
    if not interp:
        interp.append("clusters are stable and not provider-dominated; candidate repertoire structure")

    results = {
        "rung": 1,
        "analysis": "within_ecotype_calltype_discovery",
        "ecotype": ecotype,
        "single_provider": (chosen_provider if chosen_provider else None),
        "n_segments": int(len(X)),
        "n_candidate_clusters": int(n_clusters),
        "n_noise": n_noise,
        "noise_fraction": float(n_noise / len(cl)),
        "cluster_sizes_desc": sizes,
        "cluster_to_provider_nmi": (float(nmi_prov) if nmi_prov is not None else None),
        "mean_dominant_provider_fraction": (float(mean_purity) if mean_purity is not None else None),
        "subsample_stability_ari_mean": stab_mean,
        "subsample_stability_ari_std": stab_std,
        "per_cluster_provider": per_cluster,
        "interpretation": "; ".join(interp),
        "caveat": ("Unsupervised candidate clusters; NOT validated against Ford/Filatova "
                   "call-type catalogues. A repertoire claim requires labelled call types."),
        "figure": f"figures/{Path(fig_path).name}",
    }
    out = FIGURES_DIR / f"calltype_discovery_{ecotype.lower()}{'_single' if chosen_provider else ''}.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n  Metrics JSON: {out}")
    print(f"  Interpretation: {results['interpretation']}")
    print(f"{'='*64}")
    return 0


def make_figure(reduced, cl, ecotype, chosen_provider, n_clusters,
                nmi_prov, mean_purity, stab_mean):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    emb2d = reduced[:, :2]
    fig, ax = plt.subplots(figsize=(8, 6.5))
    uniq = sorted(set(cl))
    cmap = plt.cm.tab20(np.linspace(0, 1, max(len(uniq), 1)))
    for i, c in enumerate(uniq):
        m = cl == c
        ax.scatter(emb2d[m, 0], emb2d[m, 1], c=[cmap[i]], s=14,
                   alpha=0.6 if c >= 0 else 0.08,
                   label=(f"cluster {c}" if c >= 0 else "noise"))
    ax.set_xlabel("PC 1"); ax.set_ylabel("PC 2")
    title = f"Candidate call-type clusters within {ecotype} (k={n_clusters})"
    if chosen_provider:
        title += f"\nsingle provider: {chosen_provider}"
    sub = f"stability ARI={stab_mean:.2f}"
    if nmi_prov is not None:
        sub += f"  |  cluster->provider NMI={nmi_prov:.2f}"
    if mean_purity is not None:
        sub += f"  |  mean dom-provider frac={mean_purity:.2f}"
    ax.set_title(title + "\n" + sub, fontsize=11)
    if n_clusters <= 12:
        ax.legend(fontsize=7, markerscale=1.5, ncol=2)
    plt.tight_layout()
    path = FIGURES_DIR / f"calltype_discovery_{ecotype.lower()}{'_single' if chosen_provider else ''}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Figure saved: {path}")
    return path


def main():
    p = argparse.ArgumentParser(description="Rung 1: within-ecotype call-type discovery")
    p.add_argument("--embeddings", required=True)
    p.add_argument("--ecotype", default="SRKW")
    p.add_argument("--single-provider", action="store_true",
                   help="restrict to the most-represented provider to remove the site confound")
    p.add_argument("--min-cluster-size", type=int, default=30)
    p.add_argument("--min-samples", type=int, default=5)
    p.add_argument("--n-components", type=int, default=20)
    args = p.parse_args()

    emb_path = Path(args.embeddings)
    if not emb_path.exists():
        print(f"ERROR: {emb_path} not found.")
        return 1
    return discover(emb_path, args.ecotype, args.single_provider,
                    args.min_cluster_size, args.min_samples, args.n_components)


if __name__ == "__main__":
    sys.exit(main())

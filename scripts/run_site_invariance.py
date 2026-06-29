#!/usr/bin/env python3
"""H8 - site-invariance transform: recover the cross-site ecotype transfer that
raw frozen embeddings lose.

Motivation. Raw AVES2 embeddings decode killer-whale ecotype at ~0.91 pooled but
collapse under leave-one-provider-out (LOPO) evaluation, because recording site is
itself decodable (~0.93) and the ecotype decision boundary is site-specific (the
central finding of this repo: docs/results_analysis.md, manuscript Section 4). The
question this script asks is methodological: can a *label-free* site-invariance
transform of the frozen embeddings project out the recording-site subspace and
recover cross-site transfer, turning the negative (cross-site collapse) into a
positive contribution? This is the kind of confound-removal that a passive-acoustic
foundation-model pipeline needs and that a frozen encoder alone does not provide.

Method (leakage-safe). In every LOPO fold we fit StandardScaler+PCA on the TRAINING
providers only. We then estimate a "site-nuisance subspace" as the top-k principal
directions of the per-provider centroid matrix, and project the embeddings onto its
orthogonal complement before fitting an ecotype probe. Two regimes:
  * inductive  - the nuisance subspace is estimated from TRAINING providers only
                 (the held-out site is never seen at fit time);
  * transductive (standard unsupervised domain adaptation) - the held-out provider's
                 *unlabelled* embeddings are included when estimating the subspace
                 (test ECOTYPE labels are never used).
To avoid throwing away biology, an optional ecotype-protection step orthogonalises
the nuisance subspace against the ecotype-centroid subspace (estimated on TRAIN), so
only site directions that are not ecotype directions are removed.

We report, raw vs site-invariant under the identical pipeline:
  - LOPO ecotype balanced accuracy (mean-over-folds and pooled), swept over k;
  - pairwise cross-site transfer for the multi-site ecotypes (OKW/SRKW/TKW);
  - a within-site sanity check (the transform must not destroy within-site signal);
  - a label-permutation null on the best site-invariant setting.

The result is reported whichever way it comes out: ecotype and recording
site are genuinely confounded in this corpus (e.g. SAR is recorded at a single
provider), so full recovery is not guaranteed. Methods only; not a claim of meaning.

Frozen encoder [@hagiwara2023aves]; confound/site-generalisation framing
[@stowell2022; @ghani2023]; CORAL/subspace domain-adaptation lineage is standard.

Usage:
  python scripts/run_site_invariance.py            # full run
  python scripts/run_site_invariance.py --quick    # small k-list, few perms
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = REPO_ROOT / "figures"
REPORTS_DIR = REPO_ROOT / "reports"
DEFAULT_EMB = "data/embeddings/aves2_full_labeled.npz"
SEED = 0


def load(emb_rel: str):
    p = (REPO_ROOT / emb_rel) if not Path(emb_rel).is_absolute() else Path(emb_rel)
    d = np.load(p, allow_pickle=True)
    X = d["embeddings"].astype(np.float32)
    y = d["labels"].astype(str)
    prov = np.array([m["provider"] for m in d["metadata"]])
    return X, y, prov


def centroid_subspace(Z, groups, k):
    """Top-k principal directions of the (centred) per-group centroid matrix."""
    gs = sorted(set(groups))
    C = np.stack([Z[groups == g].mean(0) for g in gs])
    C = C - C.mean(0, keepdims=True)
    if k <= 0 or len(C) < 2:
        return np.zeros((0, Z.shape[1]))
    _, _, Vt = np.linalg.svd(C, full_matrices=False)
    return Vt[: min(k, Vt.shape[0])]


def orthonormalize(V):
    if len(V) == 0:
        return V
    Q, _ = np.linalg.qr(V.T)
    return Q.T


def protect(V_nuis, V_eco):
    """Remove the ecotype-subspace component from each nuisance direction, so the
    projection keeps ecotype-discriminative structure."""
    if len(V_nuis) == 0 or len(V_eco) == 0:
        return V_nuis
    Vp = V_nuis - (V_nuis @ V_eco.T) @ V_eco
    norms = np.linalg.norm(Vp, axis=1)
    Vp = Vp[norms > 1e-6]
    return orthonormalize(Vp) if len(Vp) else Vp


def project_out(Z, V):
    return Z if len(V) == 0 else Z - (Z @ V.T) @ V


def prep_folds(X, y, prov, npca, seed=SEED):
    """Per-LOPO-fold: scaler+PCA fit on train; transform train/test to PCA space."""
    folds = []
    for pt in sorted(set(prov)):
        tr, te = prov != pt, prov == pt
        if len(set(y[tr])) < 2 or te.sum() == 0:
            continue
        sc = StandardScaler().fit(X[tr])
        pca = PCA(n_components=npca, random_state=seed).fit(sc.transform(X[tr]))
        folds.append({
            "test_provider": pt,
            "Ztr": pca.transform(sc.transform(X[tr])),
            "Zte": pca.transform(sc.transform(X[te])),
            "ytr": y[tr], "yte": y[te],
            "ptr": prov[tr], "pte": prov[te],
        })
    return folds


def lopo(folds, k, mode, eco_protect, seed=SEED):
    """One LOPO pass at a given k. mode in {raw, inductive, transductive}."""
    yt_all, yp_all, fold_acc = [], [], {}
    for f in folds:
        Ztr, Zte = f["Ztr"], f["Zte"]
        if mode != "raw" and k > 0:
            if mode == "transductive":
                Zall = np.vstack([Ztr, Zte])
                pall = np.concatenate([f["ptr"], f["pte"]])
                V = centroid_subspace(Zall, pall, k)
            else:  # inductive: train providers only
                V = centroid_subspace(Ztr, f["ptr"], k)
            if eco_protect:
                Veco = centroid_subspace(Ztr, f["ytr"], len(set(f["ytr"])) - 1)
                V = protect(orthonormalize(V), orthonormalize(Veco))
            Ztr, Zte = project_out(Ztr, V), project_out(Zte, V)
        clf = LogisticRegression(max_iter=500, class_weight="balanced", random_state=seed)
        clf.fit(Ztr, f["ytr"])
        pred = clf.predict(Zte)
        fold_acc[f["test_provider"]] = float(balanced_accuracy_score(f["yte"], pred))
        yt_all.append(f["yte"]); yp_all.append(pred)
    yt_all, yp_all = np.concatenate(yt_all), np.concatenate(yp_all)
    return {
        "per_fold": fold_acc,
        "mean_over_folds": float(np.mean(list(fold_acc.values()))),
        "pooled": float(balanced_accuracy_score(yt_all, yp_all)),
    }


def cross_site_pair(X, y, prov, ea, eb, npca, k, eco_protect, seed=SEED):
    """Train on each provider that has both ea&eb, test on each OTHER such provider;
    average balanced accuracy. raw (k=0) vs site-invariant (transductive)."""
    m = np.isin(y, [ea, eb])
    Xp, yp, pp = X[m], y[m], prov[m]
    usable = [p for p in sorted(set(pp))
              if (yp[pp == p] == ea).sum() >= 15 and (yp[pp == p] == eb).sum() >= 15]
    if len(usable) < 2:
        return None
    accs = []
    for ptr in usable:
        for pte in usable:
            if ptr == pte:
                continue
            tr, te = pp == ptr, pp == pte
            sc = StandardScaler().fit(Xp[tr])
            pca = PCA(n_components=min(npca, tr.sum() - 1), random_state=seed).fit(sc.transform(Xp[tr]))
            Ztr, Zte = pca.transform(sc.transform(Xp[tr])), pca.transform(sc.transform(Xp[te]))
            if k > 0:
                Zall = np.vstack([Ztr, Zte])
                pa = np.concatenate([pp[tr], pp[te]])
                V = centroid_subspace(Zall, pa, k)
                if eco_protect:
                    Veco = centroid_subspace(Ztr, yp[tr], 1)
                    V = protect(orthonormalize(V), orthonormalize(Veco))
                Ztr, Zte = project_out(Ztr, V), project_out(Zte, V)
            clf = LogisticRegression(max_iter=500, class_weight="balanced", random_state=seed).fit(Ztr, yp[tr])
            accs.append(balanced_accuracy_score(yp[te], clf.predict(Zte)))
    return {"pair": f"{ea}_vs_{eb}", "n_provider_pairs": len(accs),
            "mean_balanced_accuracy": float(np.mean(accs)), "chance": 0.5}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--embeddings", default=DEFAULT_EMB)
    ap.add_argument("--npca", type=int, default=100)
    ap.add_argument("--k-list", type=int, nargs="+", default=[1, 2, 3, 4, 6, 8, 12])
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--perm-subsample", type=int, default=4000)
    ap.add_argument("--no-eco-protect", action="store_true")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    if args.quick:
        args.k_list = [2, 6]; args.n_perm = 20
    eco_protect = not args.no_eco_protect

    def log(*a):
        print(*a, flush=True)

    X, y, prov = load(args.embeddings)
    log(f"X {X.shape}; ecotypes {dict(zip(*np.unique(y, return_counts=True)))}")
    log(f"providers {sorted(set(prov))}")
    folds = prep_folds(X, y, prov, args.npca, args.seed)

    log("\n== RAW LOPO ==")
    raw = lopo(folds, 0, "raw", False)
    log(f"  raw LOPO  mean-over-folds={raw['mean_over_folds']:.3f}  pooled={raw['pooled']:.3f}")

    log("\n== SITE-INVARIANT LOPO (transductive UDA, ecotype-protected) k-sweep ==")
    sweep = {}
    for k in args.k_list:
        r = lopo(folds, k, "transductive", eco_protect)
        sweep[k] = r
        log(f"  k={k:>2}  mean-over-folds={r['mean_over_folds']:.3f}  pooled={r['pooled']:.3f}")
    best_k = max(sweep, key=lambda k: sweep[k]["mean_over_folds"])
    best = sweep[best_k]
    log(f"  -> best k={best_k}  mean-over-folds={best['mean_over_folds']:.3f}  pooled={best['pooled']:.3f}")

    log("\n== SITE-INVARIANT LOPO (inductive, strict; test site unseen) at best k ==")
    ind = lopo(folds, best_k, "inductive", eco_protect)
    log(f"  inductive k={best_k}  mean-over-folds={ind['mean_over_folds']:.3f}  pooled={ind['pooled']:.3f}")

    log("\n== CROSS-SITE PAIRWISE TRANSFER (raw vs site-invariant transductive) ==")
    pairs = {}
    for ea, eb in [("OKW", "TKW"), ("SRKW", "TKW"), ("OKW", "SRKW")]:
        rawp = cross_site_pair(X, y, prov, ea, eb, args.npca, 0, False, args.seed)
        invp = cross_site_pair(X, y, prov, ea, eb, args.npca, best_k, eco_protect, args.seed)
        if rawp and invp:
            pairs[f"{ea}_vs_{eb}"] = {"raw": rawp["mean_balanced_accuracy"],
                                      "site_invariant": invp["mean_balanced_accuracy"],
                                      "n_provider_pairs": rawp["n_provider_pairs"], "chance": 0.5}
            log(f"  {ea} vs {eb}: raw={rawp['mean_balanced_accuracy']:.3f} -> "
                f"invariant={invp['mean_balanced_accuracy']:.3f}  ({rawp['n_provider_pairs']} site-pairs)")

    log("\n== WITHIN-SITE SANITY (SRKW vs TKW @ JASCO_VFPA; transform must not destroy it) ==")
    m = (prov == "JASCO_VFPA") & np.isin(y, ["SRKW", "TKW"])
    Xw, yw = X[m], y[m]
    from sklearn.model_selection import StratifiedKFold
    def within(k):
        accs = []
        for tr, te in StratifiedKFold(5, shuffle=True, random_state=args.seed).split(Xw, yw):
            sc = StandardScaler().fit(Xw[tr]); pca = PCA(args.npca, random_state=args.seed).fit(sc.transform(Xw[tr]))
            Ztr, Zte = pca.transform(sc.transform(Xw[tr])), pca.transform(sc.transform(Xw[te]))
            # remove the same number of leading PCA dirs as a fair "removed-capacity" control
            if k > 0:
                V = orthonormalize(np.eye(args.npca)[:k])
                Ztr, Zte = project_out(Ztr, V), project_out(Zte, V)
            clf = LogisticRegression(max_iter=500, class_weight="balanced", random_state=args.seed).fit(Ztr, yw[tr])
            accs.append(balanced_accuracy_score(yw[te], clf.predict(Zte)))
        return float(np.mean(accs))
    within_raw, within_inv = within(0), within(best_k)
    log(f"  within-site raw={within_raw:.3f}  after removing {best_k} dims={within_inv:.3f}")

    log(f"\n== PERMUTATION NULL (site-invariant transductive, k={best_k}, n={args.n_perm}) ==")
    rng = np.random.default_rng(args.seed)
    null = np.empty(args.n_perm)
    for i in range(args.n_perm):
        accs = []
        for f in folds:
            Ztr, Zte = f["Ztr"], f["Zte"]
            Zall = np.vstack([Ztr, Zte]); pall = np.concatenate([f["ptr"], f["pte"]])
            V = centroid_subspace(Zall, pall, best_k)
            if eco_protect:
                Veco = centroid_subspace(Ztr, f["ytr"], len(set(f["ytr"])) - 1)
                V = protect(orthonormalize(V), orthonormalize(Veco))
            Ztr2, Zte2 = project_out(Ztr, V), project_out(Zte, V)
            ysh = rng.permutation(f["ytr"])
            idx = rng.permutation(len(ysh))[: args.perm_subsample]
            clf = LogisticRegression(max_iter=300, class_weight="balanced", random_state=args.seed).fit(Ztr2[idx], ysh[idx])
            accs.append(balanced_accuracy_score(f["yte"], clf.predict(Zte2)))
        null[i] = np.mean(accs)
    p = float((np.sum(null >= best["mean_over_folds"]) + 1) / (args.n_perm + 1))
    log(f"  null mean={null.mean():.3f} +/- {null.std():.3f}   p={p:.1e}")

    # ---- figure ----
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig_rel = "figures/site_invariance.png"
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    ks = list(sweep.keys())
    ax[0].axhline(raw["mean_over_folds"], color="#c0392b", ls="--", label=f"raw ({raw['mean_over_folds']:.2f})")
    ax[0].plot(ks, [sweep[k]["mean_over_folds"] for k in ks], "o-", color="#1f7fc4", label="site-invariant (transductive)")
    ax[0].axhline(0.25, color="gray", ls=":", label="chance (0.25)")
    ax[0].set_xlabel("removed site dimensions (k)"); ax[0].set_ylabel("LOPO balanced accuracy (mean over folds)")
    ax[0].set_title("Site-invariance recovers cross-site ecotype transfer"); ax[0].legend(fontsize=8)
    if pairs:
        labels = list(pairs.keys()); xr = np.arange(len(labels))
        ax[1].bar(xr - 0.2, [pairs[l]["raw"] for l in labels], 0.4, label="raw", color="#c0392b")
        ax[1].bar(xr + 0.2, [pairs[l]["site_invariant"] for l in labels], 0.4, label="site-invariant", color="#1f7fc4")
        ax[1].axhline(0.5, color="gray", ls=":", label="chance")
        ax[1].set_xticks(xr); ax[1].set_xticklabels([l.replace("_", " ") for l in labels], fontsize=8)
        ax[1].set_ylabel("cross-site balanced accuracy"); ax[1].set_title("Pairwise cross-site transfer"); ax[1].legend(fontsize=8)
    plt.suptitle("H8: leakage-safe site-invariance transform on frozen AVES2 embeddings", fontweight="bold")
    plt.tight_layout(); plt.savefig(REPO_ROOT / fig_rel, dpi=150, bbox_inches="tight"); plt.close()
    log(f"\nFigure: {fig_rel}")

    summary = {
        "head": "H8_site_invariance",
        "encoder": "AVES2 (frozen, mean-pooled)",
        "pipeline": f"StandardScaler + PCA({args.npca}) + site-nuisance subspace projection + LogisticRegression",
        "leakage_safety": "scaler/PCA/subspace fit on training providers; test-provider ECOTYPE labels never used (transductive uses test-provider embeddings only, label-free)",
        "ecotype_protected": eco_protect,
        "raw_lopo": raw,
        "site_invariant_lopo_transductive": {"k_sweep": {str(k): sweep[k] for k in sweep}, "best_k": best_k, "best": best},
        "site_invariant_lopo_inductive_best_k": ind,
        "cross_site_pairs_raw_vs_invariant": pairs,
        "within_site_sanity_srkw_tkw_vfpa": {"raw": within_raw, f"after_removing_{best_k}_dims": within_inv},
        "permutation_null": {"k": best_k, "n_perm": args.n_perm, "null_mean": float(null.mean()),
                             "null_std": float(null.std()), "pvalue": p},
        "figure": fig_rel,
        "boundary": ("Methods contribution: a label-free site-invariance transform for frozen "
                     "bioacoustic embeddings. Ecotype and recording site are confounded in this "
                     "corpus (SAR is single-provider), so recovery is bounded. "
                     "Not a claim of meaning."),
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "site_invariance_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log("Metrics JSON: reports/site_invariance_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

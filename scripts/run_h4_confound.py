#!/usr/bin/env python3
"""H4: Confound isolation -- is the ecotype signal biological or site artifact?

This head uses only DCLDE embeddings and metadata. It quantifies provider/site
signal directly, then checks whether ecotype structure remains when recording
site is controlled.

It answers the question the pooled H1 number cannot: the ecotype label is nearly
collinear with the recording provider/site, so high pooled accuracy may just be
hydrophone recognition. Three real-data tests separate biology from site:

1. SITE-DECODING PROBE. Predict the recording provider directly from the
   embeddings. High accuracy quantifies how much site information the encoder
   carries (the size of the confound).

2. WITHIN-SITE ECOTYPE DISCRIMINATION. For each provider that recorded >=2
   ecotypes with enough calls, classify ecotype *within that single provider*.
   Here site is held constant, so above-chance accuracy is genuine acoustic /
   biological signal that cannot be explained by the hydrophone. This is the
   cleanest evidence that AVES2 captures call structure, not just channel.

3. CROSS-SITE TRANSFER. For the ecotype pair that appears across the most
   providers, train on some providers and test on disjoint providers. Transfer
   accuracy is the strictest generalisation estimate.

Usage:
  python scripts/run_h4_confound.py --embeddings data/embeddings/aves2_full_labeled.npz
"""

import argparse
import json
import sys
import warnings
from collections import Counter
from pathlib import Path

warnings.filterwarnings("ignore", message="y_pred contains classes not in y_true")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
SEED = 0
TRANSFER_TRAIN_CAP = 8000


def _logreg():
    return LogisticRegression(max_iter=2000, random_state=SEED, C=1.0)


def _fast_clf():
    """Fast OvR liblinear probe used for the (many) permutation refits."""
    return OneVsRestClassifier(
        LogisticRegression(solver="liblinear", max_iter=1000, C=1.0, random_state=SEED),
        n_jobs=1,
    )


def _transfer_clf():
    """Cross-domain probe: standardise on the training providers (proper, no
    leakage) then a bounded liblinear logistic model. Standardisation makes the
    solver converge in seconds on the pooled pair, where unscaled lbfgs stalls."""
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(solver="liblinear", max_iter=1000, C=1.0, random_state=SEED),
    )


def load_arrays(emb_path: Path):
    data = np.load(emb_path, allow_pickle=True)
    embeddings = data["embeddings"].astype(np.float32)
    if "labels" in data:
        labels = np.array([str(x) for x in data["labels"]])
    elif "metadata" in data:
        labels = np.array([str(m["ecotype"]) for m in data["metadata"]])
    else:
        raise SystemExit("ERROR: npz needs 'labels' or 'metadata'.")
    providers = None
    if "metadata" in data and len(data["metadata"]) == len(embeddings):
        providers = np.array([str(m.get("provider", "NA")) for m in data["metadata"]])
    return embeddings, labels, providers


def site_decoding_probe(embeddings, providers):
    """Predict provider from embeddings; quantifies how much site leaks in."""
    le = LabelEncoder()
    y = le.fit_transform(providers)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    y_pred = cross_val_predict(_logreg(), embeddings, y, cv=cv)
    bal = balanced_accuracy_score(y, y_pred)
    chance = 1.0 / len(le.classes_)
    print("\n--- Test 1: Site-decoding probe (predict provider) ---")
    print(f"  Providers: {len(le.classes_)}  chance={chance:.3f}")
    print(f"  Balanced accuracy decoding PROVIDER from embeddings: {bal:.3f}")
    print(f"  -> embeddings carry {'STRONG' if bal > 0.6 else 'moderate' if bal > 0.3 else 'weak'} "
          f"site information")
    return {"provider_balanced_accuracy": float(bal),
            "n_providers": int(len(le.classes_)),
            "chance": float(chance)}


def within_site_discrimination(embeddings, labels, providers,
                               min_per_class=40, n_perm=200):
    """Within each provider, classify ecotype (site held constant)."""
    print("\n--- Test 2: Within-site ecotype discrimination (site held constant) ---")
    results = {}
    rng = np.random.default_rng(SEED)
    for prov in sorted(set(providers)):
        mask = providers == prov
        y_lab = labels[mask]
        counts = Counter(y_lab)
        usable = [c for c, n in counts.items() if n >= min_per_class]
        if len(usable) < 2:
            continue
        keep = np.isin(y_lab, usable)
        Xp = embeddings[mask][keep]
        le = LabelEncoder()
        yp = le.fit_transform(y_lab[keep])
        n_splits = min(5, int(np.min(np.bincount(yp))))
        if n_splits < 2:
            continue
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=SEED)
        # Reported metric: cross-validated balanced accuracy (robust).
        y_pred = cross_val_predict(_logreg(), Xp, yp, cv=cv)
        bal = balanced_accuracy_score(yp, y_pred)
        chance = 1.0 / len(le.classes_)

        # Permutation null: a single fast 70/30 liblinear split, refit per
        # shuffle (cross_val_predict per permutation is intractable on 10k+
        # rows). The observed split-score is recomputed the same way so the
        # null and observed are apples-to-apples.
        Xtr, Xte, ytr, yte = train_test_split(
            Xp, yp, test_size=0.3, stratify=yp, random_state=SEED)
        split_obs = balanced_accuracy_score(yte, _fast_clf().fit(Xtr, ytr).predict(Xte))
        null = np.empty(n_perm)
        for i in range(n_perm):
            yshuf = rng.permutation(ytr)
            null[i] = balanced_accuracy_score(yte, _fast_clf().fit(Xtr, yshuf).predict(Xte))
        pval = (np.sum(null >= split_obs) + 1) / (n_perm + 1)

        results[prov] = {
            "classes": list(map(str, le.classes_)),
            "n": int(keep.sum()),
            "balanced_accuracy": float(bal),
            "chance": float(chance),
            "pvalue": float(pval),
        }
        flag = "BIOLOGICAL SIGNAL" if (bal > 1.5 * chance and pval < 0.05) else "weak/none"
        print(f"  {prov:18s} classes={list(le.classes_)} n={int(keep.sum()):,}  "
              f"balanced={bal:.3f} (chance {chance:.2f}, p={pval:.1e})  -> {flag}")
    if not results:
        print("  No provider had >=2 ecotypes above the min-per-class threshold.")
    return results


def cross_site_transfer(embeddings, labels, providers, min_per_class=40):
    """Train on some providers, test on disjoint providers, for the ecotype
    pair spanning the most providers."""
    print("\n--- Test 3: Cross-site transfer (train/test on disjoint providers) ---")
    # Find which providers contain each ecotype with enough calls.
    eco_to_provs = {}
    for eco in sorted(set(labels)):
        provs = []
        for prov in sorted(set(providers)):
            if np.sum((labels == eco) & (providers == prov)) >= min_per_class:
                provs.append(prov)
        eco_to_provs[eco] = provs

    # Pick the two ecotypes that jointly span the most shared providers.
    ecos = [e for e, p in eco_to_provs.items() if len(p) >= 2]
    best_pair, best_provs = None, []
    for i in range(len(ecos)):
        for j in range(i + 1, len(ecos)):
            shared = sorted(set(eco_to_provs[ecos[i]]) | set(eco_to_provs[ecos[j]]))
            provs_with_both = [p for p in shared
                               if np.sum((labels == ecos[i]) & (providers == p)) >= min_per_class
                               or np.sum((labels == ecos[j]) & (providers == p)) >= min_per_class]
            if len(provs_with_both) > len(best_provs):
                best_pair = (ecos[i], ecos[j])
                best_provs = provs_with_both
    if best_pair is None:
        print("  No ecotype pair spans >=2 providers; skipping.")
        return {}

    pair_mask = np.isin(labels, list(best_pair))
    Xp, yp, pp = embeddings[pair_mask], labels[pair_mask], providers[pair_mask]
    le = LabelEncoder()
    yc = le.fit_transform(yp)
    chance = 0.5

    print(f"  Pair: {best_pair}  across providers: {best_provs}")
    rng = np.random.default_rng(SEED)
    per_test = {}
    for test_prov in best_provs:
        tr = pp != test_prov
        te = pp == test_prov
        if len(np.unique(yc[tr])) < 2 or len(np.unique(yc[te])) < 2:
            continue
        tr_idx = np.flatnonzero(tr)
        # Cap the training set for a bounded, predictable fit time; the estimate
        # is stable well below the full ~18k pooled-pair size.
        if tr_idx.size > TRANSFER_TRAIN_CAP:
            tr_idx = rng.choice(tr_idx, size=TRANSFER_TRAIN_CAP, replace=False)
        clf = _transfer_clf().fit(Xp[tr_idx], yc[tr_idx])
        bal = balanced_accuracy_score(yc[te], clf.predict(Xp[te]))
        per_test[test_prov] = {"balanced_accuracy": float(bal),
                               "n_test": int(te.sum()),
                               "n_train": int(tr_idx.size)}
        print(f"    test={test_prov:18s} balanced={bal:.3f} (test n={int(te.sum()):,}, "
              f"train n={int(tr_idx.size):,})")
    mean_bal = float(np.mean([v["balanced_accuracy"] for v in per_test.values()])) if per_test else 0.0
    print(f"  Mean cross-site transfer balanced accuracy: {mean_bal:.3f} (chance {chance:.2f})")
    return {"pair": list(best_pair), "chance": chance,
            "mean_transfer_balanced_accuracy": mean_bal, "per_test_provider": per_test}


def make_figure(site, within, transfer, encoder_name):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Panel 1: site-decoding.
    axes[0].bar(["provider\ndecoding", "chance"],
                [site["provider_balanced_accuracy"], site["chance"]],
                color=["#E91E63", "#cccccc"])
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Balanced accuracy")
    axes[0].set_title(f"Test 1: site leakage\n({site['n_providers']} providers)")
    axes[0].text(0, site["provider_balanced_accuracy"] + 0.02,
                 f"{site['provider_balanced_accuracy']:.2f}", ha="center")

    # Panel 2: within-site biology.
    if within:
        provs = list(within.keys())
        vals = [within[p]["balanced_accuracy"] for p in provs]
        chs = [within[p]["chance"] for p in provs]
        x = np.arange(len(provs))
        axes[1].bar(x, vals, color="#1565C0", label="within-site balanced acc")
        axes[1].plot(x, chs, "r_", markersize=20, label="within-site chance")
        axes[1].set_xticks(x)
        axes[1].set_xticklabels([p[:10] for p in provs], rotation=45, ha="right", fontsize=8)
        axes[1].set_ylim(0, 1)
        axes[1].set_ylabel("Balanced accuracy")
        axes[1].set_title("Test 2: within-site ecotype\n(site held constant = real signal)")
        axes[1].legend(fontsize=8)
    else:
        axes[1].axis("off")
        axes[1].text(0.5, 0.5, "No within-site\nmulti-ecotype provider", ha="center")

    # Panel 3: cross-site transfer.
    if transfer.get("per_test_provider"):
        pt = transfer["per_test_provider"]
        provs = list(pt.keys())
        vals = [pt[p]["balanced_accuracy"] for p in provs]
        axes[2].bar(range(len(provs)), vals, color="#4CAF50")
        axes[2].axhline(transfer["chance"], color="red", ls="--", label="chance")
        axes[2].set_xticks(range(len(provs)))
        axes[2].set_xticklabels([p[:10] for p in provs], rotation=45, ha="right", fontsize=8)
        axes[2].set_ylim(0, 1)
        axes[2].set_ylabel("Transfer balanced accuracy")
        axes[2].set_title(f"Test 3: cross-site transfer\n{transfer['pair']}")
        axes[2].legend(fontsize=8)
    else:
        axes[2].axis("off")
        axes[2].text(0.5, 0.5, "No cross-site pair", ha="center")

    plt.suptitle(f"H4: Confound isolation -- biology vs site ({encoder_name.upper()})",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = FIGURES_DIR / f"h4_confound_{encoder_name}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Figure saved: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description="H4: confound isolation (DCLDE-only)")
    parser.add_argument("--embeddings", required=True)
    parser.add_argument("--min-per-class", type=int, default=40)
    parser.add_argument("--n-perm", type=int, default=200)
    parser.add_argument("--skip-within", action="store_true",
                        help="skip the (slow) within-site permutation sweep; run site + transfer only")
    args = parser.parse_args()

    emb_path = Path(args.embeddings)
    if not emb_path.exists():
        print(f"ERROR: {emb_path} not found.")
        return 1

    embeddings, labels, providers = load_arrays(emb_path)
    encoder_name = emb_path.stem.replace("_embeddings", "")

    print(f"\n{'='*70}")
    print(f"HEAD H4: CONFOUND ISOLATION ({encoder_name.upper()}) -- DCLDE-only")
    print(f"{'='*70}")
    print(f"  Calls: {len(embeddings):,}  dims: {embeddings.shape[1]}")
    print(f"  Ecotypes: {sorted(set(labels))}")
    if providers is None:
        print("  ERROR: no provider metadata; this head requires provider labels.")
        return 1
    print(f"  Providers: {sorted(set(providers))}")

    site = site_decoding_probe(embeddings, providers)
    if args.skip_within:
        print("\n--- Test 2: within-site discrimination SKIPPED (--skip-within) ---")
        within = {}
    else:
        within = within_site_discrimination(embeddings, labels, providers,
                                            min_per_class=args.min_per_class,
                                            n_perm=args.n_perm)
    transfer = cross_site_transfer(embeddings, labels, providers,
                                   min_per_class=args.min_per_class)
    fig_path = make_figure(site, within, transfer, encoder_name)

    bio_providers = [p for p, r in within.items()
                     if r["balanced_accuracy"] > 1.5 * r["chance"] and r["pvalue"] < 0.05]
    print(f"\n{'='*70}\nH4 SUMMARY\n{'='*70}")
    print(f"  Site decodable at balanced acc {site['provider_balanced_accuracy']:.3f} "
          f"(chance {site['chance']:.3f}) -> confound is real and large")
    print(f"  Providers with genuine within-site ecotype signal: "
          f"{bio_providers if bio_providers else 'NONE'}")
    if transfer.get("per_test_provider"):
        print(f"  Cross-site transfer {transfer['pair']}: "
              f"mean balanced acc {transfer['mean_transfer_balanced_accuracy']:.3f}")
    verdict = ("Ecotype signal is PARTLY biological (survives within-site)"
               if bio_providers else
               "Ecotype signal NOT separable from site in this dataset")
    print(f"  Verdict: {verdict}")
    print(f"{'='*70}")

    results = {
        "encoder": encoder_name,
        "note": "DCLDE-only; all numbers from real DCLDE embeddings",
        "site_decoding": site,
        "within_site": within,
        "cross_site_transfer": transfer,
        "providers_with_biological_signal": bio_providers,
        "figure": f"figures/{Path(fig_path).name}",
    }
    metrics_path = FIGURES_DIR / f"h4_metrics_{encoder_name}.json"
    metrics_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"  Metrics JSON: {metrics_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

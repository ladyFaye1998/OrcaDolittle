#!/usr/bin/env python3
"""H2: Unsupervised clustering -- does structure align with biology or site?

Discovers clusters in frozen embeddings (PCA/UMAP + HDBSCAN) without labels,
then asks the two questions that matter for this confounded dataset:

  (a) Do clusters align with ECOTYPE (biological structure)?
  (b) Do clusters align with PROVIDER (recording-site structure)?

If (b) >> (a), the "structure" the encoder exposes is mostly which hydrophone
recorded the call, not what the whale said. Reporting both is what makes this
head testable.

Two methodological fixes over the naive version:
  - ARI/NMI are reported over ALL points (noise assigned to its own cluster),
    not only the easy non-noise subset, which otherwise inflates agreement.
  - Visualisation axes are labelled by the reducer actually used.

Usage:
  python scripts/run_h2_clustering.py --embeddings data/embeddings/aves2_full_labeled.npz
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.preprocessing import LabelEncoder

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
SEED = 0
N_PERM = 500


def load_providers(emb_path: Path, n: int):
    data = np.load(emb_path, allow_pickle=True)
    if "metadata" in data and len(data["metadata"]) == n:
        return np.array([str(m.get("provider", "NA")) for m in data["metadata"]])
    return None


def all_point_labels(cluster_labels: np.ndarray) -> np.ndarray:
    """Map noise (-1) to its own dedicated cluster id so every point counts."""
    out = cluster_labels.copy()
    if (out == -1).any():
        out[out == -1] = out.max() + 1
    return out


def run_clustering(embeddings, labels, providers, encoder_name, use_umap=False,
                   min_cluster_size=25, min_samples=5):
    import hdbscan

    le = LabelEncoder()
    y_eco = le.fit_transform(labels)
    class_names = le.classes_
    y_prov = LabelEncoder().fit_transform(providers) if providers is not None else None

    print(f"\n{'='*64}")
    print(f"HEAD H2: UNSUPERVISED CLUSTERING ({encoder_name.upper()})")
    print(f"{'='*64}")
    print(f"  Samples: {len(embeddings):,}  reduction: {'UMAP' if use_umap else 'PCA'}")
    print(f"  HDBSCAN min_cluster_size={min_cluster_size} min_samples={min_samples}")

    reducer_name = "UMAP" if use_umap else "PC"
    if use_umap:
        configs = [{"n_neighbors": nn, "min_dist": 0.0, "n_components": 5} for nn in (15, 30, 50)]
    else:
        configs = [{"n_components": nc} for nc in (5, 10, 20)]

    best = None
    for cfg in configs:
        if use_umap:
            import umap
            reduced = umap.UMAP(n_neighbors=cfg["n_neighbors"], min_dist=0.0,
                                n_components=cfg["n_components"], random_state=SEED,
                                metric="cosine").fit_transform(embeddings)
            tag = f"UMAP(nn={cfg['n_neighbors']})"
        else:
            reduced = PCA(n_components=cfg["n_components"], random_state=SEED).fit_transform(embeddings)
            tag = f"PCA(nc={cfg['n_components']})"

        cl = hdbscan.HDBSCAN(min_cluster_size=int(min_cluster_size),
                             min_samples=int(min_samples)).fit_predict(reduced)
        n_clusters = len(set(cl)) - (1 if -1 in cl else 0)
        n_noise = int((cl == -1).sum())

        cl_all = all_point_labels(cl)
        ari_eco = adjusted_rand_score(y_eco, cl_all)
        nmi_eco = normalized_mutual_info_score(y_eco, cl_all)
        ari_prov = adjusted_rand_score(y_prov, cl_all) if y_prov is not None else None
        nmi_prov = normalized_mutual_info_score(y_prov, cl_all) if y_prov is not None else None

        print(f"\n--- {tag} + HDBSCAN ---")
        print(f"  clusters={n_clusters}  noise={n_noise} ({n_noise/len(labels):.1%})")
        print(f"  [all points] ARI vs ECOTYPE  = {ari_eco:.3f}   NMI = {nmi_eco:.3f}")
        if ari_prov is not None:
            print(f"  [all points] ARI vs PROVIDER = {ari_prov:.3f}   NMI = {nmi_prov:.3f}  (confound)")

        if best is None or ari_eco > best["ari_eco"]:
            best = {"tag": tag, "cfg": cfg, "n_clusters": n_clusters, "n_noise": n_noise,
                    "ari_eco": ari_eco, "nmi_eco": nmi_eco,
                    "ari_prov": ari_prov, "nmi_prov": nmi_prov,
                    "cluster_labels": cl, "cluster_labels_all": cl_all, "reduced": reduced}

    # Permutation test on the ecotype ARI (all points).
    print(f"\n--- Permutation Test on ARI vs ecotype (n={N_PERM}) ---")
    rng = np.random.default_rng(SEED)
    cl_all = best["cluster_labels_all"]
    perm = np.array([adjusted_rand_score(rng.permutation(y_eco), cl_all) for _ in range(N_PERM)])
    pvalue = (np.sum(perm >= best["ari_eco"]) + 1) / (N_PERM + 1)
    print(f"  True ARI={best['ari_eco']:.4f}  perm mean={perm.mean():.4f}±{perm.std():.4f}  p={pvalue:.2e}")

    fig_path = make_figure(embeddings, labels, class_names, best, perm, pvalue,
                           reducer_name, use_umap, encoder_name)

    print(f"\n{'='*64}\nH2 SUMMARY\n{'='*64}")
    print(f"  Best: {best['tag']}  clusters={best['n_clusters']}")
    print(f"  ARI vs ecotype  (all points) = {best['ari_eco']:.3f}")
    if best["ari_prov"] is not None:
        print(f"  ARI vs provider (all points) = {best['ari_prov']:.3f}")
        if best["ari_prov"] > best["ari_eco"]:
            print("  -> clusters align MORE with recording site than ecotype (confound dominates)")
        else:
            print("  -> clusters align more with ecotype than site (biological structure present)")
    print(f"  Permutation p-value (ecotype) = {pvalue:.2e}")
    print(f"{'='*64}")

    results = {
        "encoder": encoder_name,
        "best_config": best["tag"],
        "n_clusters": best["n_clusters"],
        "n_noise": best["n_noise"],
        "ari_ecotype_all_points": float(best["ari_eco"]),
        "nmi_ecotype_all_points": float(best["nmi_eco"]),
        "ari_provider_all_points": (float(best["ari_prov"]) if best["ari_prov"] is not None else None),
        "nmi_provider_all_points": (float(best["nmi_prov"]) if best["nmi_prov"] is not None else None),
        "permutation_pvalue_ecotype": float(pvalue),
        "figure": f"figures/{Path(fig_path).name}",
    }
    (FIGURES_DIR / f"h2_metrics_{encoder_name}.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")
    print(f"  Metrics JSON: {FIGURES_DIR / f'h2_metrics_{encoder_name}.json'}")
    return results


def make_figure(embeddings, labels, class_names, best, perm, pvalue,
                reducer_name, use_umap, encoder_name):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    if use_umap:
        import umap
        emb2d = umap.UMAP(n_neighbors=15, min_dist=0.3, n_components=2,
                          random_state=SEED, metric="cosine").fit_transform(embeddings)
        ax_label = "UMAP"
    else:
        emb2d = PCA(n_components=2, random_state=SEED).fit_transform(embeddings)
        ax_label = "PC"

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    colors = plt.cm.Set2(np.linspace(0, 1, len(class_names)))
    for i, eco in enumerate(class_names):
        m = labels == eco
        axes[0].scatter(emb2d[m, 0], emb2d[m, 1], c=[colors[i]], label=eco, s=18, alpha=0.5)
    axes[0].legend(fontsize=9)
    axes[0].set_title("True ecotype")
    axes[0].set_xlabel(f"{ax_label} 1"); axes[0].set_ylabel(f"{ax_label} 2")

    cl = best["cluster_labels"]
    uniq = sorted(set(cl))
    cmap = plt.cm.tab20(np.linspace(0, 1, len(uniq)))
    for i, c in enumerate(uniq):
        m = cl == c
        axes[1].scatter(emb2d[m, 0], emb2d[m, 1], c=[cmap[i]],
                        s=18, alpha=0.6 if c >= 0 else 0.1)
    axes[1].set_title(f"HDBSCAN clusters (k={best['n_clusters']})")
    axes[1].set_xlabel(f"{ax_label} 1")

    axes[2].hist(perm, bins=50, color="lightgray", edgecolor="gray", alpha=0.8, label="Permuted ARI")
    axes[2].axvline(best["ari_eco"], color="red", lw=2, label=f"ARI vs ecotype={best['ari_eco']:.3f}")
    if best["ari_prov"] is not None:
        axes[2].axvline(best["ari_prov"], color="purple", lw=2, ls=":",
                        label=f"ARI vs provider={best['ari_prov']:.3f}")
    axes[2].axvline(0, color="blue", lw=1, ls="--", label="chance")
    axes[2].set_xlabel("Adjusted Rand Index"); axes[2].set_ylabel("Count")
    axes[2].set_title(f"Permutation test (p={pvalue:.2e})")
    axes[2].legend(fontsize=8)

    plt.suptitle(f"H2: Unsupervised structure -- biology vs site ({encoder_name.upper()})",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = FIGURES_DIR / f"h2_clustering_{encoder_name}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Figure saved: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description="H2: unsupervised clustering (confound-aware)")
    parser.add_argument("--embeddings", required=True)
    parser.add_argument("--umap", action="store_true")
    parser.add_argument("--min-cluster-size", type=int, default=25)
    parser.add_argument("--min-samples", type=int, default=5)
    args = parser.parse_args()

    emb_path = Path(args.embeddings)
    if not emb_path.exists():
        print(f"ERROR: {emb_path} not found.")
        return 1

    data = np.load(emb_path, allow_pickle=True)
    embeddings = data["embeddings"]
    labels = np.array([str(x) for x in data["labels"]])
    providers = load_providers(emb_path, len(embeddings))

    encoder_name = emb_path.stem.replace("_embeddings", "")
    run_clustering(embeddings, labels, providers, encoder_name,
                   use_umap=args.umap, min_cluster_size=args.min_cluster_size,
                   min_samples=args.min_samples)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""H2: Unsupervised clustering — UMAP + HDBSCAN on embeddings.

Discovers call-type clusters without labels, then measures how well
they align with the known ecotype/call-type catalogue from literature.

Usage:
  python3 scripts/run_h2_clustering.py --embeddings data/embeddings/aves2_embeddings.npz
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.preprocessing import LabelEncoder

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
SEED = 0
N_PERM = 10_000

UMAP_PARAMS = [
    {"n_neighbors": 15, "min_dist": 0.0, "n_components": 5},
    {"n_neighbors": 30, "min_dist": 0.0, "n_components": 5},
    {"n_neighbors": 50, "min_dist": 0.0, "n_components": 5},
]

HDBSCAN_PARAMS = {"min_cluster_size": 25, "min_samples": 5}


def run_clustering(embeddings: np.ndarray, labels: np.ndarray, encoder_name: str, use_umap: bool = False):
    """Run dimensionality reduction + HDBSCAN and evaluate against known labels."""
    import hdbscan

    le = LabelEncoder()
    y_true = le.fit_transform(labels)
    class_names = le.classes_

    print(f"\n{'='*60}")
    print(f"HEAD H2: UNSUPERVISED CLUSTERING ({encoder_name.upper()} embeddings)")
    print(f"{'='*60}")
    print(f"  Samples: {len(embeddings):,}")
    print(f"  True classes: {list(class_names)}")
    print(f"  Reduction: {'UMAP' if use_umap else 'PCA'}")

    best_ari = -1
    best_result = None

    if use_umap:
        import umap
        configs = [
            {"n_neighbors": nn, "min_dist": 0.0, "n_components": 5}
            for nn in [15, 30, 50]
        ]
    else:
        configs = [
            {"n_components": 5},
            {"n_components": 10},
            {"n_components": 20},
        ]

    for cfg in configs:
        if use_umap:
            nn = cfg["n_neighbors"]
            print(f"\n--- UMAP (n_neighbors={nn}) + HDBSCAN ---")
            reducer = umap.UMAP(
                n_neighbors=nn, min_dist=0.0, n_components=cfg["n_components"],
                random_state=SEED, metric="cosine",
            )
            reduced = reducer.fit_transform(embeddings)
        else:
            nc = cfg["n_components"]
            print(f"\n--- PCA (n_components={nc}) + HDBSCAN ---")
            reducer = PCA(n_components=nc, random_state=SEED)
            reduced = reducer.fit_transform(embeddings)

        # Adaptive HDBSCAN params based on sample size
        min_cluster = max(5, len(embeddings) // 20)
        min_samples = max(2, min_cluster // 5)

        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster, min_samples=min_samples)
        cluster_labels = clusterer.fit_predict(reduced)

        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = (cluster_labels == -1).sum()

        mask = cluster_labels != -1
        if mask.sum() > 10:
            ari = adjusted_rand_score(y_true[mask], cluster_labels[mask])
            nmi = normalized_mutual_info_score(y_true[mask], cluster_labels[mask])
        else:
            ari = 0.0
            nmi = 0.0

        print(f"  Clusters found: {n_clusters}")
        print(f"  Noise points: {n_noise} ({n_noise/len(labels):.1%})")
        print(f"  ARI vs ecotype: {ari:.3f}")
        print(f"  NMI vs ecotype: {nmi:.3f}")

        if ari > best_ari:
            best_ari = ari
            best_result = {
                "config": cfg,
                "n_clusters": n_clusters,
                "n_noise": n_noise,
                "ari": ari,
                "nmi": nmi,
                "cluster_labels": cluster_labels,
                "reduced": reduced,
            }

    # Permutation test on best ARI
    print(f"\n--- Permutation Test (n={N_PERM}) ---")
    print(f"  Best config: {best_result['config']}")
    print(f"  Running permutation test on ARI...")

    mask = best_result["cluster_labels"] != -1
    true_ari = best_result["ari"]
    perm_aris = []

    rng = np.random.default_rng(SEED)
    for _ in range(N_PERM):
        shuffled = rng.permutation(y_true[mask])
        perm_ari = adjusted_rand_score(shuffled, best_result["cluster_labels"][mask])
        perm_aris.append(perm_ari)

    perm_aris = np.array(perm_aris)
    pvalue = (np.sum(perm_aris >= true_ari) + 1) / (N_PERM + 1)

    print(f"  True ARI: {true_ari:.4f}")
    print(f"  Permutation mean: {perm_aris.mean():.4f} ± {perm_aris.std():.4f}")
    print(f"  p-value: {pvalue:.2e}")

    # Generate headline figure
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 2D reduction for visualization
    if use_umap:
        import umap as umap_lib
        reducer_2d = umap_lib.UMAP(n_neighbors=15, min_dist=0.3, n_components=2, random_state=SEED, metric="cosine")
        embedding_2d = reducer_2d.fit_transform(embeddings)
    else:
        pca_2d = PCA(n_components=2, random_state=SEED)
        embedding_2d = pca_2d.fit_transform(embeddings)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Panel 1: colored by true ecotype
    colors_eco = plt.cm.Set2(np.linspace(0, 1, len(class_names)))
    for i, eco in enumerate(class_names):
        mask_eco = labels == eco
        axes[0].scatter(
            embedding_2d[mask_eco, 0], embedding_2d[mask_eco, 1],
            c=[colors_eco[i]], label=eco, s=20, alpha=0.6,
        )
    axes[0].legend(fontsize=9)
    axes[0].set_title("True Ecotype Labels", fontsize=11)
    axes[0].set_xlabel("UMAP 1")
    axes[0].set_ylabel("UMAP 2")

    # Panel 2: colored by discovered clusters
    cluster_ids = best_result["cluster_labels"]
    unique_clusters = sorted(set(cluster_ids))
    colors_cl = plt.cm.tab20(np.linspace(0, 1, len(unique_clusters)))
    for i, cl in enumerate(unique_clusters):
        mask_cl = cluster_ids == cl
        label = f"Cluster {cl}" if cl >= 0 else "Noise"
        alpha = 0.6 if cl >= 0 else 0.1
        axes[1].scatter(
            embedding_2d[mask_cl, 0], embedding_2d[mask_cl, 1],
            c=[colors_cl[i]], label=label if cl < 5 or cl == -1 else "",
            s=20, alpha=alpha,
        )
    axes[1].legend(fontsize=8, ncol=2)
    axes[1].set_title(f"HDBSCAN Clusters (k={best_result['n_clusters']})", fontsize=11)
    axes[1].set_xlabel("UMAP 1")

    # Panel 3: permutation test
    axes[2].hist(perm_aris, bins=50, color="lightgray", edgecolor="gray", alpha=0.8, label="Permuted ARI")
    axes[2].axvline(true_ari, color="red", linewidth=2, label=f"True ARI = {true_ari:.3f}")
    axes[2].axvline(0, color="blue", linewidth=1, linestyle="--", label="Chance (ARI=0)")
    axes[2].set_xlabel("Adjusted Rand Index")
    axes[2].set_ylabel("Count")
    axes[2].set_title(f"Permutation Test (p={pvalue:.2e})", fontsize=11)
    axes[2].legend(fontsize=9)

    plt.suptitle(
        f"H2: Unsupervised Cluster Recovery from {encoder_name.upper()} Embeddings",
        fontsize=13, fontweight="bold",
    )
    plt.tight_layout()

    fig_path = FIGURES_DIR / f"h2_clustering_{encoder_name}.png"
    plt.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Figure saved: {fig_path}")

    # Summary
    print(f"\n{'='*60}")
    print(f"H2 SUMMARY")
    print(f"{'='*60}")
    print(f"  Clusters discovered: {best_result['n_clusters']}")
    print(f"  ARI vs ecotype: {true_ari:.3f}")
    print(f"  NMI vs ecotype: {best_result['nmi']:.3f}")
    print(f"  Permutation p-value: {pvalue:.2e}")
    print(f"  Verdict: {'PASS' if pvalue < 0.001 else 'MARGINAL' if pvalue < 0.05 else 'FAIL'}")
    print(f"{'='*60}")

    return {
        "encoder": encoder_name,
        "n_clusters": best_result["n_clusters"],
        "ari": true_ari,
        "nmi": best_result["nmi"],
        "pvalue": pvalue,
    }


def main():
    parser = argparse.ArgumentParser(description="H2: Unsupervised clustering")
    parser.add_argument("--embeddings", type=str, required=True)
    parser.add_argument("--umap", action="store_true", help="Use UMAP instead of PCA (needs more RAM)")
    args = parser.parse_args()

    emb_path = Path(args.embeddings)
    if not emb_path.exists():
        print(f"ERROR: {emb_path} not found. Run scripts/batch_encode.py first.")
        return 1

    data = np.load(emb_path)
    embeddings = data["embeddings"]
    labels = data["labels"]

    encoder_name = emb_path.stem.replace("_embeddings", "")
    results = run_clustering(embeddings, labels, encoder_name, use_umap=args.umap)

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Synthetic benchmark for provider-aware bioacoustic evaluation.

The benchmark varies acquisition/provider signal strength under three label-overlap
regimes. It compares ordinary random cross-validation with leave-one-provider-out
evaluation, within-provider evaluation, direct provider decoding, and a label-free
provider-subspace projection. The benchmark is deliberately generic: observations
are feature vectors with independent biological and acquisition components, so the
same failure mode applies to acoustic embeddings from any taxon or recorder network.

Outputs
-------
reports/provider_aware_benchmark_summary.json
figures/provider_aware_benchmark.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import LeaveOneGroupOut, StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
SEED = 0


def classifier(seed: int) -> object:
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(
            max_iter=1500,
            class_weight="balanced",
            C=1.0,
            random_state=seed,
        ),
    )


def centered_simplex(n_classes: int, dim: int, rng: np.random.Generator) -> np.ndarray:
    raw = rng.normal(size=(n_classes, dim))
    raw -= raw.mean(axis=0, keepdims=True)
    norms = np.linalg.norm(raw, axis=1, keepdims=True)
    return raw / np.maximum(norms, 1e-12)


def count_matrix(regime: str, n_providers: int, n_classes: int) -> np.ndarray:
    counts = np.zeros((n_providers, n_classes), dtype=int)
    if regime == "balanced":
        counts[:] = 45
    elif regime == "partial":
        counts[:] = 12
        for provider in range(n_providers):
            counts[provider, provider % n_classes] = 105
    elif regime == "structural":
        # Class 3 is observed only at provider 0. Other classes remain available
        # across providers, making the unsupported class explicit rather than
        # turning every held-out fold into a single-class problem.
        counts[0, 0] = 30
        counts[0, 3] = 120
        for provider in range(1, n_providers):
            counts[provider, :3] = 12
            counts[provider, provider % 3] = 105
    else:
        raise ValueError(f"Unknown regime: {regime}")
    return counts


def simulate(
    regime: str,
    provider_strength: float,
    seed: int,
    n_providers: int = 8,
    n_classes: int = 4,
    dim: int = 48,
    biology_strength: float = 1.35,
    noise_scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    biology = centered_simplex(n_classes, dim, rng) * biology_strength

    # Provider shifts share a low-rank acquisition subspace, as recorder/site
    # effects commonly do, while remaining independent of the biological means.
    basis_raw = rng.normal(size=(dim, 5))
    provider_basis, _ = np.linalg.qr(basis_raw)
    provider_coeff = rng.normal(size=(n_providers, 5))
    provider_coeff -= provider_coeff.mean(axis=0, keepdims=True)
    provider_shift = provider_coeff @ provider_basis.T
    provider_shift /= np.maximum(np.linalg.norm(provider_shift, axis=1, keepdims=True), 1e-12)
    provider_shift *= provider_strength

    counts = count_matrix(regime, n_providers, n_classes)
    rows: list[np.ndarray] = []
    labels: list[int] = []
    providers: list[int] = []
    for provider in range(n_providers):
        for label in range(n_classes):
            n = int(counts[provider, label])
            if n == 0:
                continue
            eps = rng.normal(scale=noise_scale, size=(n, dim))
            rows.append(biology[label] + provider_shift[provider] + eps)
            labels.extend([label] * n)
            providers.extend([provider] * n)
    return np.vstack(rows), np.asarray(labels), np.asarray(providers)


def random_cv_score(X: np.ndarray, y: np.ndarray, seed: int) -> float:
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    pred = cross_val_predict(classifier(seed), X, y, cv=cv)
    return float(balanced_accuracy_score(y, pred))


def provider_score(X: np.ndarray, providers: np.ndarray, seed: int) -> float:
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    pred = cross_val_predict(classifier(seed), X, providers, cv=cv)
    return float(balanced_accuracy_score(providers, pred))


def lopo_score(X: np.ndarray, y: np.ndarray, providers: np.ndarray, seed: int) -> float:
    logo = LeaveOneGroupOut()
    pred = np.empty_like(y)
    for train, test in logo.split(X, y, providers):
        model = classifier(seed)
        model.fit(X[train], y[train])
        pred[test] = model.predict(X[test])
    return float(balanced_accuracy_score(y, pred))


def within_provider_score(X: np.ndarray, y: np.ndarray, providers: np.ndarray, seed: int) -> float:
    scores: list[float] = []
    for provider in np.unique(providers):
        mask = providers == provider
        classes, counts = np.unique(y[mask], return_counts=True)
        if len(classes) < 2 or counts.min() < 3:
            continue
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed)
        pred = cross_val_predict(classifier(seed), X[mask], y[mask], cv=cv)
        scores.append(float(balanced_accuracy_score(y[mask], pred)))
    return float(np.mean(scores)) if scores else float("nan")


def provider_subspace(centroids: np.ndarray, k: int) -> np.ndarray:
    centered = centroids - centroids.mean(axis=0, keepdims=True)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    return vt[: min(k, vt.shape[0])].T


def project_out(Z: np.ndarray, basis: np.ndarray) -> np.ndarray:
    if basis.size == 0:
        return Z
    return Z - (Z @ basis) @ basis.T


def invariant_lopo_score(
    X: np.ndarray,
    y: np.ndarray,
    providers: np.ndarray,
    seed: int,
    n_components: int = 24,
    nuisance_dims: int = 4,
) -> float:
    logo = LeaveOneGroupOut()
    pred = np.empty_like(y)
    for train, test in logo.split(X, y, providers):
        scaler = StandardScaler().fit(X[train])
        train_scaled = scaler.transform(X[train])
        test_scaled = scaler.transform(X[test])
        n_pca = min(n_components, train_scaled.shape[1], train_scaled.shape[0] - 1)
        pca = PCA(n_components=n_pca, random_state=seed).fit(train_scaled)
        Z_train = pca.transform(train_scaled)
        Z_test = pca.transform(test_scaled)
        train_providers = np.unique(providers[train])
        centroids = np.vstack(
            [Z_train[providers[train] == p].mean(axis=0) for p in train_providers]
        )
        nuisance = provider_subspace(centroids, nuisance_dims)
        Z_train = project_out(Z_train, nuisance)
        Z_test = project_out(Z_test, nuisance)
        model = LogisticRegression(
            max_iter=1500,
            class_weight="balanced",
            C=1.0,
            random_state=seed,
        )
        model.fit(Z_train, y[train])
        pred[test] = model.predict(Z_test)
    return float(balanced_accuracy_score(y, pred))


def run_one(regime: str, strength: float, seed: int) -> dict[str, float]:
    X, y, providers = simulate(regime, strength, seed)
    return {
        "random_cv_balanced_accuracy": random_cv_score(X, y, seed),
        "leave_one_provider_out_balanced_accuracy": lopo_score(X, y, providers, seed),
        "within_provider_balanced_accuracy": within_provider_score(X, y, providers, seed),
        "provider_decoding_balanced_accuracy": provider_score(X, providers, seed),
        "projected_leave_one_provider_out_balanced_accuracy": invariant_lopo_score(
            X, y, providers, seed
        ),
        "n_observations": float(len(y)),
    }


def summarize(values: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=float)
    return {
        "mean": float(np.nanmean(arr)),
        "sd": float(np.nanstd(arr, ddof=1)),
        "q05": float(np.nanquantile(arr, 0.05)),
        "q95": float(np.nanquantile(arr, 0.95)),
    }


def benchmark(strengths: list[float], repeats: int, seed: int) -> dict:
    regimes = ["balanced", "partial", "structural"]
    raw: list[dict] = []
    for regime_index, regime in enumerate(regimes):
        for strength_index, strength in enumerate(strengths):
            for repeat in range(repeats):
                run_seed = seed + regime_index * 100_000 + strength_index * 1_000 + repeat
                metrics = run_one(regime, strength, run_seed)
                raw.append(
                    {
                        "regime": regime,
                        "provider_strength": strength,
                        "repeat": repeat,
                        "seed": run_seed,
                        **metrics,
                    }
                )

    metric_names = [
        "random_cv_balanced_accuracy",
        "leave_one_provider_out_balanced_accuracy",
        "within_provider_balanced_accuracy",
        "provider_decoding_balanced_accuracy",
        "projected_leave_one_provider_out_balanced_accuracy",
    ]
    summary: dict[str, dict[str, dict]] = {}
    for regime in regimes:
        summary[regime] = {}
        for strength in strengths:
            rows = [
                row
                for row in raw
                if row["regime"] == regime and row["provider_strength"] == strength
            ]
            summary[regime][str(strength)] = {
                metric: summarize([float(row[metric]) for row in rows]) for metric in metric_names
            }

    return {
        "analysis": "provider_aware_evaluation_benchmark",
        "seed": seed,
        "repeats": repeats,
        "provider_strengths": strengths,
        "n_providers": 8,
        "n_biological_classes": 4,
        "feature_dimension": 48,
        "biology_strength": 1.35,
        "regimes": {
            "balanced": "Every biological class occurs equally at every provider.",
            "partial": (
                "Every class occurs at every provider, but each provider is dominated by one class."
            ),
            "structural": (
                "One biological class occurs at only one provider; the other classes "
                "retain cross-provider overlap."
            ),
        },
        "summary": summary,
        "raw_runs": raw,
        "interpretation_boundary": (
            "The synthetic benchmark diagnoses acquisition-label confounding and tests "
            "evaluation behavior. "
            "It does not establish that nuisance projection can recover a biological class absent "
            "from training providers; structural non-overlap is an identifiability limit."
        ),
    }


def interval(summary: dict, regime: str, strengths: list[float], metric: str):
    rows = [summary[regime][str(s)][metric] for s in strengths]
    mean = np.asarray([row["mean"] for row in rows])
    low = np.asarray([row["q05"] for row in rows])
    high = np.asarray([row["q95"] for row in rows])
    return mean, low, high


def make_figure(result: dict, path: Path) -> None:
    strengths = [float(x) for x in result["provider_strengths"]]
    summary = result["summary"]
    regimes = ["balanced", "partial", "structural"]
    titles = {
        "balanced": "Balanced class-provider overlap",
        "partial": "Partial class-provider confounding",
        "structural": "Structural non-overlap",
    }
    styles = {
        "random_cv_balanced_accuracy": ("Random CV", "#1f77b4", "o", "-"),
        "leave_one_provider_out_balanced_accuracy": ("Provider holdout", "#d55e00", "s", "--"),
        "within_provider_balanced_accuracy": ("Within provider", "#009e73", "^", "-."),
        "projected_leave_one_provider_out_balanced_accuracy": (
            "Holdout after projection",
            "#7a3e9d",
            "D",
            ":",
        ),
    }
    fig, axes = plt.subplots(3, 2, figsize=(12.2, 11.4), sharex=True)
    for row, regime in enumerate(regimes):
        ax = axes[row, 0]
        for metric, (label, color, marker, linestyle) in styles.items():
            mean, low, high = interval(summary, regime, strengths, metric)
            ax.plot(
                strengths,
                mean,
                label=label,
                color=color,
                marker=marker,
                linestyle=linestyle,
                linewidth=2,
                markersize=5,
            )
            ax.fill_between(strengths, low, high, color=color, alpha=0.10)
        ax.axhline(0.25, color="0.35", linewidth=1, linestyle=(0, (2, 2)))
        ax.set_ylim(0.18, 1.02)
        ax.set_ylabel("Biological balanced accuracy")
        ax.set_title(titles[regime], loc="left", fontweight="bold")
        ax.grid(alpha=0.22)

        ax2 = axes[row, 1]
        mean, low, high = interval(
            summary, regime, strengths, "provider_decoding_balanced_accuracy"
        )
        ax2.plot(
            strengths,
            mean,
            color="#4c4c4c",
            marker="o",
            linewidth=2,
            label="Provider decoding",
        )
        ax2.fill_between(strengths, low, high, color="#4c4c4c", alpha=0.12)
        ax2.axhline(0.125, color="0.35", linewidth=1, linestyle=(0, (2, 2)))
        ax2.set_ylim(0.08, 1.02)
        ax2.set_ylabel("Provider balanced accuracy")
        ax2.grid(alpha=0.22)

    axes[-1, 0].set_xlabel("Provider-effect strength (standardized units)")
    axes[-1, 1].set_xlabel("Provider-effect strength (standardized units)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, 0.995),
    )
    fig.suptitle(
        "Provider-aware evaluation separates biological signal from acquisition shortcuts",
        y=1.035,
        fontsize=14,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.005,
        "Lines show means; shaded bands show 5th-95th percentiles across benchmark repeats.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.025, 1, 0.965))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--strengths",
        type=float,
        nargs="+",
        default=[0.0, 0.75, 1.5, 2.25, 3.0, 4.0],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "provider_aware_benchmark_summary.json",
    )
    parser.add_argument(
        "--figure",
        type=Path,
        default=ROOT / "figures" / "provider_aware_benchmark.png",
    )
    args = parser.parse_args()

    result = benchmark(list(args.strengths), args.repeats, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    make_figure(result, args.figure)
    print(f"Wrote {args.output}")
    print(f"Wrote {args.figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

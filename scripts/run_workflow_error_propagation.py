"""Quantify error propagation through the provider-aware workflow.

The experiment starts from the partially confounded synthetic benchmark and
introduces three common upstream errors: feature-extraction noise, target-label
error, and provider-metadata error. It reports one-factor sensitivity curves and a
cumulative sequence so that uncertainty added at each workflow stage is visible.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from run_provider_aware_benchmark import lopo_score, provider_score, random_cv_score, simulate

ROOT = Path(__file__).resolve().parents[1]
FEATURE_LEVELS = [0.0, 0.25, 0.5, 1.0]
LABEL_LEVELS = [0.0, 0.05, 0.1, 0.2]
PROVIDER_LEVELS = [0.0, 0.05, 0.1, 0.2]


def corrupt_features(X: np.ndarray, sigma: float, rng: np.random.Generator) -> np.ndarray:
    return X + rng.normal(scale=sigma, size=X.shape)


def corrupt_labels(y: np.ndarray, fraction: float, rng: np.random.Generator) -> np.ndarray:
    out = y.copy()
    n = int(round(len(out) * fraction))
    if n == 0:
        return out
    idx = rng.choice(len(out), size=n, replace=False)
    classes = np.unique(out)
    for row in idx:
        alternatives = classes[classes != out[row]]
        out[row] = rng.choice(alternatives)
    return out


def corrupt_providers(
    providers: np.ndarray, fraction: float, rng: np.random.Generator
) -> np.ndarray:
    out = providers.copy()
    n = int(round(len(out) * fraction))
    if n == 0:
        return out
    idx = rng.choice(len(out), size=n, replace=False)
    groups = np.unique(out)
    for row in idx:
        alternatives = groups[groups != out[row]]
        out[row] = rng.choice(alternatives)
    return out


def evaluate(X: np.ndarray, y: np.ndarray, providers: np.ndarray, seed: int) -> dict[str, float]:
    return {
        "random_cv": random_cv_score(X, y, seed),
        "provider_holdout": lopo_score(X, y, providers, seed),
        "provider_decode": provider_score(X, providers, seed),
    }


def summarize(rows: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for metric in ["random_cv", "provider_holdout", "provider_decode"]:
        values = np.asarray([row[metric] for row in rows])
        result[metric] = {
            "mean": float(values.mean()),
            "sd": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
            "q05": float(np.quantile(values, 0.05)),
            "q95": float(np.quantile(values, 0.95)),
        }
    return result


def run(repeats: int, seed: int) -> dict:
    raw: list[dict] = []
    cumulative: dict[str, list[dict[str, float]]] = {
        "clean": [],
        "feature_noise_0.5": [],
        "plus_target_error_0.1": [],
        "plus_provider_error_0.1": [],
    }
    sweeps = {
        "feature_noise": {str(level): [] for level in FEATURE_LEVELS},
        "target_label_error": {str(level): [] for level in LABEL_LEVELS},
        "provider_metadata_error": {str(level): [] for level in PROVIDER_LEVELS},
    }

    for repeat in range(repeats):
        run_seed = seed + repeat * 1000
        X, y, providers = simulate("partial", 3.0, run_seed)

        stage_rng = np.random.default_rng(run_seed + 101)
        clean = evaluate(X, y, providers, run_seed)
        X_noisy = corrupt_features(X, 0.5, stage_rng)
        feature = evaluate(X_noisy, y, providers, run_seed)
        y_noisy = corrupt_labels(y, 0.1, stage_rng)
        target = evaluate(X_noisy, y_noisy, providers, run_seed)
        p_noisy = corrupt_providers(providers, 0.1, stage_rng)
        provider = evaluate(X_noisy, y_noisy, p_noisy, run_seed)
        cumulative["clean"].append(clean)
        cumulative["feature_noise_0.5"].append(feature)
        cumulative["plus_target_error_0.1"].append(target)
        cumulative["plus_provider_error_0.1"].append(provider)

        for index, level in enumerate(FEATURE_LEVELS):
            rng = np.random.default_rng(run_seed + 200 + index)
            metrics = evaluate(corrupt_features(X, level, rng), y, providers, run_seed)
            sweeps["feature_noise"][str(level)].append(metrics)
            raw.append({"repeat": repeat, "error": "feature_noise", "level": level, **metrics})

        for index, level in enumerate(LABEL_LEVELS):
            rng = np.random.default_rng(run_seed + 300 + index)
            metrics = evaluate(X, corrupt_labels(y, level, rng), providers, run_seed)
            sweeps["target_label_error"][str(level)].append(metrics)
            raw.append({"repeat": repeat, "error": "target_label_error", "level": level, **metrics})

        for index, level in enumerate(PROVIDER_LEVELS):
            rng = np.random.default_rng(run_seed + 400 + index)
            metrics = evaluate(X, y, corrupt_providers(providers, level, rng), run_seed)
            sweeps["provider_metadata_error"][str(level)].append(metrics)
            raw.append(
                {"repeat": repeat, "error": "provider_metadata_error", "level": level, **metrics}
            )

    return {
        "analysis": "provider_aware_workflow_error_propagation",
        "seed": seed,
        "repeats": repeats,
        "base_regime": "partial class-provider confounding",
        "base_provider_strength": 3.0,
        "cumulative_stages": {stage: summarize(rows) for stage, rows in cumulative.items()},
        "one_factor_sweeps": {
            name: {level: summarize(rows) for level, rows in levels.items()}
            for name, levels in sweeps.items()
        },
        "raw_runs": raw,
        "interpretation": (
            "Feature and target-label error reduce both biological estimates. Provider-metadata "
            "error contaminates the grouping variable itself and can make provider holdout less "
            "strict by mixing true providers across folds; provider identifiers therefore require "
            "the same provenance checks as biological labels."
        ),
    }


def interval(result: dict, sweep: str, metric: str):
    levels = [float(x) for x in result["one_factor_sweeps"][sweep]]
    rows = [result["one_factor_sweeps"][sweep][str(x)][metric] for x in levels]
    return (
        np.asarray(levels),
        np.asarray([row["mean"] for row in rows]),
        np.asarray([row["q05"] for row in rows]),
        np.asarray([row["q95"] for row in rows]),
    )


def make_figure(result: dict, path: Path) -> None:
    colors = {"random_cv": "#2468a2", "provider_holdout": "#d55e00", "provider_decode": "#b23a78"}
    labels = {
        "random_cv": "Random CV",
        "provider_holdout": "Provider holdout",
        "provider_decode": "Provider decode",
    }
    fig, axes = plt.subplots(1, 4, figsize=(13.2, 3.9))

    stages = list(result["cumulative_stages"])
    stage_labels = ["Clean", "+ feature\nnoise", "+ target\nlabels", "+ provider\nIDs"]
    x = np.arange(len(stages))
    width = 0.25
    for offset, metric in enumerate(["random_cv", "provider_holdout", "provider_decode"]):
        values = [result["cumulative_stages"][stage][metric]["mean"] for stage in stages]
        axes[0].bar(
            x + (offset - 1) * width, values, width, color=colors[metric], label=labels[metric]
        )
    axes[0].set_xticks(x, stage_labels, rotation=0, ha="center", fontsize=7)
    axes[0].set_ylim(0.2, 1.0)
    axes[0].set_ylabel("Balanced accuracy")
    axes[0].set_title("Cumulative errors", fontsize=10)
    axes[0].legend(frameon=False, fontsize=7)

    sweep_specs = [
        ("feature_noise", "Feature noise SD"),
        ("target_label_error", "Target-label error fraction"),
        ("provider_metadata_error", "Provider-ID error fraction"),
    ]
    for ax, (sweep, xlabel) in zip(axes[1:], sweep_specs):
        for metric in ["random_cv", "provider_holdout", "provider_decode"]:
            levels, mean, low, high = interval(result, sweep, metric)
            ax.plot(
                levels, mean, marker="o", linewidth=2, color=colors[metric], label=labels[metric]
            )
            ax.fill_between(levels, low, high, color=colors[metric], alpha=0.10)
        ax.set_ylim(0.2, 1.0)
        ax.set_xlabel(xlabel)
        ax.grid(alpha=0.2)
    axes[1].set_ylabel("Balanced accuracy")
    fig.suptitle("Error propagation through provider-aware bioacoustic evaluation", fontsize=12)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94), pad=1.2)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=400, bbox_inches="tight", pad_inches=0.16, facecolor="white")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "workflow_error_propagation_summary.json",
    )
    parser.add_argument(
        "--figure",
        type=Path,
        default=ROOT / "figures" / "workflow_error_propagation.png",
    )
    args = parser.parse_args()
    result = run(args.repeats, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    make_figure(result, args.figure)
    print(f"Wrote {args.output}")
    print(f"Wrote {args.figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

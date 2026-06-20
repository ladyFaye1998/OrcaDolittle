#!/usr/bin/env python3
"""Render the H4 confound-isolation figure from its metrics JSON.

Plotting is decoupled from computation so the figure is always consistent with
`figures/h4_metrics_*.json` and can be regenerated without re-running the slow
within-site permutation sweep. Three panels: (1) site-decoding magnitude,
(2) within-site ecotype discrimination with site held constant, and
(3) cross-site transfer.

Usage:
  python scripts/plot_h4_summary.py --metrics figures/h4_metrics_aves2_full_labeled.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", default="figures/h4_metrics_aves2_full_labeled.json")
    args = parser.parse_args()

    metrics_path = (REPO_ROOT / args.metrics) if not Path(args.metrics).is_absolute() else Path(args.metrics)
    data = json.loads(metrics_path.read_text(encoding="utf-8"))
    encoder = data.get("encoder", "aves2_full_labeled")

    site = data["site_decoding"]
    within = data.get("within_site", {})
    transfer = data.get("cross_site_transfer", {})

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    axes[0].bar(["provider\ndecoding", "chance"],
                [site["provider_balanced_accuracy"], site["chance"]],
                color=["#E91E63", "#cccccc"])
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Balanced accuracy")
    axes[0].set_title(f"Test 1: site leakage\n({site['n_providers']} providers)")
    axes[0].text(0, site["provider_balanced_accuracy"] + 0.02,
                 f"{site['provider_balanced_accuracy']:.2f}", ha="center")

    if within:
        provs = list(within.keys())
        vals = [within[p]["balanced_accuracy"] for p in provs]
        chs = [within[p]["chance"] for p in provs]
        x = np.arange(len(provs))
        axes[1].bar(x, vals, color="#1565C0", label="within-site balanced acc")
        axes[1].plot(x, chs, "r_", markersize=20, label="within-site chance")
        axes[1].set_xticks(x)
        axes[1].set_xticklabels([p[:12] for p in provs], rotation=45, ha="right", fontsize=8)
        axes[1].set_ylim(0, 1)
        axes[1].set_ylabel("Balanced accuracy")
        axes[1].set_title("Test 2: within-site ecotype\n(site held constant = real signal)")
        axes[1].legend(fontsize=8)
    else:
        axes[1].axis("off")
        axes[1].text(0.5, 0.5, "within-site not in metrics", ha="center")

    pt = transfer.get("per_test_provider", {})
    if pt:
        provs = list(pt.keys())
        vals = [pt[p]["balanced_accuracy"] for p in provs]
        axes[2].bar(range(len(provs)), vals, color="#4CAF50")
        axes[2].axhline(transfer.get("chance", 0.5), color="red", ls="--", label="chance")
        axes[2].set_xticks(range(len(provs)))
        axes[2].set_xticklabels([p[:12] for p in provs], rotation=45, ha="right", fontsize=8)
        axes[2].set_ylim(0, 1)
        axes[2].set_ylabel("Transfer balanced accuracy")
        axes[2].set_title(f"Test 3: cross-site transfer\n{transfer.get('pair')}")
        axes[2].legend(fontsize=8)
    else:
        axes[2].axis("off")
        axes[2].text(0.5, 0.5, "no cross-site pair", ha="center")

    plt.suptitle(f"H4: Confound isolation -- biology vs site ({encoder.upper()})",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    out_path = REPO_ROOT / "figures" / f"h4_confound_{encoder}.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Figure saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

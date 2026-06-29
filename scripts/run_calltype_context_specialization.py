#!/usr/bin/env python3
"""C2 (catalogue level): are the validated catalogue call types differentially
associated with foraging vs socializing?

The DTAG head (H5) shows context-specific *production* across movement-defined
contexts (foraging/travelling/resting). This script adds the **functionally
distinct** foraging-vs-socializing contrast at the level of the *named* catalogue
call types we recover in Rung 1, using the published ethological associations in
`data/join_tables/call_type_to_context.csv` (Ford 1989; Foote 2008; Riesch; Yurk)
[@ford1989; @foote2008; @riesch2008; @yurk2002].

Important framing (non-circular): the context labels here come from the published
field ethograms, NOT from our embeddings. This is therefore a literature-grounded
contextual-specialization map of the recovered units, complementing - not
duplicating - the embedding decode in H5. It tests whether resident killer
whales use *distinct named call types* across two functionally distinct contexts
(foraging vs social), which is the production-side reading of the
"more than one behavioural context" criterion. It is NOT a claim of meaning.

Output: a per-call-type foraging/socializing classification, a specialization
index, and a Fisher exact test that the foraging-associated and socializing-
associated type sets are non-randomly distinct.

Usage:
  python scripts/run_calltype_context_specialization.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import fisher_exact

REPO_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = REPO_ROOT / "figures"
REPORTS_DIR = REPO_ROOT / "reports"
DEFAULT_TABLE = "data/join_tables/call_type_to_context.csv"

FORAGING_KEYS = {"foraging"}
SOCIAL_KEYS = {
    "socializing", "social_travelling", "pod_meeting", "multi_pod",
    "large_aggregation", "multi_pod_affiliation", "inter_clan_association",
    "single_pod_identity", "clan_identity", "excitement", "beach_rubbing",
}


def bucket(context: str, context_type: str) -> str | None:
    c = str(context).strip().lower()
    ct = str(context_type).strip().lower()
    if c in FORAGING_KEYS:
        return "foraging"
    if c in SOCIAL_KEYS or ct == "social":
        return "socializing"
    return None  # travelling / resting / other -> not part of this contrast


def classify(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (population, call_type) with foraging / socializing flags."""
    rows = []
    for (pop, ct), grp in df.groupby(["population", "call_type"], sort=False):
        buckets = set()
        for _, r in grp.iterrows():
            for ctx in (r["primary_context"], r["secondary_context"]):
                b = bucket(ctx, r["context_type"])
                if b:
                    buckets.add(b)
        if not buckets:
            continue
        if buckets == {"foraging"}:
            label = "foraging-specialist"
        elif buckets == {"socializing"}:
            label = "socializing-specialist"
        else:
            label = "both"
        rows.append({"population": pop, "call_type": ct,
                     "foraging": "foraging" in buckets,
                     "socializing": "socializing" in buckets,
                     "label": label})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--table", default=DEFAULT_TABLE)
    ap.add_argument("--populations", nargs="*", default=["NRKW", "SRKW"],
                    help="catalogue populations recovered in Rung 1")
    args = ap.parse_args()

    path = (REPO_ROOT / args.table) if not Path(args.table).is_absolute() else Path(args.table)
    df = pd.read_csv(path).fillna("")
    df = df[df["population"].isin(args.populations)]

    cls = classify(df)
    n_for = int(cls["foraging"].sum())
    n_soc = int(cls["socializing"].sum())
    n_both = int((cls["label"] == "both").sum())
    n_for_spec = int((cls["label"] == "foraging-specialist").sum())
    n_soc_spec = int((cls["label"] == "socializing-specialist").sum())
    n_types = int(len(cls))
    specialization_index = (n_for_spec + n_soc_spec) / n_types if n_types else 0.0

    # Fisher exact: are foraging-association and socializing-association non-randomly
    # distinct across the catalogue types? 2x2 of (foraging yes/no) x (socializing yes/no).
    table = [
        [int(((cls["foraging"]) & (cls["socializing"])).sum()),
         int(((cls["foraging"]) & (~cls["socializing"])).sum())],
        [int(((~cls["foraging"]) & (cls["socializing"])).sum()),
         int(((~cls["foraging"]) & (~cls["socializing"])).sum())],
    ]
    odds, p = fisher_exact(table, alternative="two-sided")

    print("\n" + "=" * 66)
    print("C2 (CATALOGUE): FORAGING vs SOCIALIZING SPECIALIZATION")
    print("=" * 66)
    print(f"  populations: {', '.join(args.populations)}  (validated Rung-1 catalogue)")
    print(f"  call types with a foraging/social context: {n_types}")
    print(f"    foraging-associated     : {n_for}")
    print(f"    socializing-associated  : {n_soc}")
    print(f"    foraging-specialist     : {n_for_spec}  {sorted(cls[cls.label=='foraging-specialist'].call_type)}")
    print(f"    socializing-specialist  : {n_soc_spec}  {sorted(cls[cls.label=='socializing-specialist'].call_type)}")
    print(f"    used in both            : {n_both}  {sorted(cls[cls.label=='both'].call_type)}")
    print(f"  specialization index (single-context / total) = {specialization_index:.2f}")
    print(f"  Fisher exact (foraging x socializing disjointness) p = {p:.3g}")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig_rel = "figures/calltype_context_specialization.png"
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    cats = ["foraging-specialist", "socializing-specialist", "both"]
    vals = [n_for_spec, n_soc_spec, n_both]
    ax.bar(cats, vals, color=["#2a7fb8", "#d1495b", "#bbbbbb"])
    for i, v in enumerate(vals):
        ax.text(i, v, str(v), ha="center", va="bottom", fontsize=11)
    ax.set_ylabel("number of catalogue call types")
    ax.set_title("Catalogue call types specialize by context (foraging vs socializing)\n"
                 f"NRKW+SRKW; specialization index {specialization_index:.2f}; "
                 f"Fisher p={p:.3g} (literature-grounded: Ford 1989, Foote 2008)")
    plt.tight_layout()
    plt.savefig(REPO_ROOT / fig_rel, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Figure saved: {fig_rel}")

    summary = {
        "analysis": "catalogue_calltype_foraging_vs_socializing_specialization",
        "criterion": "C2 (more than one behavioural context), catalogue / named-unit level",
        "context_label_source": "published field ethograms (NOT embeddings): "
                                "ford1989, foote2008, riesch2008, yurk2002",
        "populations": args.populations,
        "n_call_types": n_types,
        "n_foraging_associated": n_for,
        "n_socializing_associated": n_soc,
        "n_foraging_specialist": n_for_spec,
        "n_socializing_specialist": n_soc_spec,
        "n_both": n_both,
        "foraging_specialist_types": sorted(cls[cls.label == "foraging-specialist"].call_type.tolist()),
        "socializing_specialist_types": sorted(cls[cls.label == "socializing-specialist"].call_type.tolist()),
        "both_context_types": sorted(cls[cls.label == "both"].call_type.tolist()),
        "specialization_index": specialization_index,
        "disjointness_fisher_p": float(p),
        "figure": fig_rel,
        "caveats": [
            "Context labels come from published ethograms, not from our embeddings "
            "(non-circular); this maps the documented contextual use of the recovered "
            "catalogue units, complementing the H5 embedding decode.",
            "Supports context-specific PRODUCTION across two functionally distinct "
            "contexts (foraging vs social); NOT a claim of referential meaning.",
            "Ford 1989: 'no call type was correlated exclusively with any behaviour' - "
            "this is differential specialization, not deterministic mapping.",
        ],
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "calltype_context_specialization_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print("  Metrics JSON: reports/calltype_context_specialization_summary.json")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

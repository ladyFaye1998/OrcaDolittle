#!/usr/bin/env python3
"""C2-multi (catalogue level): do the validated catalogue call types span MORE
THAN ONE behavioural context, and how broadly?

`run_calltype_context_specialization.py` collapsed the contrast to the single
foraging-vs-socializing axis. Context-specific communication is conventionally
framed as use across *more than one context (e.g., alarm, mating, foraging)*, so
this script makes the breadth explicit: it maps each validated
Rung-1 call type onto the canonical killer-whale **behavioural** contexts used in
the published ethograms - foraging, travelling, resting, socializing, greeting/
excitement (pod meetings), multi-pod aggregation, and beach-rubbing
[@ford1989; @foote2008; @riesch2008; @yurk2002] - and reports how many distinct
contexts the recovered repertoire covers and how the named units distribute
across them.

Non-circular framing (identical to C2): the context labels come from the
published field ethograms, independently of the embeddings. This is a literature-grounded
map of the documented behavioural use of the units recovered in Rung 1; it
complements the DTAG embedding decode (H5), which carries the inferential weight
on the production side. Pure identity-signalling associations (single-pod /
clan-identity / inter-clan), which are about *who* is calling rather than *what
behavioural context* the call is produced in, are outside the behavioural-context
axis. This is the production-side reading of the "more than one context" criterion
at the named-unit level.

Output: a call-type x behavioural-context incidence map, the number of distinct
contexts covered, a per-type context-count distribution, a specialization index,
and a chi-square test that the named units are non-uniformly distributed across
the behavioural contexts (with an explicit small-n caveat).

Usage:
  python scripts/run_calltype_multicontext.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chisquare

REPO_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = REPO_ROOT / "figures"
REPORTS_DIR = REPO_ROOT / "reports"
DEFAULT_TABLE = "data/join_tables/call_type_to_context.csv"

# Canonical killer-whale behavioural contexts (Ford 1989 activity states + Foote
# 2008 social contexts), in a fixed display order. Identity-signalling contexts
# are intentionally NOT behavioural contexts and are mapped to None below.
CONTEXT_ORDER = [
    "foraging",
    "travelling",
    "resting",
    "socializing",
    "greeting_excitement",
    "aggregation",
    "beach_rubbing",
]

# Raw ethogram context strings -> canonical behavioural context (or None to drop).
CONTEXT_MAP = {
    "foraging": "foraging",
    "silent_foraging": "foraging",
    "travelling": "travelling",
    "resting": "resting",
    "low_arousal": "resting",
    "socializing": "socializing",
    "social_travelling": "socializing",
    "greeting": "greeting_excitement",
    "pod_meeting": "greeting_excitement",
    "excitement": "greeting_excitement",
    "large_aggregation": "aggregation",
    "multi_pod": "aggregation",
    "multi_pod_affiliation": "aggregation",
    # identity / affiliation signalling: not a behavioural context -> dropped
    "single_pod": None,
    "single_pod_identity": None,
    "clan_identity": None,
    "inter_clan_association": None,
    "distinct_LFC_syllables": None,
}


def canonical(ctx: str) -> str | None:
    return CONTEXT_MAP.get(str(ctx).strip().lower(), None)


def build_incidence(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """One row per (population, call_type); columns are canonical behavioural
    contexts with 0/1 documented incidence from the ethogram rows."""
    rows = []
    for (pop, ct), grp in df.groupby(["population", "call_type"], sort=False):
        contexts: set[str] = set()
        for _, r in grp.iterrows():
            for raw in (r["primary_context"], r["secondary_context"]):
                c = canonical(raw)
                if c is not None:
                    contexts.add(c)
        if not contexts:  # pure identity-signalling type: no behavioural context
            continue
        row = {"population": pop, "call_type": ct}
        for c in CONTEXT_ORDER:
            row[c] = int(c in contexts)
        row["n_contexts"] = len(contexts)
        rows.append(row)
    inc = pd.DataFrame(rows)
    covered = [c for c in CONTEXT_ORDER if c in inc.columns and inc[c].sum() > 0]
    return inc, covered


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--table", default=DEFAULT_TABLE)
    ap.add_argument("--populations", nargs="*", default=["NRKW", "SRKW"],
                    help="catalogue populations recovered in Rung 1")
    args = ap.parse_args()

    path = (REPO_ROOT / args.table) if not Path(args.table).is_absolute() else Path(args.table)
    df = pd.read_csv(path).fillna("")
    df = df[df["population"].isin(args.populations)]

    inc, covered = build_incidence(df)
    n_types = int(len(inc))
    n_contexts_covered = len(covered)
    per_context_counts = {c: int(inc[c].sum()) for c in covered}
    n_single = int((inc["n_contexts"] == 1).sum())
    n_multi = int((inc["n_contexts"] >= 2).sum())
    specialization_index = n_single / n_types if n_types else 0.0
    mean_contexts_per_type = float(inc["n_contexts"].mean()) if n_types else 0.0

    # Non-uniformity test: are the named units distributed unevenly across the
    # behavioural contexts? Chi-square goodness-of-fit of the per-context
    # incidence counts vs a uniform expectation (small-n; descriptive support).
    obs = np.array([per_context_counts[c] for c in covered], dtype=float)
    exp = np.full(len(covered), obs.sum() / len(covered))
    chi2, chi2_p = chisquare(obs, exp)

    print("\n" + "=" * 70)
    print("C2-MULTI (CATALOGUE): BEHAVIOURAL-CONTEXT BREADTH OF VALIDATED UNITS")
    print("=" * 70)
    print(f"  populations            : {', '.join(args.populations)} (validated Rung-1 catalogue)")
    print(f"  call types with a context: {n_types}")
    print(f"  distinct behavioural contexts covered: {n_contexts_covered}  {covered}")
    print(f"  types per context      : {per_context_counts}")
    print(f"  single-context types   : {n_single}   multi-context types: {n_multi}")
    print(f"  specialization index   : {specialization_index:.2f}")
    print(f"  mean contexts per type : {mean_contexts_per_type:.2f}")
    print(f"  chi-square non-uniformity across contexts: chi2={chi2:.2f}, p={chi2_p:.3g}")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig_rel = "figures/calltype_multicontext.png"
    inc_sorted = inc.sort_values(["population", "n_contexts", "call_type"],
                                 ascending=[True, False, True]).reset_index(drop=True)
    mat = inc_sorted[covered].to_numpy()
    fig, ax = plt.subplots(figsize=(max(7.5, 1.1 * len(covered) + 3),
                                    max(4.5, 0.32 * n_types + 1.5)))
    ax.imshow(mat, aspect="auto", cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(covered)))
    ax.set_xticklabels([c.replace("_", "/\n") for c in covered], fontsize=9)
    ax.set_yticks(range(n_types))
    ax.set_yticklabels([f"{r.population} {r.call_type}" for r in inc_sorted.itertuples()],
                       fontsize=7)
    for i in range(n_types):
        for j in range(len(covered)):
            if mat[i, j]:
                ax.text(j, i, "•", ha="center", va="center", color="white", fontsize=9)
    ax.set_title(
        "Validated catalogue call types span more than one behavioural context\n"
        f"NRKW+SRKW; {n_contexts_covered} contexts; specialization index "
        f"{specialization_index:.2f} (literature-grounded: Ford 1989, Foote 2008, Riesch 2008)",
        fontsize=10)
    plt.tight_layout()
    plt.savefig(REPO_ROOT / fig_rel, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Figure saved: {fig_rel}")

    type_context_map = {
        f"{r.population} {r.call_type}": [c for c in covered if getattr(r, c)]
        for r in inc.itertuples()
    }
    summary = {
        "analysis": "catalogue_calltype_multicontext_breadth",
        "criterion": "C2 / versatility (communication in MORE THAN ONE context), "
                     "catalogue / named-unit level",
        "context_axis": "canonical killer-whale BEHAVIOURAL contexts "
                        "(activity + social), NOT identity signalling",
        "context_label_source": "published field ethograms (NOT embeddings): "
                                "ford1989, foote2008, riesch2008, yurk2002",
        "populations": args.populations,
        "contexts_covered": covered,
        "n_contexts_covered": n_contexts_covered,
        "n_call_types": n_types,
        "per_context_type_counts": per_context_counts,
        "n_single_context_types": n_single,
        "n_multi_context_types": n_multi,
        "specialization_index": specialization_index,
        "mean_contexts_per_type": round(mean_contexts_per_type, 3),
        "nonuniformity_chisquare": round(float(chi2), 3),
        "nonuniformity_chisquare_p": float(chi2_p),
        "type_context_map": type_context_map,
        "figure": fig_rel,
        "caveats": [
            "Context labels come from published field ethograms, NOT from our "
            "embeddings (non-circular); this maps documented behavioural use of "
            "the recovered units and complements the H5 embedding decode.",
            "Behavioural-context axis only: identity-signalling associations "
            "(single-pod / clan-identity / inter-clan) are excluded because they "
            "encode caller identity, not behavioural context.",
            "Supports context-specific PRODUCTION across more than one "
            "behavioural context at the named-unit level; NOT a claim of meaning.",
            "Small n (catalogue types with a documented behavioural context); the "
            "chi-square is descriptive support, and Ford 1989 notes no call type "
            "is correlated exclusively with one behaviour - this is differential "
            "specialization, not deterministic mapping.",
        ],
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "calltype_multicontext_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print("  Metrics JSON: reports/calltype_multicontext_summary.json")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

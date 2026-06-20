#!/usr/bin/env python3
"""Derive non-circular behavioural-context labels from open DTAG movement data.

This builds the *label side* of the within-individual context-decoding design
(see docs/decode_context_plan.md). Behavioural context is defined from
**movement and kinematics only** (dive depth, duration, and jerk-derived
prey-capture events), never from acoustic variables (buzzes / slow clicks),
so that a later decode of context from the whales' *communicative calls* is
not circular [@tennessen2019; @holt2024masking].

Data substrate (open, CC-BY-4.0):
  Zenodo 10.5281/zenodo.13308835 -- calibrated movement + per-dive variables
  for 25 suction-cup DTAG deployments on fish-eating killer whales (NRKW+SRKW)
  in the Salish Sea, 2009-2014 [@tennessen2019; @holt2024masking].

`foraging_data.csv` columns used:
  population (NRKW/SRKW), deployment, tagID, sex, divenum,
  maxdep (max dive depth, m), durwho (dive duration, s),
  kindet (kinematic prey-capture detections; jerk-based, non-acoustic).
  (bzsounds, sc, NLmax are acoustic / noise and are *reported only*, never
  used to define the context label.)

Output:
  data/join_tables/dtag_dive_context.csv  -- one row per dive with context label
  reports/dtag_context_power.json          -- per-individual class balance / power

Usage:
  python scripts/dtag_movement_states.py            # downloads csv if absent
  python scripts/dtag_movement_states.py --deep-m 30
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXT = REPO / "data" / "external" / "dtag"
CSV = EXT / "foraging_data.csv"
OUT = REPO / "data" / "join_tables" / "dtag_dive_context.csv"
REPORT = REPO / "reports" / "dtag_context_power.json"
CSV_URL = "https://zenodo.org/records/13308835/files/foraging_data.csv?download=1"


def ensure_csv() -> None:
    if CSV.exists():
        return
    EXT.mkdir(parents=True, exist_ok=True)
    print(f"Downloading foraging_data.csv -> {CSV}")
    urllib.request.urlretrieve(CSV_URL, CSV)


def label_context(df, deep_m: float):
    """Movement/kinematic-only binary context: foraging vs non-foraging.

    foraging  := kinematic prey-capture present (kindet > 0) OR deep dive
                 (maxdep >= deep_m), following the deep-pursuit signature in
                 the HMM state analysis [@tennessen2019].
    non_forag := shallow dive with no kinematic capture event.
    Neither rule uses any acoustic variable, so the label is independent of
    the call stream we later try to decode it from.
    """
    import numpy as np

    deep = df["maxdep"].astype(float) >= deep_m
    capture = df["kindet"].astype(float) > 0
    ctx = np.where(deep | capture, "foraging", "non_foraging")
    return ctx


def main() -> int:
    import pandas as pd

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--deep-m", type=float, default=30.0,
                   help="depth (m) at/above which a dive counts as deep foraging")
    args = p.parse_args()

    ensure_csv()
    df = pd.read_csv(CSV)
    df["context"] = label_context(df, args.deep_m)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    keep = ["population", "deployment", "tagID", "sex", "divenum",
            "maxdep", "durwho", "kindet", "bzsounds", "sc", "context"]
    keep = [c for c in keep if c in df.columns]
    df[keep].to_csv(OUT, index=False)

    # Power check: within-individual decode needs individuals that visit BOTH
    # contexts, so that a leave-individual-out model is not just learning identity.
    per = (df.groupby(["deployment", "population", "sex"])["context"]
             .value_counts().unstack(fill_value=0))
    per.columns = [str(c) for c in per.columns]
    for c in ("foraging", "non_foraging"):
        if c not in per.columns:
            per[c] = 0
    per["total"] = per["foraging"] + per["non_foraging"]
    per["has_both"] = (per["foraging"] > 0) & (per["non_foraging"] > 0)

    by_pop = df.groupby("population")["context"].value_counts().unstack(fill_value=0)

    summary = {
        "source": "Zenodo 10.5281/zenodo.13308835 (DTAG calibrated movement + per-dive variables)",
        "label_rule": f"foraging = (kindet>0 OR maxdep>={args.deep_m} m); else non_foraging "
                      f"(movement/kinematic only, no acoustic variables)",
        "n_dives": int(len(df)),
        "n_deployments": int(df["deployment"].nunique()),
        "by_population_dives": {k: {str(kk): int(vv) for kk, vv in v.items()}
                                 for k, v in by_pop.to_dict("index").items()},
        "context_counts": {str(k): int(v) for k, v in df["context"].value_counts().items()},
        "deployments_with_both_contexts": int(per["has_both"].sum()),
        "deployments_total": int(len(per)),
        "median_dives_per_deployment": float(per["total"].median()),
        "per_deployment": {
            idx[0]: {
                "population": idx[1], "sex": idx[2],
                "foraging": int(row["foraging"]),
                "non_foraging": int(row["non_foraging"]),
                "has_both": bool(row["has_both"]),
            }
            for idx, row in per.iterrows()
        },
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Dives: {summary['n_dives']}  deployments: {summary['n_deployments']}")
    print(f"Context counts: {summary['context_counts']}")
    print(f"By population: {summary['by_population_dives']}")
    print(f"Deployments with BOTH contexts (usable for within-individual decode): "
          f"{summary['deployments_with_both_contexts']} / {summary['deployments_total']}")
    print(f"Wrote {OUT}")
    print(f"Wrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

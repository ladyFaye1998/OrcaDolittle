#!/usr/bin/env python3
"""H6 (behavioural response side): differential response of wild killer whales to
broadcast conspecific calls.

This is the *response-criterion* (perception-side) result that the archival
ecotype/call-type/DTAG heads cannot supply. It is a re-analysis of a published,
peer-reviewed conspecific playback experiment on wild killer whales
[@filatova2011playback]: 2-min sequences of same-pod vs different-pod calls were
broadcast to free-ranging Kamchatkan resident killer whales (FEROP, Avacha Gulf,
2006-2008) and the per-trial behavioural response was scored.

The behavioural experiment is prior published work; our contribution is (a) the
explicit, reproducible statistic on the per-trial table transcribed in
`data/join_tables/filatova2011_playback_trials.csv`, and (b) the embedding-based
stimulus/matching model in `scripts/run_playback_response.py` (which encodes the
public FEROP call catalogue [@russianorca_catalogue] with frozen AVES2). This
script computes only (a) -- the differential-response contingency -- so it runs
with no audio and no encoder.

Criteria addressed (the interspecies-communication criteria of Yovel & Rechavi
[@yovel2023doctor]):
  * endogenous signals - broadcast signals are the animals' OWN conspecific calls.
  * measurable response - a behavioural response to a broadcast signal.
  * no associative learning - wild, free-ranging animals, first exposure, no conditioning.

The result is response-criterion evidence (the perception leg of Rung 2/3); it is
NOT a claim of referential meaning. Reported honestly whichever way it comes out.

Usage:
  python scripts/run_playback_response_stats.py
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
DEFAULT_TRIALS = "data/join_tables/filatova2011_playback_trials.csv"


def contingency(df: pd.DataFrame) -> dict:
    """2x2: stimulus_type (same_pod / different_pod) x vocal_response (yes / no)."""
    same = df[df["stimulus_type"] == "same_pod"]
    diff = df[df["stimulus_type"] == "different_pod"]
    table = [
        [int((same["vocal_response"] == "yes").sum()), int((same["vocal_response"] == "no").sum())],
        [int((diff["vocal_response"] == "yes").sum()), int((diff["vocal_response"] == "no").sum())],
    ]
    odds, p = fisher_exact(table, alternative="two-sided")
    return {
        "table_rows": ["same_pod", "different_pod"],
        "table_cols": ["responded", "silent"],
        "table": table,
        "n_same_pod": int(len(same)),
        "n_different_pod": int(len(diff)),
        "fisher_exact_p_two_sided": float(p),
    }


def pool_pseudoreplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse trials sharing a pooled_id (same recipient + stimulus) to one row,
    matching the paper's pseudoreplication control."""
    pooled_rows, seen = [], set()
    for _, r in df.iterrows():
        pid = r.get("pooled_id")
        if isinstance(pid, str) and pid.strip():
            if pid in seen:
                continue
            seen.add(pid)
        pooled_rows.append(r)
    return pd.DataFrame(pooled_rows)


def make_figure(raw: dict, pooled: dict, path: Path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    for ax, res, title in [
        (axes[0], raw, "All trials (n=14)"),
        (axes[1], pooled, "Pseudoreplication-controlled"),
    ]:
        same_resp, same_sil = res["table"][0]
        diff_resp, diff_sil = res["table"][1]
        x = ["same-pod\nplayback", "different-pod\nplayback"]
        ax.bar(x, [same_resp, diff_resp], color="#2a7fb8", label="vocal response")
        ax.bar(x, [same_sil, diff_sil], bottom=[same_resp, diff_resp],
               color="#d9d9d9", label="silent")
        ax.set_ylabel("number of playbacks")
        ax.set_title(f"{title}\nFisher exact p = {res['fisher_exact_p_two_sided']:.3g}")
        ax.legend(fontsize=8)
    plt.suptitle("H6: wild killer whales respond vocally to broadcast conspecific calls\n"
                 "(same-pod vs different-pod; re-analysis of Filatova et al. 2011)",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trials", default=DEFAULT_TRIALS)
    args = ap.parse_args()

    path = (REPO_ROOT / args.trials) if not Path(args.trials).is_absolute() else Path(args.trials)
    df = pd.read_csv(path)
    df["vocal_response"] = df["vocal_response"].astype(str).str.strip()
    df["stimulus_type"] = df["stimulus_type"].astype(str).str.strip()

    raw = contingency(df)
    pooled = contingency(pool_pseudoreplicates(df))

    # Descriptive direction-change tally (the paper reports this is n.s., p=0.444,
    # due to small n; we report counts only and do not over-test the subset).
    toward = int((df["direction_change"].astype(str).str.strip() == "toward").sum())

    print("\n" + "=" * 66)
    print("H6: RESPONSE TO BROADCAST CONSPECIFIC CALLS (Filatova et al. 2011)")
    print("=" * 66)
    print(f"  trials file: {args.trials}")
    print(f"\n  All trials (n={len(df)}):")
    print(f"    same-pod    responded/silent = {raw['table'][0]}")
    print(f"    different-pod responded/silent = {raw['table'][1]}")
    print(f"    Fisher exact (two-sided) p = {raw['fisher_exact_p_two_sided']:.3g}")
    print(f"\n  Pseudoreplication-controlled:")
    print(f"    same-pod    responded/silent = {pooled['table'][0]}")
    print(f"    different-pod responded/silent = {pooled['table'][1]}")
    print(f"    Fisher exact (two-sided) p = {pooled['fisher_exact_p_two_sided']:.3g}  (paper: 0.002)")

    fig_rel = "figures/playback_response.png"
    make_figure(raw, pooled, REPO_ROOT / fig_rel)
    print(f"\n  Figure saved: {fig_rel}")

    summary = {
        "head": "H6",
        "analysis": "response_to_broadcast_conspecific_calls",
        "behavioural_source": "filatova2011playback (Marine Mammal Science 27(2):E26-E42)",
        "behavioural_source_note": (
            "Prior published conspecific playback experiment on wild killer whales; "
            "this script recomputes the differential-response statistic from the "
            "transcribed per-trial table. The embedding/matching model is in "
            "run_playback_response.py."),
        "criteria_addressed": {
            "C1_endogenous_signals": True,
            "C3_measurable_response_to_broadcast": True,
            "no_learning_naive_wild_animals": True,
        },
        "all_trials": raw,
        "pseudoreplication_controlled": pooled,
        "primary_result": "pseudoreplication_controlled",
        "direction_toward_boat_trials": toward,
        "figure": fig_rel,
        "caveats": [
            "Behavioural experiment is prior published work (Filatova et al. 2011); "
            "our contribution is the reproducible statistic + the embedding model.",
            "Small sample (14 playbacks; 6 vs 6 after pseudoreplication control) -- "
            "typical for cetacean playback but a real power limit.",
            "Differential vocal response = the response/perception criterion "
            "(receivers act on the broadcast signal); NOT a claim of referential meaning.",
            "Direction-change is reported descriptively; the paper found it n.s. (p=0.444).",
        ],
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "playback_response_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"  Metrics JSON: reports/playback_response_summary.json")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Derive a *three-state* movement-only behavioural context for each call.

This extends the binary foraging/non-foraging label (scripts/dtag_context_labels.py)
to a multi-context label so the decode can speak to "communication in more than one
context" rather than a single foraging contrast. As before, every label is defined
from the **movement / kinematic channel only** (dive depth, jerk-derived prey-capture,
and dynamic body acceleration), never from any acoustic variable, so a later decode of
context from the whales' *communicative calls* is non-circular [@tennessen2019;
@holt2024masking].

Three behavioural contexts on two independent movement axes (depth + dynamic
acceleration), following standard biologging practice [@tennessen2019]:

  foraging    := dive reaches DEEP_M OR contains a jerk prey-capture spike
                 (deep-pursuit signature; depth/jerk axis).
  travelling  := not foraging AND high dynamic body acceleration (ODBA), i.e.
                 active sustained locomotion (activity axis).
  resting     := not foraging AND low ODBA, i.e. quiescent / low-activity.

The travelling/resting split uses a **per-deployment** ODBA median so that
between-tag gain/placement differences cannot stand in for behaviour, and so the
split is calibrated to each individual rather than a pooled threshold.

Reuses scripts/dtag_context_labels.py for the PRH loader, the foraging dive rule, and
the per-deployment download, so the foraging class is identical to the binary build.

Inputs:
  --clips DIR    folder with clips_manifest.json (default D:/dtag_run/clips)
  --labels DIR   where prh50.mat live / are downloaded (default repo data/external/dtag)
Outputs:
  <clips>/context3_labeled_calls.csv    one row per call (clip, deployment, abs_t, dur, context3)
  reports/context3_label_yield.json     per-individual x context counts (power check)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import dtag_context_labels as base  # load_prh, ensure_prh, dive_context, _zenodo_index

REPO = Path(__file__).resolve().parent.parent
REPORT = REPO / "reports" / "context3_label_yield.json"

ODBA_WIN_S = 2.0    # window (s) for the running mean that defines the static accel component


def odba_series(A: np.ndarray, fs: float) -> np.ndarray | None:
    """Per-sample Overall Dynamic Body Acceleration (ODBA) from calibrated accel.

    dynamic accel = A - running_mean(A); ODBA = sum of |dynamic| across the 3 axes.
    A standard, non-acoustic locomotor-activity proxy [@tennessen2019]. Returns None
    if the deployment has no usable 3-axis acceleration.
    """
    if A is None or A.ndim != 2 or A.shape[1] < 3 or A.shape[0] < 3:
        return None
    win = max(int(round(ODBA_WIN_S * fs)), 1)
    kern = np.ones(win) / win
    dyn = np.empty_like(A[:, :3], dtype=float)
    for k in range(3):
        static = np.convolve(A[:, k].astype(float), kern, mode="same")
        dyn[:, k] = A[:, k].astype(float) - static
    return np.abs(dyn).sum(axis=1)


def three_state(p, fs, A):
    """Per-sample context in {2:foraging, 1:travelling, 0:resting, -1:undefined}."""
    forag, _ = base.dive_context(p, fs, A)          # 1 = foraging, 0 = non-foraging
    odba = odba_series(A, fs)
    ctx = np.full(len(p), -1, dtype=np.int8)
    ctx[forag == 1] = 2                              # foraging
    nonf = forag == 0
    if odba is None:
        return ctx, None                             # cannot split travel/rest for this tag
    thr = float(np.nanmedian(odba[nonf])) if nonf.any() else float("nan")
    if np.isfinite(thr):
        ctx[nonf & (odba >= thr)] = 1                # travelling (active)
        ctx[nonf & (odba < thr)] = 0                 # resting (quiescent)
    return ctx, thr


CTX_NAME = {2: "foraging", 1: "travelling", 0: "resting"}


def main() -> int:
    import pandas as pd

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clips", default=r"D:/dtag_run/clips")
    ap.add_argument("--labels", default=str(base.DEF_LABELS))
    args = ap.parse_args()

    clips = Path(args.clips)
    labels = Path(args.labels)
    manifest_path = clips / "clips_manifest.json"
    if not manifest_path.exists():
        ap.error(f"no clips_manifest.json in {clips} — run dtag_local_extract.py first")
    M = pd.DataFrame(json.loads(manifest_path.read_text()))
    deployments = sorted(M["deployment"].unique())
    print(f"{len(M)} clips across {len(deployments)} deployment(s)")

    index = None
    CTX, THR = {}, {}
    for dep in deployments:
        prh = base.ensure_prh(dep, labels, index)
        if prh is None:
            continue
        if index is None:
            index = base._zenodo_index(base.ZEN_MOVEMENT)
        p, fs, A = base.load_prh(prh)
        if p is None:
            print(f"  {dep}: no depth variable — skipped")
            continue
        ctx, thr = three_state(p, fs, A)
        CTX[dep] = (ctx, fs, len(p))
        THR[dep] = thr
        mins = {CTX_NAME[k]: round((ctx == k).sum() / fs / 60, 1) for k in (2, 1, 0)}
        print(f"  {dep}: {round(len(p)/fs/60,1)} min  {mins}  odba_thr={thr}")

    def label(dep, abs_t):
        if dep not in CTX:
            return -1
        ctx, fs, n = CTX[dep]
        i = int(abs_t * fs)
        return int(ctx[i]) if 0 <= i < n else -1

    M["ctx_int"] = [label(d, t) for d, t in zip(M["deployment"], M["abs_t"])]
    M = M[M["ctx_int"] >= 0].copy()
    M["context3"] = M["ctx_int"].map(CTX_NAME)
    print(f"\ncalls with a 3-state context label: {len(M)}")
    if len(M) == 0:
        print("0 calls fell inside any context timeline — check abs_t alignment.")
        return 1

    cross = pd.crosstab(M["deployment"], M["context3"])
    for c in ("foraging", "travelling", "resting"):
        if c not in cross.columns:
            cross[c] = 0
    cross = cross[["foraging", "travelling", "resting"]]
    print("\nYield per individual x context:")
    print(cross)
    usable_all3 = [d for d in cross.index if (cross.loc[d] > 0).sum() == 3]
    usable_ge2 = [d for d in cross.index if (cross.loc[d] > 0).sum() >= 2]
    print(f"\nindividuals with all 3 contexts: {len(usable_all3)}; with >=2: {len(usable_ge2)}")

    out_csv = clips / "context3_labeled_calls.csv"
    M[["clip", "deployment", "abs_t", "dur", "context3"]].to_csv(out_csv, index=False)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "source": "Zenodo 13308835 prh50.mat (depth + jerk + ODBA), movement-only",
        "label_rule": {
            "foraging": f"dive maxdep>={base.DEEP_M} m OR jerk prey-capture spike",
            "travelling": "non-foraging AND ODBA >= per-deployment median",
            "resting": "non-foraging AND ODBA < per-deployment median",
            "odba_window_s": ODBA_WIN_S,
        },
        "n_labeled_calls": int(len(M)),
        "context_counts": {k: int(v) for k, v in M["context3"].value_counts().items()},
        "individuals_all3_contexts": usable_all3,
        "individuals_ge2_contexts": usable_ge2,
        "odba_threshold_per_deployment": {k: (None if v is None or not np.isfinite(v) else float(v))
                                           for k, v in THR.items()},
        "yield": {d: {c: int(cross.loc[d, c]) for c in cross.columns} for d in cross.index},
    }
    REPORT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nwrote {out_csv}\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

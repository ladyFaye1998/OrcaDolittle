#!/usr/bin/env python3
"""Join locally-decoded call clips to movement-only behavioural context.

Label side of the confound-clean context decode (see docs/decode_context_plan.md).
Behavioural context is defined from the DTAG *movement* channel only (dive depth +
jerk-derived prey-capture), never from the acoustic channel we later decode, so the
test is non-circular [@tennessen2019; @holt2024masking].

Pipeline position:
  scripts/dtag_local_extract.py  -> clips/ + clips_manifest.json  (audio side, done locally)
  THIS SCRIPT                    -> per-clip context label + power check
  (then) AVES2 encode + leave-individual-out decode               (decision side)

Context series mirrors notebook Cell 6 exactly; the abs_t->context join mirrors Cell 8.

Inputs:
  --clips DIR        folder holding clips_manifest.json (default: D:/dtag_run/clips)
  --labels DIR       where prh50.mat live / are downloaded (default repo data/external/dtag)
Outputs:
  <clips>/context_labeled_calls.csv     one row per labelled call (clip, deployment, abs_t, context)
  reports/context_label_yield.json      per-individual x context counts (power check)

prh50.mat are MATLAB v7 or v7.3; both are handled (scipy.io.loadmat, h5py fallback).
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
DEF_LABELS = REPO / "data" / "external" / "dtag"
REPORT = REPO / "reports" / "context_label_yield.json"
ZEN_MOVEMENT = "13308835"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "*/*"}

# Movement-only context thresholds (identical to notebook Cell 2 / Cell 6).
DEEP_M = 30.0       # dive reaching >= this depth = foraging (deep pursuit) [@tennessen2019]
SURFACE_M = 5.0     # depth below this = at-surface (between dives)
MIN_DIVE_S = 10.0   # minimum dive duration


def _zenodo_index(record: str) -> dict:
    req = urllib.request.Request(f"https://zenodo.org/api/records/{record}", headers=UA)
    meta = json.loads(urllib.request.urlopen(req, timeout=120).read())
    out = {}
    for f in meta.get("files", []):
        key = f.get("key") or f.get("filename")
        link = (f.get("links", {}) or {}).get("self") or f.get("download")
        out[key] = link
    return out


def ensure_prh(dep: str, labels: Path, index: dict | None) -> Path | None:
    labels.mkdir(parents=True, exist_ok=True)
    dst = labels / f"{dep}prh50.mat"
    if dst.exists() and dst.stat().st_size > 0:
        return dst
    if index is None:
        index = _zenodo_index(ZEN_MOVEMENT)
    key = f"{dep}prh50.mat"
    if key not in index:
        print(f"  no prh50 for {dep} in deposit {ZEN_MOVEMENT}")
        return None
    print(f"  downloading {key} ...")
    tmp = dst.with_suffix(".part")
    req = urllib.request.Request(index[key], headers=UA)
    with urllib.request.urlopen(req, timeout=3600) as r, open(tmp, "wb") as fh:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
    tmp.replace(dst)
    return dst


def load_prh(path: Path):
    """Return (depth[1d], fs, A[n,3] or None) from a prh50.mat (v7 or v7.3)."""
    def pick(d, *names):
        for n in names:
            if n in d and d[n] is not None:
                return np.asarray(d[n], dtype=float).squeeze()
        return None

    try:
        from scipy.io import loadmat
        m = loadmat(str(path), squeeze_me=True, struct_as_record=False)
        p = pick(m, "p", "P", "depth", "Depth")
        fs = pick(m, "fs", "Fs", "sampling_rate")
        A = pick(m, "A", "Aw", "acc")
    except (NotImplementedError, ValueError):
        import h5py
        with h5py.File(str(path), "r") as h:
            keys = {k: k for k in h.keys()}
            def hget(*names):
                for n in names:
                    if n in keys:
                        return np.asarray(h[keys[n]]).squeeze()
                return None
            p = hget("p", "P", "depth", "Depth")
            fs = hget("fs", "Fs", "sampling_rate")
            A = hget("A", "Aw", "acc")
            if A is not None and A.ndim == 2 and A.shape[0] < A.shape[1]:
                A = A.T
    fs = float(np.atleast_1d(fs)[0]) if fs is not None else 50.0
    return p, fs, A


def dive_context(p, fs, A):
    """Per-sample context (1=foraging, 0=non). Dive = depth>SURFACE_M for >=MIN_DIVE_S;
    foraging if it reaches DEEP_M or contains a jerk prey-capture spike. Movement only."""
    below = p > SURFACE_M
    ctx = np.zeros(len(p), dtype=np.int8)
    jerk = jthr = None
    if A is not None and A.ndim == 2 and A.shape[0] >= A.shape[1]:
        jerk = np.linalg.norm(np.diff(A, axis=0), axis=1) * fs
        jthr = np.nanmedian(jerk) + 6 * (np.nanstd(jerk) + 1e-9)
    i, n, dives = 0, len(p), []
    while i < n:
        if below[i]:
            j = i
            while j < n and below[j]:
                j += 1
            if (j - i) / fs >= MIN_DIVE_S:
                maxd = float(np.nanmax(p[i:j]))
                forag = maxd >= DEEP_M
                if jerk is not None and not forag:
                    forag = bool(np.any(jerk[max(i - 1, 0):max(j - 1, 1)] > jthr))
                if forag:
                    ctx[i:j] = 1
                dives.append((i / fs, j / fs, maxd, int(forag)))
            i = j
        else:
            i += 1
    return ctx, dives


def main() -> int:
    import pandas as pd

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clips", default=r"D:/dtag_run/clips",
                    help="folder with clips_manifest.json")
    ap.add_argument("--labels", default=str(DEF_LABELS),
                    help="folder for prh50.mat (downloaded if absent)")
    args = ap.parse_args()

    clips = Path(args.clips)
    labels = Path(args.labels)
    manifest_path = clips / "clips_manifest.json"
    if not manifest_path.exists():
        ap.error(f"no clips_manifest.json in {clips} — run dtag_local_extract.py first")
    manifest = json.loads(manifest_path.read_text())
    M = pd.DataFrame(manifest)
    deployments = sorted(M["deployment"].unique())
    print(f"{len(M)} clips across {len(deployments)} deployment(s): {deployments}")

    index = None
    CTX = {}
    for dep in deployments:
        prh = ensure_prh(dep, labels, index)
        if prh is None:
            continue
        if index is None:
            index = _zenodo_index(ZEN_MOVEMENT)  # cache after first miss/use
        p, fs, A = load_prh(prh)
        if p is None:
            print(f"  {dep}: no depth variable found — keys differ")
            continue
        ctx, dives = dive_context(p, fs, A)
        CTX[dep] = (ctx, fs, len(p))
        fmin = round((ctx == 1).sum() / fs / 60, 1)
        nmin = round((ctx == 0).sum() / fs / 60, 1)
        print(f"  {dep}: {round(len(p) / fs / 60, 1)} min, {len(dives)} dives, "
              f"foraging {fmin} min / non {nmin} min")

    def label(dep, abs_t):
        if dep not in CTX:
            return -1
        ctx, fs, n = CTX[dep]
        i = int(abs_t * fs)
        return int(ctx[i]) if 0 <= i < n else -1

    M["context_int"] = [label(d, t) for d, t in zip(M["deployment"], M["abs_t"])]
    M = M[M["context_int"] >= 0].copy()
    M["context"] = M["context_int"].map({1: "foraging", 0: "non_foraging"})

    print(f"\ncalls with a context label: {len(M)}")
    if len(M) == 0:
        print("0 calls fell inside any context timeline — check abs_t alignment.")
        return 1
    cross = pd.crosstab(M["deployment"], M["context"])
    print("\nYield per individual x context (power check):")
    print(cross)
    usable = [d for d, g in M.groupby("deployment") if g["context"].nunique() == 2]
    print(f"\ndeployments with BOTH contexts (usable for leave-individual-out): {usable}")

    out_csv = clips / "context_labeled_calls.csv"
    M[["clip", "deployment", "abs_t", "dur", "context"]].to_csv(out_csv, index=False)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "n_labeled_calls": int(len(M)),
        "deployments": deployments,
        "usable_both_contexts": usable,
        "thresholds": {"deep_m": DEEP_M, "surface_m": SURFACE_M, "min_dive_s": MIN_DIVE_S},
        "yield": {d: {c: int(cross.loc[d, c]) for c in cross.columns} for d in cross.index},
    }
    REPORT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nwrote {out_csv}\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

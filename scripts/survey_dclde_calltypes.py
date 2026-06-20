#!/usr/bin/env python3
"""Survey DCLDE 2026 per-provider annotation files for call-type labels.

The combined/published DCLDE CSV standardises killer-whale labels to ecotype,
but the original per-provider annotation files retain finer fields - including
`call_type` (Ford/Filatova stereotyped call codes), `clan`, `subclan`, `pod`
[@palmer2025dclde; @ford1989; @filatova2015]. This tool enumerates those files
on the public GCS mirror and, in --scan mode, quantifies how many detections
actually carry a populated `call_type`, per provider, with no credentials.

Read-only. Downloads annotation CSVs to a scratch dir (default data/external,
gitignored) only in --scan mode.

Usage:
  python scripts/survey_dclde_calltypes.py --inventory
  python scripts/survey_dclde_calltypes.py --scan --limit-per-provider 20
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.parse
import urllib.request
from collections import Counter

GCS_API = "https://storage.googleapis.com/storage/v1/b/noaa-passive-bioacoustic/o"
GCS_DL = "https://storage.googleapis.com/noaa-passive-bioacoustic/"
ROOT = "dclde/2027/dclde_2027_killer_whales"
PROVIDERS = ["dfo_crp", "dfo_wdlp", "onc", "orcasound", "scripps",
             "simres", "smru", "uaf", "vfpa"]
CALLTYPE_COLS = ["call_type", "Call Type", "calltype", "CallType"]


def list_annotation_csvs(provider: str):
    prefix = f"{ROOT}/{provider}/annotations/"
    out, token = [], None
    while True:
        url = f"{GCS_API}?prefix={urllib.parse.quote(prefix)}&maxResults=1000"
        if token:
            url += f"&pageToken={token}"
        d = json.load(urllib.request.urlopen(url, timeout=60))
        for it in d.get("items", []):
            if it["name"].endswith(".csv"):
                out.append((it["name"], int(it.get("size", 0))))
        token = d.get("nextPageToken")
        if not token:
            break
    return out


def inventory():
    grand_n = grand_b = 0
    print(f"{'provider':12s} {'csv':>5s} {'MB':>10s}")
    print("-" * 30)
    for pv in PROVIDERS:
        files = list_annotation_csvs(pv)
        n = len(files)
        b = sum(s for _, s in files)
        print(f"{pv:12s} {n:5d} {b/1e6:10.1f}")
        grand_n += n
        grand_b += b
    print("-" * 30)
    print(f"{'TOTAL':12s} {grand_n:5d} {grand_b/1e6:10.1f}")


def scan(limit_per_provider: int):
    import pandas as pd

    grand_calltype = 0
    grand_rows = 0
    all_types: Counter = Counter()
    per_provider = {}
    print(f"{'provider':12s} {'files':>6s} {'rows':>10s} {'call_type':>10s} {'%':>6s}")
    print("-" * 50)
    for pv in PROVIDERS:
        files = list_annotation_csvs(pv)
        files = files[:limit_per_provider] if limit_per_provider else files
        rows = ct = 0
        for name, _ in files:
            try:
                raw = urllib.request.urlopen(GCS_DL + name, timeout=120).read()
                df = pd.read_csv(io.BytesIO(raw), low_memory=False)
            except Exception as exc:  # noqa: BLE001
                print(f"  WARN {name}: {exc}")
                continue
            col = next((c for c in CALLTYPE_COLS if c in df.columns), None)
            rows += len(df)
            if col is not None:
                vals = df[col].dropna()
                vals = vals[vals.astype(str).str.strip().ne("")]
                ct += len(vals)
                all_types.update(vals.astype(str).str.strip().tolist())
        pct = (100 * ct / rows) if rows else 0.0
        per_provider[pv] = {"files_scanned": len(files), "rows": rows,
                            "call_type_rows": ct, "pct": round(pct, 2)}
        print(f"{pv:12s} {len(files):6d} {rows:10d} {ct:10d} {pct:6.2f}")
        grand_calltype += ct
        grand_rows += rows
    print("-" * 50)
    pct = (100 * grand_calltype / grand_rows) if grand_rows else 0.0
    print(f"{'TOTAL':12s} {'':6s} {grand_rows:10d} {grand_calltype:10d} {pct:6.2f}")
    print(f"\nDistinct call_type codes seen: {len(all_types)}")
    print("Top 25:", dict(all_types.most_common(25)))
    summary = {"per_provider": per_provider,
               "total_rows": grand_rows,
               "total_call_type_rows": grand_calltype,
               "distinct_call_types": len(all_types),
               "top_call_types": dict(all_types.most_common(40)),
               "limit_per_provider": limit_per_provider}
    from pathlib import Path
    out = Path(__file__).resolve().parent.parent / "reports" / "dclde_calltype_survey.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nReport written: reports/{out.name}")
    print(f"TOTAL call_type-labeled detections: {grand_calltype} of {grand_rows} rows; "
          f"{len(all_types)} distinct codes")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inventory", action="store_true")
    p.add_argument("--scan", action="store_true")
    p.add_argument("--limit-per-provider", type=int, default=0,
                   help="0 = all files; otherwise cap files scanned per provider")
    args = p.parse_args()
    if args.inventory:
        inventory()
    if args.scan:
        scan(args.limit_per_provider)
    if not (args.inventory or args.scan):
        p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

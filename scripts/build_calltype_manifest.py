#!/usr/bin/env python3
"""Build a call-type manifest from DCLDE per-provider annotation files.

Extracts every detection that carries a populated `call_type` (Ford/Filatova
stereotyped call code) from the public DCLDE 2026 provider annotation CSVs and
writes a normalised manifest for downstream call-type modelling (Rung 1)
[@palmer2025dclde; @ford1989; @filatova2015].

Schema (one row per labelled detection):
  audio_path, start, end, freq_min, freq_max, provider, kw_ecotype,
  clan, subclan, pod, call_type_raw, call_type, call_family, label_source

Label normalisation:
  - strip whitespace; drop trailing '?' and '(...)' uncertainty markers
  - drop non-call codes: Unk/Unknown/'?'/'' and pure-noise rows
  - call_family from leading letters: N->NRKW, S->SRKW, T->Bigg's/transient,
    OFF->offshore (a coarse provenance prior, NOT a re-label of kw_ecotype)

Annotation CSVs are cached under data/external (gitignored). The manifest is
written to data/join_tables (small, committable provenance table).

Usage:
  python scripts/build_calltype_manifest.py --min-per-type 30
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

GCS_API = "https://storage.googleapis.com/storage/v1/b/noaa-passive-bioacoustic/o"
GCS_DL = "https://storage.googleapis.com/noaa-passive-bioacoustic/"
ROOT = "dclde/2027/dclde_2027_killer_whales"
PROVIDERS_WITH_CALLTYPE = ["dfo_crp", "smru", "vfpa"]
CALLTYPE_COLS = ["call_type", "Call Type", "calltype", "CallType"]
NON_CALL = {"", "unk", "unknown", "?", "n/a", "na", "none", "nothing", "nan"}

REPO = Path(__file__).resolve().parent.parent
CACHE = REPO / "data" / "external" / "dclde_annot"
OUT = REPO / "data" / "join_tables" / "call_type_manifest.csv"
REPORT = REPO / "reports" / "calltype_manifest_summary.json"


def list_csvs(provider: str):
    prefix = f"{ROOT}/{provider}/annotations/"
    out, token = [], None
    while True:
        url = f"{GCS_API}?prefix={urllib.parse.quote(prefix)}&maxResults=1000"
        if token:
            url += f"&pageToken={token}"
        d = json.load(urllib.request.urlopen(url, timeout=60))
        for it in d.get("items", []):
            if it["name"].endswith(".csv"):
                out.append(it["name"])
        token = d.get("nextPageToken")
        if not token:
            break
    return out


def fetch_csv(name: str):
    import pandas as pd

    CACHE.mkdir(parents=True, exist_ok=True)
    local = CACHE / name.split("/")[-1]
    if local.exists():
        raw = local.read_bytes()
    else:
        raw = urllib.request.urlopen(GCS_DL + name, timeout=180).read()
        local.write_bytes(raw)
    return pd.read_csv(io.BytesIO(raw), low_memory=False)


def normalise_call_type(val: str):
    s = str(val).strip()
    if s.lower() in NON_CALL:
        return None
    s = re.sub(r"\s*\(.*?\)\s*", "", s)          # drop parentheticals
    s = s.replace(" call", "").replace("call", "").strip()
    s = s.rstrip("?").strip()
    if not s or s.lower() in NON_CALL:
        return None
    # collapse zero-padding variants: S4 -> S04, T2 -> T02 (letter+digits only)
    m = re.fullmatch(r"([A-Za-z]+)(\d+)([a-z]*)", s)
    if m:
        pref, num, suf = m.groups()
        s = f"{pref.upper()}{int(num):02d}{suf}"
    return s


def call_family(code: str):
    c = code.upper()
    if c.startswith("OFF"):
        return "offshore"
    if c.startswith("N"):
        return "NRKW"
    if c.startswith("S"):
        return "SRKW"
    if c.startswith("T"):
        return "Biggs/transient"
    return "other"


def main() -> int:
    import pandas as pd

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--min-per-type", type=int, default=30,
                   help="report (not drop) types with at least this many examples")
    args = p.parse_args()

    rows = []
    for pv in PROVIDERS_WITH_CALLTYPE:
        for name in list_csvs(pv):
            df = fetch_csv(name)
            col = next((c for c in CALLTYPE_COLS if c in df.columns), None)
            if col is None:
                continue
            df = df[df[col].notna()].copy()
            if df.empty:
                continue
            df["call_type"] = df[col].map(normalise_call_type)
            df = df[df["call_type"].notna()]
            for _, r in df.iterrows():
                rows.append({
                    "audio_path": r.get("path", r.get("filename", "")),
                    "start": r.get("start", ""),
                    "end": r.get("end", ""),
                    "freq_min": r.get("freq_min", ""),
                    "freq_max": r.get("freq_max", ""),
                    "provider": pv,
                    "kw_ecotype": r.get("kw_ecotype", ""),
                    "clan": r.get("clan", ""),
                    "subclan": r.get("subclan", ""),
                    "pod": r.get("pod", ""),
                    "call_type_raw": str(r[col]).strip(),
                    "call_type": r["call_type"],
                    "call_family": call_family(r["call_type"]),
                    "label_source": f"dclde/{pv}",
                })

    man = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    man.to_csv(OUT, index=False)

    counts = Counter(man["call_type"])
    usable = {k: v for k, v in counts.items() if v >= args.min_per_type}
    fam = Counter(man["call_family"])
    prov = Counter(man["provider"])
    summary = {
        "manifest_path": "data/join_tables/call_type_manifest.csv",
        "total_labeled_detections": int(len(man)),
        "distinct_call_types": int(len(counts)),
        "call_types_min_examples": args.min_per_type,
        "usable_call_types": len(usable),
        "usable_detections": int(sum(usable.values())),
        "by_family": dict(fam),
        "by_provider": dict(prov),
        "top_usable_types": dict(Counter(usable).most_common(40)),
    }
    REPORT.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Manifest: {OUT}  ({len(man)} rows)")
    print(f"Distinct call types: {len(counts)}")
    print(f"Usable (>= {args.min_per_type} ex): {len(usable)} types, "
          f"{sum(usable.values())} detections")
    print(f"By family: {dict(fam)}")
    print(f"By provider: {dict(prov)}")
    print(f"Report: reports/{REPORT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Fetch the public FEROP Kamchatkan killer-whale call catalogue and build a
manifest for the H6 embedding analysis.

The Filatova et al. 2011 conspecific playback experiment [@filatova2011playback]
used 2-min sequences of Kamchatkan resident discrete calls (call types K1-K34) as
stimuli. The per-call-type exemplar catalogue is public [@russianorca_catalogue]
at http://russianorca.com/sounds/catalog/ as individual WAV files named by call
type (e.g. K1/K1ia.wav, K5/K5iii.wav). This script enumerates those links,
downloads the WAVs to `data/playback/ferop_catalogue/`, and writes a manifest
(`data/join_tables/ferop_catalogue_manifest.csv`) with one row per exemplar:
`call_type, variant, url, local_path`.

Raw audio is excluded from version control (see .gitignore); only the manifest is
committed. Re-run this script to repopulate the audio.

Usage:
  python scripts/build_playback_manifest.py
  python scripts/build_playback_manifest.py --max-types 0   # manifest only, no download
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_URL = "http://russianorca.com/sounds/catalog/index.htm"
AUDIO_DIR = REPO_ROOT / "data" / "playback" / "ferop_catalogue"
MANIFEST = REPO_ROOT / "data" / "join_tables" / "ferop_catalogue_manifest.csv"

# call type is the leading K<number> of the link path, e.g. "K12/K12iiia.wav" -> K12
TYPE_RE = re.compile(r"(K\d+)", re.IGNORECASE)
WAV_RE = re.compile(r'href=["\']([^"\']+\.wav)["\']', re.IGNORECASE)


def fetch_index(url: str) -> str:
    import requests
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def parse_links(html: str, base: str) -> list[dict]:
    rows = []
    for m in WAV_RE.finditer(html):
        href = m.group(1)
        tm = TYPE_RE.search(href)
        if not tm:
            continue
        call_type = tm.group(1).upper()
        variant = Path(href).stem
        rows.append({"call_type": call_type, "variant": variant,
                     "url": urljoin(base, href)})
    # de-duplicate by url
    seen, out = set(), []
    for r in rows:
        if r["url"] not in seen:
            seen.add(r["url"])
            out.append(r)
    return out


def download(rows: list[dict], limit: int) -> None:
    import requests
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for r in rows:
        if limit and n >= limit:
            break
        dest = AUDIO_DIR / f"{r['call_type']}__{r['variant']}.wav"
        r["local_path"] = str(dest.relative_to(REPO_ROOT))
        if dest.exists():
            n += 1
            continue
        try:
            resp = requests.get(r["url"], timeout=60)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            n += 1
        except Exception as e:  # noqa: BLE001
            print(f"  WARN could not fetch {r['url']}: {e}", file=sys.stderr)
            r["local_path"] = ""
    print(f"  downloaded/verified {n} exemplars -> {AUDIO_DIR.relative_to(REPO_ROOT)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-types", type=int, default=0,
                    help="cap exemplars downloaded (0 = all; the catalogue is small)")
    ap.add_argument("--no-download", action="store_true",
                    help="write the manifest of URLs without downloading audio")
    args = ap.parse_args()

    print("\n" + "=" * 66)
    print("FEROP KAMCHATKA CALL CATALOGUE -> H6 PLAYBACK MANIFEST")
    print("=" * 66)
    try:
        html = fetch_index(CATALOG_URL)
    except Exception as e:  # noqa: BLE001
        print(f"  ERROR fetching catalogue index ({e}).")
        print("  Run this on a machine with internet access to russianorca.com.")
        return 1

    rows = parse_links(html, CATALOG_URL)
    types = sorted({r["call_type"] for r in rows}, key=lambda t: int(t[1:]))
    print(f"  found {len(rows)} WAV exemplars across {len(types)} call types: {', '.join(types)}")

    if not args.no_download:
        download(rows, args.max_types)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["call_type", "variant", "url", "local_path"])
        w.writeheader()
        for r in rows:
            r.setdefault("local_path", "")
            w.writerow(r)
    print(f"  manifest written: {MANIFEST.relative_to(REPO_ROOT)} ({len(rows)} rows)")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

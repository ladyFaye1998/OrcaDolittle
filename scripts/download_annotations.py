#!/usr/bin/env python3
"""Download the DCLDE 2026 Annotations.csv from NOAA's Google Cloud Storage.

The collated annotations file (~48 MB) contains 225,000+ call-level annotations
across 23 hydrophone sites and 9 years, with standardized ecotype labels.

Data source: DOI 10.25921/15ey-mh50 (Palmer & Joy, 2025)
GCS bucket: gs://noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/
"""

import sys
from pathlib import Path

import gcsfs

GCS_BASE = "noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales"
ANNOTATIONS_PATH = f"{GCS_BASE}/Annotations.csv"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "dclde"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "Annotations.csv"

    if output_file.exists():
        print(f"Already exists: {output_file}")
        print(f"  Size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
        print("  Delete it to re-download.")
        return

    print("Connecting to NOAA GCS bucket (public, no auth needed)...")
    fs = gcsfs.GCSFileSystem(token="anon")

    info = fs.info(ANNOTATIONS_PATH)
    size_mb = info["size"] / 1024 / 1024
    print(f"Downloading Annotations.csv ({size_mb:.1f} MB)...")

    fs.get(ANNOTATIONS_PATH, str(output_file))

    print(f"Saved to: {output_file}")
    print(f"  Size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")

    # Quick sanity check
    import pandas as pd

    df = pd.read_csv(output_file, nrows=5)
    print(f"\nColumns: {list(df.columns)}")
    print(f"First 5 rows preview:")
    print(df.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main() or 0)

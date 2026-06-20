#!/usr/bin/env python3
"""Download a small sample of DCLDE 2026 audio clips for testing.

Downloads 3 clips from different providers to verify the pipeline works
before pulling the full dataset. Total download: ~15 MB.

Data source: DOI 10.25921/15ey-mh50 (Palmer & Joy, 2025)
"""

import sys
from pathlib import Path

import gcsfs

GCS_BASE = "noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "dclde" / "sample_audio"

SAMPLE_FILES = [
    f"{GCS_BASE}/orcasound/audio/orcasound_lab/1562337136_0004.wav",
    f"{GCS_BASE}/orcasound/audio/orcasound_lab/1562337136_0005.wav",
    f"{GCS_BASE}/orcasound/audio/orcasound_lab/1562337136_0006.wav",
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Connecting to NOAA GCS bucket (public, no auth needed)...")
    fs = gcsfs.GCSFileSystem(token="anon")

    for gcs_path in SAMPLE_FILES:
        filename = Path(gcs_path).name
        output_file = OUTPUT_DIR / filename

        if output_file.exists():
            print(f"  Already exists: {filename}")
            continue

        info = fs.info(gcs_path)
        size_mb = info["size"] / 1024 / 1024
        print(f"  Downloading {filename} ({size_mb:.1f} MB)...")
        fs.get(gcs_path, str(output_file))

    print(f"\nSample audio saved to: {OUTPUT_DIR}")
    print(f"Files:")
    for f in sorted(OUTPUT_DIR.glob("*.wav")):
        print(f"  {f.name} ({f.stat().st_size / 1024 / 1024:.1f} MB)")

    # Quick audio info
    try:
        import soundfile as sf

        for f in sorted(OUTPUT_DIR.glob("*.wav"))[:1]:
            info = sf.info(str(f))
            print(f"\nAudio info ({f.name}):")
            print(f"  Sample rate: {info.samplerate} Hz")
            print(f"  Channels: {info.channels}")
            print(f"  Duration: {info.duration:.1f} s")
            print(f"  Format: {info.subtype}")
    except ImportError:
        print("\n(Install soundfile for audio info: pip install soundfile)")


if __name__ == "__main__":
    sys.exit(main() or 0)

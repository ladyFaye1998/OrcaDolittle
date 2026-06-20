#!/usr/bin/env python3
"""Organize Wellard/Dryad Drive files for the H5-H7 evidence pipeline.

Run from Colab after mounting Drive:

    python scripts/organize_wellard_drive_colab.py --execute --mode move

The default is a dry run. Use --mode copy if you want to populate the new
layout while leaving older cache/root paths in place.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


OUTER_ZIP = "doi_10_5061_dryad_37pvmcvfr__v20200129.zip"
INNER_ZIP = "Wellard_et_al_2020_Acoustic_files_of_Type_C_Killer_Whales_Ross_Sea_Antarctica.zip"
EXTRACTED_DIR = "Wellard_et_al_2020_Acoustic_files_of_Type_C_Killer_Whales_Ross_Sea_Antarctica_extracted"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--my-drive",
        type=Path,
        default=Path("/content/drive/MyDrive"),
        help="Mounted My Drive path.",
    )
    parser.add_argument(
        "--mode",
        choices=("copy", "move"),
        default="copy",
        help="Transfer mode used when --execute is set.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually create folders and transfer files. Without this, only prints a dry run.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing destination files or folders.",
    )
    return parser.parse_args()


def remove_existing(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def transfer(src: Path, dst: Path, *, mode: str, execute: bool, replace: bool) -> dict[str, str]:
    record = {"source": str(src), "destination": str(dst), "mode": mode}
    if not src.exists():
        record["status"] = "missing_source"
        return record
    if dst.exists():
        if not replace:
            record["status"] = "destination_exists"
            return record
        if execute:
            remove_existing(dst)
    if not execute:
        record["status"] = "dry_run"
        return record

    dst.parent.mkdir(parents=True, exist_ok=True)
    if mode == "move":
        shutil.move(str(src), str(dst))
    elif src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    record["status"] = "ok"
    return record


def main() -> int:
    args = parse_args()
    my_drive = args.my_drive
    if not my_drive.exists():
        raise FileNotFoundError(f"My Drive path is not mounted: {my_drive}")

    source_root = my_drive / "OrcaAcoustics_sources" / "wellard_type_c"
    folders = {
        "raw_zip": source_root / "raw_zip",
        "raw_unzipped": source_root / "raw_unzipped",
        "manifests": source_root / "manifests",
        "audit": source_root / "audit",
        "labels": source_root / "labels",
    }
    verified_evidence = my_drive / "OrcaAcoustics_verified_evidence"

    if args.execute:
        for folder in [*folders.values(), verified_evidence]:
            folder.mkdir(parents=True, exist_ok=True)

    cache_root = my_drive / "OrcaAcoustics_validation_evidence" / "_cache"
    wellard_root = cache_root / "wellard_mcmurdo_type_c"
    planned = [
        (my_drive / OUTER_ZIP, folders["raw_zip"] / OUTER_ZIP),
        (wellard_root / INNER_ZIP, folders["raw_zip"] / INNER_ZIP),
        (wellard_root / EXTRACTED_DIR, folders["raw_unzipped"] / EXTRACTED_DIR),
        (wellard_root / ".extracted_ok", folders["audit"] / ".extracted_ok"),
        (
            wellard_root / f".{INNER_ZIP}.7z_extracted",
            folders["audit"] / f".{INNER_ZIP}.7z_extracted",
        ),
        (
            cache_root / "wellard_segment_features_manifest.csv",
            folders["manifests"] / "wellard_segment_features_manifest.csv",
        ),
        (
            cache_root / "wellard_segment_features.npz",
            folders["manifests"] / "wellard_segment_features.npz",
        ),
        (cache_root / "wellard_segments", folders["manifests"] / "wellard_segments"),
    ]

    records = [
        transfer(src, dst, mode=args.mode, execute=args.execute, replace=args.replace)
        for src, dst in planned
    ]
    manifest = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "execute": args.execute,
        "mode": args.mode,
        "source_root": str(source_root),
        "verified_evidence": str(verified_evidence),
        "records": records,
    }
    print(json.dumps(manifest, indent=2))

    if args.execute:
        audit_path = folders["audit"] / "drive_organization_manifest.json"
        audit_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {audit_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

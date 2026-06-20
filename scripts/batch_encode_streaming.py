#!/usr/bin/env python3
"""Streaming batch encoder over the DCLDE 2026 killer-whale archive.

The DCLDE 2026 corpus is approximately 1.6 TB on GCS. This script processes
the full set of call-level annotations without ever holding more than one
source file on local disk: for each source file it downloads, extracts the
annotated call segments, encodes them with AVES2 to 768-d embeddings,
deletes the source file, and writes a periodic checkpoint.

Usage:
  python scripts/batch_encode_streaming.py --device cuda
  python scripts/batch_encode_streaming.py --device cuda --resume
  python scripts/batch_encode_streaming.py --device cuda --max-file-size-mb 1024

Output: data/embeddings/aves2_full_embeddings.npz with arrays
  - embeddings : (N, 768) float32
  - metadata   : (N,) object array of {soundfile, provider, dataset, ecotype,
                                       begin_sec, end_sec}
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import gcsfs
import librosa
import numpy as np
import pandas as pd
import torch
from tqdm import tqdm

GCS_BASE = "noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_DIR = DATA_DIR / "dclde" / "audio_cache"
OUTPUT_DIR = DATA_DIR / "embeddings"
PROGRESS_FILE = OUTPUT_DIR / "encoding_progress.json"
TARGET_SR = 16000
MIN_DURATION_S = 1.0

PROVIDER_TO_GCS = {
    "OrcaSound": "orcasound",
    "UAF_NGOS": "uaf",
    "SIO": "scripps",
    "JASCO_VFPA": "vfpa",
    "JASCO_VFPA_ONC": "vfpa",  # files actually live under vfpa/, not onc/ (verified 2026-05-27)
    "ONC": "onc",
    "SMRUConsulting": "smru",
    "SIMRES": "simres",
    "DFO_CRP": "dfo_crp",
    "DFO_WDLP": "dfo_wdlp",
}

DATASET_TO_SUBFOLDER = {
    "Bush_Pt": "bush_point", "bush_point": "bush_point",
    "OrcaSound_Lab": "orcasound_lab", "orcasound_lab": "orcasound_lab",
    "Port_Townsend": "port_townsend", "port_townsend": "port_townsend",
    "KB_67383303": "kb", "KB_5354": "kb", "KB_67424266": "kb",
    "RB_335826997": "rb", "RB_67424266": "rb",
    "Field_HTI": "field", "Field_SondTrap": "field",
    "HE_67424266": "he", "HE_67391498": "he",
    "MS_671879205": "ms", "MS_5360": "ms", "MS_6897": "ms",
    "Cpe_Elz": "ce", "Quin_Can": "qc",
    "BoundaryPass": "boundarypass",
    "StraitofGeorgia": "straitofgeorgia_globus-robertsbank",
    "HaroStraitSouth": "vfpa-harostrait-sb",
    "HaroStraitNorth": "vfpa-harostrait-nb",
    "BarkleyCanyon": "barkleycanyon",
    "LimeKiln": "lime-kiln",  # actual GCS folder uses hyphen, not concatenation (verified 2026-05-27)
    "Tekteksen": "eastpoint",  # SIMRES Tekteksen recordings live under eastpoint/ (verified 2026-05-27)
}


def resolve_gcs_path(provider: str, dataset: str, soundfile: str) -> str | None:
    gcs_provider = PROVIDER_TO_GCS.get(provider)
    if gcs_provider is None:
        return None
    subfolder = DATASET_TO_SUBFOLDER.get(dataset, dataset.lower().replace(" ", "_"))
    return f"{GCS_BASE}/{gcs_provider}/audio/{subfolder}/{soundfile}"


def extract_call_segment(audio_path: Path, begin_sec: float, end_sec: float) -> np.ndarray | None:
    """Extract a call segment from a local audio file, resample to 16 kHz."""
    try:
        duration = max(end_sec - begin_sec, MIN_DURATION_S)
        waveform, sr = librosa.load(
            str(audio_path), sr=None, offset=begin_sec, duration=duration, mono=True
        )
    except Exception:
        return None

    waveform_16k = librosa.resample(waveform, orig_sr=sr, target_sr=TARGET_SR)

    min_samples = int(MIN_DURATION_S * TARGET_SR)
    if len(waveform_16k) < min_samples:
        waveform_16k = np.pad(waveform_16k, (0, min_samples - len(waveform_16k)))

    return waveform_16k


def encode_waveform(model, waveform: np.ndarray, device: str) -> np.ndarray:
    """Encode a single waveform with AVES2, return mean-pooled 768-dim embedding."""
    audio_tensor = torch.from_numpy(waveform).unsqueeze(0).float().to(device)
    with torch.no_grad():
        features = model(audio_tensor)
    return features.cpu().numpy().mean(axis=1)[0]


def load_progress(progress_file: Path) -> dict:
    if progress_file.exists():
        with open(progress_file) as f:
            return json.load(f)
    return {"completed_files": [], "embeddings_count": 0}


def save_progress(progress_file: Path, progress: dict):
    with open(progress_file, "w") as f:
        json.dump(progress, f)


def main():
    parser = argparse.ArgumentParser(description="Streaming batch encode (full dataset)")
    parser.add_argument("--device", default="cpu", help="cpu or cuda")
    parser.add_argument("--resume", action="store_true", help="Resume from progress file")
    parser.add_argument("--max-files", type=int, default=None, help="Limit files (for testing)")
    parser.add_argument(
        "--max-file-size-mb", type=float, default=None,
        help=(
            "Skip files whose remote size exceeds this many megabytes. The DCLDE "
            "2026 archive contains a long tail of multi-GB continuous recordings "
            "for which download time dominates encoding time; a 1024 MB cap "
            "discards roughly 1.3% of annotations and reduces wall time by ~50x "
            "on a residential link."
        ),
    )
    args = parser.parse_args()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load annotations
    annotations_file = DATA_DIR / "dclde" / "Annotations.csv"
    if not annotations_file.exists():
        print("ERROR: Run scripts/download_annotations.py first")
        return 1

    df = pd.read_csv(annotations_file)
    calls = df[df["Ecotype"].notna() & (df["AnnotationLevel"] == "Call")].copy()

    # Group calls by file (so we download each file only once)
    file_groups = calls.groupby(["Provider", "Dataset", "Soundfile"])
    total_files = len(file_groups)
    total_calls = len(calls)

    print(f"=== Streaming Batch Encoder ===")
    print(f"  Total calls to encode: {total_calls:,}")
    print(f"  Total files to process: {total_files:,}")
    print(f"  Device: {args.device}")
    print(f"  Strategy: download → extract → encode → delete → next")
    print()

    # Load or init progress
    progress = load_progress(PROGRESS_FILE) if args.resume else {"completed_files": [], "embeddings_count": 0}

    # Load existing embeddings if resuming
    output_file = OUTPUT_DIR / "aves2_full_embeddings.npz"
    if args.resume and output_file.exists():
        existing = np.load(output_file, allow_pickle=True)
        all_embeddings = list(existing["embeddings"])
        all_metadata = list(existing["metadata"])
        print(f"  Resuming from {len(all_embeddings):,} existing embeddings")
    else:
        all_embeddings = []
        all_metadata = []

    # Connect to GCS
    fs = gcsfs.GCSFileSystem(token="anon")

    # Load encoder
    print(f"  Loading AVES2 encoder...")
    from avex import load_model
    model = load_model("esp_aves2_sl_beats_all", return_features_only=True, device=args.device)
    model.eval()
    print(f"  Encoder ready.\n")

    # Sort files: small files first (OrcaSound, UAF small), large files last
    size_priority = {
        "OrcaSound": 0, "UAF_NGOS": 1, "SMRUConsulting": 2,
        "SIMRES": 3, "ONC": 4, "SIO": 5, "JASCO_VFPA_ONC": 6, "JASCO_VFPA": 7,
    }

    file_list = []
    for (provider, dataset, soundfile), group in file_groups:
        file_list.append((provider, dataset, soundfile, len(group), size_priority.get(provider, 99)))
    file_list.sort(key=lambda x: (x[4], -x[3]))

    if args.max_files:
        file_list = file_list[:args.max_files]

    # Process files
    files_processed = 0
    files_failed = 0
    calls_encoded = len(all_embeddings)
    start_time = time.time()

    for provider, dataset, soundfile, n_calls, _ in tqdm(file_list, desc="Files"):
        file_key = f"{provider}/{dataset}/{soundfile}"

        # Skip if already done
        if file_key in progress["completed_files"]:
            continue

        # Resolve GCS path
        gcs_path = resolve_gcs_path(provider, dataset, soundfile)
        if gcs_path is None:
            files_failed += 1
            continue

        # Optionally skip files exceeding the size cap before downloading.
        # IMPORTANT: do NOT mark size-skipped files as completed in the
        # progress file. A subsequent uncapped --resume run must be free to
        # retry them; otherwise, all calls inside size-skipped files are lost
        # silently. (Bug discovered 2026-05-27: the prior --max-file-size-mb
        # 1024 run marked 52 such files as completed, dropping ~8,800 calls
        # mostly from UAF_NGOS / SAR / SIO transient recordings.)
        if args.max_file_size_mb is not None:
            try:
                remote_mb = fs.info(gcs_path)["size"] / (1024 * 1024)
            except Exception:
                remote_mb = None
            if remote_mb is not None and remote_mb > args.max_file_size_mb:
                files_failed += 1
                tqdm.write(
                    f"  SKIP {soundfile}: {remote_mb:.0f} MB exceeds cap "
                    f"({args.max_file_size_mb:.0f} MB) [not marked complete]"
                )
                continue

        # Download
        local_path = CACHE_DIR / soundfile
        if not local_path.exists():
            try:
                fs.get(gcs_path, str(local_path))
            except Exception as e:
                files_failed += 1
                tqdm.write(f"  SKIP {soundfile}: download failed ({type(e).__name__}: {e})")
                continue

        # Get all calls from this file
        file_calls = calls[
            (calls["Provider"] == provider) &
            (calls["Dataset"] == dataset) &
            (calls["Soundfile"] == soundfile)
        ]

        # Extract and encode each call
        file_success = 0
        for _, row in file_calls.iterrows():
            waveform = extract_call_segment(local_path, row["FileBeginSec"], row["FileEndSec"])
            if waveform is None:
                continue

            try:
                embedding = encode_waveform(model, waveform, args.device)
                all_embeddings.append(embedding)
                all_metadata.append({
                    "soundfile": soundfile,
                    "provider": provider,
                    "dataset": dataset,
                    "ecotype": row["Ecotype"],
                    "begin_sec": float(row["FileBeginSec"]),
                    "end_sec": float(row["FileEndSec"]),
                })
                file_success += 1
            except Exception:
                continue

        # Delete the file to free disk
        try:
            local_path.unlink()
        except Exception:
            pass

        # Update progress
        files_processed += 1
        calls_encoded += file_success
        progress["completed_files"].append(file_key)
        progress["embeddings_count"] = len(all_embeddings)

        # Save checkpoint every 10 files
        if files_processed % 10 == 0:
            np.savez_compressed(
                output_file,
                embeddings=np.array(all_embeddings, dtype=np.float32),
                metadata=np.array(all_metadata, dtype=object),
            )
            save_progress(PROGRESS_FILE, progress)
            elapsed = time.time() - start_time
            rate = calls_encoded / elapsed if elapsed > 0 else 0
            tqdm.write(
                f"  Checkpoint: {calls_encoded:,} calls encoded, "
                f"{files_processed}/{len(file_list)} files, "
                f"{rate:.1f} calls/s"
            )

    # Final save
    embeddings_array = np.array(all_embeddings, dtype=np.float32)
    np.savez_compressed(
        output_file,
        embeddings=embeddings_array,
        metadata=np.array(all_metadata, dtype=object),
    )
    save_progress(PROGRESS_FILE, progress)

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"STREAMING ENCODE COMPLETE")
    print(f"{'='*60}")
    print(f"  Calls encoded: {len(all_embeddings):,} / {total_calls:,}")
    print(f"  Files processed: {files_processed:,} / {total_files:,}")
    print(f"  Files failed: {files_failed:,}")
    print(f"  Embedding shape: {embeddings_array.shape}")
    print(f"  Time elapsed: {elapsed/60:.1f} min")
    print(f"  Output: {output_file}")

    # Ecotype distribution
    labels = np.array([m["ecotype"] for m in all_metadata])
    print(f"\n  Ecotype distribution:")
    for eco, count in pd.Series(labels).value_counts().items():
        print(f"    {eco}: {count:,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

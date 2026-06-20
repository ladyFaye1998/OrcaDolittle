#!/usr/bin/env python3
"""Batch-encode all call-level DCLDE clips through AVES2 (or NatureLM-audio).

This is the foundational pipeline: it produces the embedding matrix that
ALL four heads (H1-H4) consume.

Usage:
  # AVES2 on CPU (slow but works anywhere):
  python3 scripts/batch_encode.py --encoder aves2 --device cpu

  # AVES2 on GPU (fast, for the 4090):
  python3 scripts/batch_encode.py --encoder aves2 --device cuda

  # NatureLM-audio on GPU (requires HF_TOKEN + Llama access):
  python3 scripts/batch_encode.py --encoder naturelm --device cuda

Output: data/embeddings/{encoder}_embeddings.npz
  - embeddings: (N, 768) float32 matrix
  - labels: (N,) ecotype labels
  - metadata: per-clip provenance (soundfile, provider, begin/end sec)
"""

import argparse
import json
import sys
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
TARGET_SR = 16000
MIN_DURATION_S = 1.0  # BEATs 16x16 patch minimum

PROVIDER_TO_GCS = {
    "OrcaSound": "orcasound",
    "UAF_NGOS": "uaf",
    "SIO": "scripps",
    "JASCO_VFPA": "vfpa",
    "JASCO_VFPA_ONC": "onc",
    "ONC": "onc",
    "SMRUConsulting": "smru",
    "SIMRES": "simres",
    "DFO_CRP": "dfo_crp",
    "DFO_WDLP": "dfo_wdlp",
}

DATASET_TO_SUBFOLDER = {
    # OrcaSound
    "Bush_Pt": "bush_point",
    "OrcaSound_Lab": "orcasound_lab",
    "Port_Townsend": "port_townsend",
    # UAF
    "KB_67383303": "kb",
    "KB_5354": "kb",
    "RB_335826997": "rb",
    "RB_67424266": "rb",
    "Field_HTI": "field",
    "HE_67424266": "he",
    "HE_67391498": "he",
    "MS_671879205": "ms",
    "MS_5360": "ms",
    "MS_6897": "ms",
    # Scripps (SIO)
    "Cpe_Elz": "ce",
    "Quin_Can": "qc",
    # JASCO VFPA
    "BoundaryPass": "boundarypass",
    "StraitofGeorgia": "straitofgeorgia_globus-robertsbank",
    "HaroStraitSouth": "vfpa-harostrait-sb",
    "HaroStraitNorth": "vfpa-harostrait-nb",
    # ONC
    "BarkleyCanyon": "barkleycanyon",
}


def resolve_gcs_path(row: pd.Series) -> str | None:
    """Map an annotation row to its GCS audio path."""
    provider = row["Provider"]
    dataset = row["Dataset"]
    soundfile = row["Soundfile"]

    gcs_provider = PROVIDER_TO_GCS.get(provider)
    if gcs_provider is None:
        return None

    subfolder = DATASET_TO_SUBFOLDER.get(dataset)
    if subfolder is None:
        subfolder = dataset.lower().replace(" ", "_")

    return f"{GCS_BASE}/{gcs_provider}/audio/{subfolder}/{soundfile}"


def load_call_segment(
    fs: gcsfs.GCSFileSystem,
    gcs_path: str,
    begin_sec: float,
    end_sec: float,
) -> np.ndarray | None:
    """Download (cached) and extract a call segment, resampled to 16 kHz."""
    filename = Path(gcs_path).name
    local_file = CACHE_DIR / filename

    if not local_file.exists():
        try:
            fs.get(gcs_path, str(local_file))
        except Exception:
            return None

    try:
        duration = end_sec - begin_sec
        waveform, sr = librosa.load(
            str(local_file), sr=None, offset=begin_sec, duration=duration, mono=True
        )
    except Exception:
        return None

    waveform_16k = librosa.resample(waveform, orig_sr=sr, target_sr=TARGET_SR)

    min_samples = int(MIN_DURATION_S * TARGET_SR)
    if len(waveform_16k) < min_samples:
        waveform_16k = np.pad(waveform_16k, (0, min_samples - len(waveform_16k)))

    return waveform_16k


def get_encoder(encoder_name: str, device: str):
    """Load the specified encoder model."""
    if encoder_name == "aves2":
        from avex import load_model

        model = load_model("esp_aves2_sl_beats_all", return_features_only=True, device=device)
        model.eval()
        return model
    elif encoder_name == "naturelm":
        from NatureLM.models import NatureLM

        model = NatureLM.from_pretrained("EarthSpeciesProject/NatureLM-audio")
        model = model.eval().to(device)
        return model
    else:
        raise ValueError(f"Unknown encoder: {encoder_name}")


def encode_waveform(model, waveform: np.ndarray, encoder_name: str, device: str) -> np.ndarray:
    """Encode a single waveform, return mean-pooled embedding."""
    audio_tensor = torch.from_numpy(waveform).unsqueeze(0).float().to(device)

    with torch.no_grad():
        if encoder_name == "aves2":
            features = model(audio_tensor)  # (1, T, 768)
            pooled = features.cpu().numpy().mean(axis=1)  # (1, 768)
        elif encoder_name == "naturelm":
            features = model.encode_audio(audio_tensor)
            pooled = features.cpu().numpy().mean(axis=1)
        else:
            raise ValueError(f"Unknown encoder: {encoder_name}")

    return pooled[0]


def main():
    parser = argparse.ArgumentParser(description="Batch-encode DCLDE calls")
    parser.add_argument("--encoder", choices=["aves2", "naturelm"], default="aves2")
    parser.add_argument("--device", default="cpu", help="cpu or cuda")
    parser.add_argument("--max-clips", type=int, default=None, help="Limit clips (for testing)")
    parser.add_argument("--max-file-size-mb", type=float, default=50.0,
                        help="Skip audio files larger than this (MB)")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"{args.encoder}_embeddings.npz"
    print(f"=== Batch Encode Pipeline ===")
    print(f"  Encoder: {args.encoder}")
    print(f"  Device: {args.device}")
    print(f"  Output: {output_file}")
    print()

    # Load annotations
    annotations_file = DATA_DIR / "dclde" / "Annotations.csv"
    if not annotations_file.exists():
        print("ERROR: Run scripts/download_annotations.py first")
        return 1

    df = pd.read_csv(annotations_file)
    calls = df[df["Ecotype"].notna() & (df["AnnotationLevel"] == "Call")].copy()
    print(f"  Call-level annotations with ecotype: {len(calls):,}")

    if args.max_clips:
        calls = calls.sample(n=min(args.max_clips, len(calls)), random_state=args.seed)
        print(f"  Sampled down to: {len(calls):,}")

    # Connect to GCS
    fs = gcsfs.GCSFileSystem(token="anon")

    # Load encoder
    print(f"\n  Loading {args.encoder} encoder...")
    model = get_encoder(args.encoder, args.device)
    print("  Encoder ready.\n")

    # Process clips
    embeddings = []
    metadata = []
    failed = 0

    for idx, row in tqdm(calls.iterrows(), total=len(calls), desc="Encoding"):
        gcs_path = resolve_gcs_path(row)
        if gcs_path is None:
            failed += 1
            continue

        # Check file size before downloading
        filename = Path(gcs_path).name
        local_file = CACHE_DIR / filename
        if not local_file.exists():
            try:
                info = fs.info(gcs_path)
                size_mb = info["size"] / 1024 / 1024
                if size_mb > args.max_file_size_mb:
                    failed += 1
                    continue
            except Exception:
                failed += 1
                continue

        waveform = load_call_segment(fs, gcs_path, row["FileBeginSec"], row["FileEndSec"])
        if waveform is None:
            failed += 1
            continue

        try:
            embedding = encode_waveform(model, waveform, args.encoder, args.device)
            embeddings.append(embedding)
            metadata.append({
                "soundfile": row["Soundfile"],
                "provider": row["Provider"],
                "dataset": row["Dataset"],
                "ecotype": row["Ecotype"],
                "begin_sec": row["FileBeginSec"],
                "end_sec": row["FileEndSec"],
                "class_species": row["ClassSpecies"],
            })
        except Exception as e:
            failed += 1
            continue

    embeddings_array = np.array(embeddings, dtype=np.float32)
    labels_array = np.array([m["ecotype"] for m in metadata])

    print(f"\n{'='*50}")
    print(f"BATCH ENCODING COMPLETE")
    print(f"{'='*50}")
    print(f"  Successfully encoded: {len(embeddings):,}")
    print(f"  Failed/skipped: {failed:,}")
    print(f"  Embedding shape: {embeddings_array.shape}")
    print(f"  Ecotype distribution:")
    for eco, count in pd.Series(labels_array).value_counts().items():
        print(f"    {eco}: {count:,}")

    # Save
    np.savez_compressed(
        output_file,
        embeddings=embeddings_array,
        labels=labels_array,
    )

    # Save metadata separately as JSON for provenance
    meta_file = OUTPUT_DIR / f"{args.encoder}_metadata.json"
    with open(meta_file, "w") as f:
        json.dump(metadata, f)

    print(f"\n  Saved embeddings to: {output_file}")
    print(f"  Saved metadata to: {meta_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

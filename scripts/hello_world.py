#!/usr/bin/env python3
"""Hello-world: extract AVES2 embeddings from a killer whale audio clip.

This is the Stage 1 smoke test. If this runs, the core pipeline entry points are reachable:
  audio clip -> frozen encoder -> embedding vector -> downstream heads

Uses AVES2 (BEATs backbone) via the avex library. Runs on CPU.
AVES2 expects 16 kHz mono audio and produces (batch, time_steps, 768) embeddings.

Run the download scripts first:
  python scripts/download_annotations.py
  python scripts/download_sample_audio.py
"""

import sys
from pathlib import Path

import numpy as np

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "dclde" / "sample_audio"
ANNOTATIONS_FILE = Path(__file__).resolve().parent.parent / "data" / "dclde" / "Annotations.csv"


def load_and_resample(audio_path: Path, target_sr: int = 16000):
    """Load audio and resample to target sample rate."""
    import librosa

    waveform, sr = librosa.load(str(audio_path), sr=target_sr, mono=True)
    return waveform, sr


def extract_embedding(waveform: np.ndarray, sr: int):
    """Extract AVES2 embedding from audio waveform."""
    import torch
    from avex import load_model

    model = load_model("esp_aves2_sl_beats_all", return_features_only=True, device="cpu")
    model.eval()

    audio_tensor = torch.from_numpy(waveform).unsqueeze(0).float()

    with torch.no_grad():
        embedding = model(audio_tensor)

    return embedding.numpy()


def main():
    # Check prerequisites
    wav_files = sorted(SAMPLE_DIR.glob("*.wav")) if SAMPLE_DIR.exists() else []
    if not wav_files:
        print("ERROR: No sample audio found.")
        print("Run first:  python scripts/download_sample_audio.py")
        return 1

    audio_path = wav_files[0]
    print(f"=== OrcaDolittle Stage 1: Hello World ===\n")
    print(f"Audio file: {audio_path.name}")

    # Load audio
    print("\n[1/3] Loading and resampling audio to 16 kHz...")
    waveform, sr = load_and_resample(audio_path)
    print(f"  Waveform shape: {waveform.shape}")
    print(f"  Sample rate: {sr} Hz")
    print(f"  Duration: {len(waveform) / sr:.1f} s")

    # Extract embedding
    print("\n[2/3] Extracting AVES2 embedding (BEATs backbone, CPU)...")
    print("  (First run downloads model weights from HuggingFace, ~350 MB)")
    embedding = extract_embedding(waveform, sr)
    print(f"  Embedding shape: {embedding.shape}")
    print(f"  → (batch={embedding.shape[0]}, time_steps={embedding.shape[1]}, features={embedding.shape[2]})")

    # Mean-pool across time to get a single vector per clip
    pooled = embedding.mean(axis=1)
    print(f"\n  Mean-pooled embedding: {pooled.shape} → {pooled.shape[1]}-dim vector per clip")
    print(f"  First 10 values: {pooled[0, :10]}")
    print(f"  L2 norm: {np.linalg.norm(pooled[0]):.4f}")

    # Cross-reference with annotations
    print("\n[3/3] Cross-referencing with annotations...")
    if ANNOTATIONS_FILE.exists():
        import pandas as pd

        df = pd.read_csv(ANNOTATIONS_FILE)
        print(f"  Total annotations: {len(df):,}")
        print(f"  Columns: {list(df.columns)}")
        if "Ecotype" in df.columns:
            print(f"  Ecotype distribution:")
            for eco, count in df["Ecotype"].value_counts().items():
                print(f"    {eco}: {count:,}")
    else:
        print("  (Run scripts/download_annotations.py for annotation stats)")

    print("\n=== SUCCESS ===")
    print("The pipeline works: audio → AVES2 encoder → 768-dim embedding.")
    print("Next: encode all 225K calls, then run the four heads (H1-H4).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

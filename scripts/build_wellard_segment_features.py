#!/usr/bin/env python3
"""Build compact acoustic feature vectors for Wellard H5-H7 segment rows.

The script expects the Wellard WAV files to be extracted from the Dryad archive
into a directory. Raw audio is never written by this script; only compact
per-segment summary features and row metadata are saved.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import librosa
import numpy as np
import pandas as pd
import soundfile as sf
from tqdm import tqdm

TARGET_SR = 16_000
MIN_SAMPLES = TARGET_SR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-dir", required=True, help="Directory containing extracted Wellard WAV files")
    parser.add_argument("--segment-manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--target-sr", type=int, default=TARGET_SR)
    parser.add_argument("--max-segments", type=int, default=None, help="Optional development cap")
    return parser.parse_args()


def find_audio_files(audio_dir: Path) -> dict[str, Path]:
    files = {}
    for path in audio_dir.rglob("*.wav"):
        files[path.name] = path
    return files


def read_segment(path: Path, start_s: float, end_s: float, target_sr: int) -> np.ndarray:
    with sf.SoundFile(str(path)) as snd:
        native_sr = int(snd.samplerate)
        start_frame = max(0, int(round(start_s * native_sr)))
        stop_frame = max(start_frame + 1, int(round(end_s * native_sr)))
        snd.seek(min(start_frame, len(snd)))
        audio = snd.read(max(0, min(stop_frame, len(snd)) - start_frame), dtype="float32", always_2d=True)
    if audio.size == 0:
        raise ValueError("empty audio segment")
    mono = audio.mean(axis=1)
    if native_sr != target_sr:
        mono = librosa.resample(mono, orig_sr=native_sr, target_sr=target_sr)
    if len(mono) < MIN_SAMPLES:
        mono = np.pad(mono, (0, MIN_SAMPLES - len(mono)))
    return mono.astype(np.float32, copy=False)


def summarize_waveform(y: np.ndarray, sr: int) -> np.ndarray:
    """Return a fixed-dimensional acoustic summary vector."""
    y = np.asarray(y, dtype=np.float32)
    if not np.any(np.isfinite(y)):
        raise ValueError("non-finite waveform")
    y = np.nan_to_num(y)

    hop = 512
    n_fft = 1024
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20, n_fft=n_fft, hop_length=hop)
    mel = librosa.feature.melspectrogram(
        y=y, sr=sr, n_fft=n_fft, hop_length=hop, n_mels=32, power=2.0
    )
    logmel = librosa.power_to_db(mel + 1e-12, ref=np.max)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=n_fft, hop_length=hop)
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, n_fft=n_fft, hop_length=hop)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, n_fft=n_fft, hop_length=hop)
    flatness = librosa.feature.spectral_flatness(y=y, n_fft=n_fft, hop_length=hop)
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=n_fft, hop_length=hop)
    rms = librosa.feature.rms(y=y, frame_length=n_fft, hop_length=hop)

    parts = [
        mfcc.mean(axis=1), mfcc.std(axis=1),
        logmel.mean(axis=1), logmel.std(axis=1),
        centroid.mean(axis=1), centroid.std(axis=1),
        bandwidth.mean(axis=1), bandwidth.std(axis=1),
        rolloff.mean(axis=1), rolloff.std(axis=1),
        flatness.mean(axis=1), flatness.std(axis=1),
        zcr.mean(axis=1), zcr.std(axis=1),
        rms.mean(axis=1), rms.std(axis=1),
        np.array([float(np.mean(y)), float(np.std(y)), float(np.max(np.abs(y)))], dtype=np.float32),
    ]
    return np.concatenate([np.asarray(p, dtype=np.float32).ravel() for p in parts]).astype(np.float32)


def main() -> int:
    args = parse_args()
    audio_dir = Path(args.audio_dir)
    manifest_path = Path(args.segment_manifest)
    output_path = Path(args.output)

    if not audio_dir.exists():
        print(f"ERROR: audio directory not found: {audio_dir}", file=sys.stderr)
        return 2
    if not manifest_path.exists():
        print(f"ERROR: segment manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    manifest = pd.read_csv(manifest_path)
    if args.max_segments:
        manifest = manifest.head(args.max_segments).copy()
    required = {"segment_id", "source_file", "start_time_s", "end_time_s"}
    missing = required - set(manifest.columns)
    if missing:
        print(f"ERROR: manifest missing columns: {sorted(missing)}", file=sys.stderr)
        return 2

    audio_files = find_audio_files(audio_dir)
    missing_files = sorted(set(manifest["source_file"]) - set(audio_files))
    if missing_files:
        print(f"ERROR: missing extracted WAV files: {missing_files[:10]}", file=sys.stderr)
        return 2

    features = []
    metadata = []
    failures = []
    for _, row in tqdm(manifest.iterrows(), total=len(manifest), desc="Wellard segments"):
        try:
            path = audio_files[str(row["source_file"])]
            y = read_segment(path, float(row["start_time_s"]), float(row["end_time_s"]), args.target_sr)
            features.append(summarize_waveform(y, args.target_sr))
            metadata.append(row.to_dict())
        except Exception as exc:
            failures.append({
                "segment_id": row.get("segment_id"),
                "source_file": row.get("source_file"),
                "start_time_s": row.get("start_time_s"),
                "end_time_s": row.get("end_time_s"),
                "error_type": type(exc).__name__,
                "error": str(exc),
            })

    if not features:
        print("ERROR: no segment features were generated.", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    X = np.vstack(features).astype(np.float32)
    np.savez_compressed(output_path, embeddings=X, metadata=np.array(metadata, dtype=object))

    summary = {
        "audio_dir": str(audio_dir),
        "segment_manifest": str(manifest_path),
        "output": str(output_path),
        "segments_requested": int(len(manifest)),
        "segments_encoded": int(len(features)),
        "failures": int(len(failures)),
        "feature_shape": list(X.shape),
    }
    summary_path = output_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps({**summary, "failure_examples": failures[:20]}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if len(features) == len(manifest) else 1


if __name__ == "__main__":
    raise SystemExit(main())

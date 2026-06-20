#!/usr/bin/env python3
"""Test whether AVES2 embeddings separate killer whale ecotypes.

Downloads a balanced sample of clips from 3 ecotypes (SRKW, TKW, OKW),
extracts the annotated call segments, encodes them with AVES2, and
visualizes with UMAP. If ecotypes cluster, the project thesis is viable.
"""

import sys
from pathlib import Path

import gcsfs
import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import torch
from tqdm import tqdm

GCS_BASE = "noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "dclde"
SAMPLE_DIR = DATA_DIR / "ecotype_test"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "embeddings"

N_CLIPS_PER_ECOTYPE = 20
TARGET_SR = 16000


def get_ecotype_samples(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Get balanced samples of call-level annotations per ecotype."""
    samples = {}

    # SRKW from OrcaSound
    srkw = df[
        (df["Provider"] == "OrcaSound")
        & (df["Ecotype"] == "SRKW")
        & (df["AnnotationLevel"] == "Call")
    ]
    samples["SRKW"] = srkw.sample(n=min(N_CLIPS_PER_ECOTYPE, len(srkw)), random_state=42)

    # TKW from UAF RB
    tkw = df[
        (df["Provider"] == "UAF_NGOS")
        & (df["Ecotype"] == "TKW")
        & (df["AnnotationLevel"] == "Call")
    ]
    samples["TKW"] = tkw.sample(n=min(N_CLIPS_PER_ECOTYPE, len(tkw)), random_state=42)

    # OKW from UAF KB
    okw = df[
        (df["Provider"] == "UAF_NGOS")
        & (df["Ecotype"] == "OKW")
        & (df["AnnotationLevel"] == "Call")
    ]
    samples["OKW"] = okw.sample(n=min(N_CLIPS_PER_ECOTYPE, len(okw)), random_state=42)

    return samples


def soundfile_to_gcs_path(soundfile: str, provider: str, dataset: str) -> str:
    """Map a soundfile name to its GCS path."""
    provider_map = {
        "OrcaSound": "orcasound",
        "UAF_NGOS": "uaf",
    }
    gcs_provider = provider_map[provider]

    if provider == "OrcaSound":
        location_map = {
            "Bush_Pt": "bush_point",
            "OrcaSound_Lab": "orcasound_lab",
            "Port_Townsend": "port_townsend",
        }
        location = location_map.get(dataset, dataset.lower())
        return f"{GCS_BASE}/{gcs_provider}/audio/{location}/{soundfile}"
    elif provider == "UAF_NGOS":
        dataset_map = {
            "KB_67383303": "kb",
            "KB_5354": "kb",
            "RB_335826997": "rb",
            "RB_67424266": "rb",
            "Field_HTI": "field",
        }
        subfolder = dataset_map.get(dataset, dataset.lower())
        return f"{GCS_BASE}/{gcs_provider}/audio/{subfolder}/{soundfile}"

    return None


def download_and_extract_call(
    fs: gcsfs.GCSFileSystem,
    gcs_path: str,
    begin_sec: float,
    end_sec: float,
    local_cache: Path,
) -> np.ndarray | None:
    """Download audio file (cached) and extract the call segment."""
    filename = Path(gcs_path).name
    local_file = local_cache / filename

    if not local_file.exists():
        try:
            fs.get(gcs_path, str(local_file))
        except Exception as e:
            print(f"    Failed to download {filename}: {e}")
            return None

    try:
        waveform, sr = librosa.load(
            str(local_file), sr=None, offset=begin_sec, duration=end_sec - begin_sec, mono=True
        )
    except Exception as e:
        print(f"    Failed to read {filename}: {e}")
        return None

    if len(waveform.shape) > 1:
        waveform = waveform[:, 0]

    waveform_16k = librosa.resample(waveform.astype(np.float32), orig_sr=sr if isinstance(sr, int) else 48000, target_sr=TARGET_SR)

    # BEATs needs at least ~1s of audio for its 16x16 patch embedding
    min_samples = TARGET_SR  # 1 second minimum
    if len(waveform_16k) < min_samples:
        waveform_16k = np.pad(waveform_16k, (0, min_samples - len(waveform_16k)))

    return waveform_16k


def encode_batch(waveforms: list[np.ndarray]) -> np.ndarray:
    """Encode a batch of waveforms with AVES2, return mean-pooled embeddings."""
    from avex import load_model

    model = load_model("esp_aves2_sl_beats_all", return_features_only=True, device="cpu")
    model.eval()

    embeddings = []
    for waveform in tqdm(waveforms, desc="  Encoding"):
        audio_tensor = torch.from_numpy(waveform).unsqueeze(0).float()
        with torch.no_grad():
            emb = model(audio_tensor)
        pooled = emb.numpy().mean(axis=1)  # (1, 768)
        embeddings.append(pooled[0])

    return np.array(embeddings)


def plot_umap(embeddings: np.ndarray, labels: list[str], output_path: Path):
    """Run UMAP and plot embeddings colored by ecotype."""
    from sklearn.preprocessing import LabelEncoder
    import umap
    import matplotlib.pyplot as plt

    le = LabelEncoder()
    label_nums = le.fit_transform(labels)

    reducer = umap.UMAP(n_neighbors=10, min_dist=0.1, n_components=2, random_state=42)
    embedding_2d = reducer.fit_transform(embeddings)

    colors = {"SRKW": "#2196F3", "TKW": "#F44336", "OKW": "#4CAF50"}

    plt.figure(figsize=(10, 8))
    for eco in sorted(set(labels)):
        mask = [l == eco for l in labels]
        pts = embedding_2d[mask]
        plt.scatter(pts[:, 0], pts[:, 1], c=colors.get(eco, "gray"), label=eco, s=100, alpha=0.7, edgecolors="white", linewidth=0.5)

    plt.legend(fontsize=14, markerscale=1.5)
    plt.title("AVES2 Embeddings of Killer Whale Calls\n(UMAP projection, colored by ecotype)", fontsize=14)
    plt.xlabel("UMAP 1", fontsize=12)
    plt.ylabel("UMAP 2", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nPlot saved to: {output_path}")


def compute_separation_stats(embeddings: np.ndarray, labels: list[str]):
    """Compute basic separation statistics."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import LabelEncoder

    le = LabelEncoder()
    y = le.fit_transform(labels)

    clf = LogisticRegression(max_iter=1000, random_state=42)
    scores = cross_val_score(clf, embeddings, y, cv=5, scoring="accuracy")

    chance = 1.0 / len(set(labels))
    print(f"\n{'='*50}")
    print(f"ECOTYPE CLASSIFICATION (linear probe, 5-fold CV)")
    print(f"{'='*50}")
    print(f"  Accuracy: {scores.mean():.1%} ± {scores.std():.1%}")
    print(f"  Chance:   {chance:.1%}")
    print(f"  Above chance by: {(scores.mean() - chance) / chance:.0%}")
    print(f"{'='*50}")

    if scores.mean() > chance + 0.10:
        print("\n  ✓ EMBEDDINGS SEPARATE ECOTYPES. The thesis is viable.")
        print("    H1 (linear probes) and H2 (clustering) both look promising.")
    elif scores.mean() > chance + 0.03:
        print("\n  ~ WEAK SEPARATION. May need NatureLM-audio or more data.")
    else:
        print("\n  ✗ NO SEPARATION. Consider fine-tuning (Risk C fallback).")


def main():
    print("=== Ecotype Separation Test ===\n")
    print("Question: Do AVES2 embeddings cluster by killer whale ecotype?")
    print("If yes → the project thesis is viable. If no → pivot needed.\n")

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load annotations
    annotations_file = DATA_DIR / "Annotations.csv"
    if not annotations_file.exists():
        print("ERROR: Run scripts/download_annotations.py first")
        return 1

    df = pd.read_csv(annotations_file)
    samples = get_ecotype_samples(df)

    for eco, s in samples.items():
        print(f"  {eco}: {len(s)} call annotations selected")

    # Download and extract calls
    print("\nDownloading audio and extracting call segments...")
    fs = gcsfs.GCSFileSystem(token="anon")

    all_waveforms = []
    all_labels = []

    for eco, sample_df in samples.items():
        print(f"\n  [{eco}]")
        for _, row in sample_df.iterrows():
            gcs_path = soundfile_to_gcs_path(row["Soundfile"], row["Provider"], row["Dataset"])
            if gcs_path is None:
                continue

            waveform = download_and_extract_call(
                fs, gcs_path, row["FileBeginSec"], row["FileEndSec"], SAMPLE_DIR
            )
            if waveform is not None:
                all_waveforms.append(waveform)
                all_labels.append(eco)

    print(f"\nSuccessfully extracted {len(all_waveforms)} call segments")
    for eco in sorted(set(all_labels)):
        count = all_labels.count(eco)
        print(f"  {eco}: {count}")

    if len(all_waveforms) < 10:
        print("ERROR: Too few clips extracted. Check GCS paths.")
        return 1

    # Encode with AVES2
    print("\nEncoding with AVES2 (this takes a few minutes on CPU)...")
    embeddings = encode_batch(all_waveforms)
    print(f"  Embedding matrix: {embeddings.shape}")

    # Save embeddings
    np.savez(
        OUTPUT_DIR / "ecotype_test_embeddings.npz",
        embeddings=embeddings,
        labels=np.array(all_labels),
    )

    # Compute stats
    compute_separation_stats(embeddings, all_labels)

    # Plot
    try:
        plot_umap(embeddings, all_labels, OUTPUT_DIR / "ecotype_umap.png")
    except ImportError as e:
        print(f"\n(Install umap-learn for visualization: pip install umap-learn)")
        print(f"  Missing: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

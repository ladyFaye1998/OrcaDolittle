#!/usr/bin/env python3
"""Inject `labels` array (per-call ecotype) into the streaming-encoder output.

The streaming encoder (`batch_encode_streaming.py`) saves `embeddings` and
`metadata` (list of dicts) but not a flat `labels` array. The H1/H2/H4 scripts
load `data["labels"]` directly, so this small adapter writes a sibling npz
with both `embeddings` and `labels` extracted from metadata's `ecotype` field.

Usage:
  python scripts/add_labels_from_metadata.py \
      --input data/embeddings/aves2_full_embeddings.npz \
      --output data/embeddings/aves2_full_labeled.npz
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject labels from metadata")
    parser.add_argument("--input", required=True, help="npz with `embeddings` + `metadata`")
    parser.add_argument("--output", required=True, help="npz with `embeddings` + `labels`")
    parser.add_argument(
        "--field", default="ecotype",
        help="metadata field to use as label (default: ecotype)",
    )
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        print(f"ERROR: {in_path} not found")
        return 1

    data = np.load(in_path, allow_pickle=True)
    embeddings = data["embeddings"]
    metadata = data["metadata"]

    if len(embeddings) != len(metadata):
        print(f"ERROR: mismatch — {len(embeddings)} embeddings vs {len(metadata)} metadata")
        return 1

    labels = np.array([str(m[args.field]) for m in metadata])
    print(f"Loaded: {len(embeddings):,} embeddings, dim {embeddings.shape[1]}")
    print(f"Label field: {args.field}")
    print(f"Label distribution:")
    for label, count in Counter(labels).most_common():
        print(f"  {label}: {count:,}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_path,
        embeddings=embeddings.astype(np.float32),
        labels=labels,
        metadata=metadata,
    )
    print(f"\nWrote: {out_path}")
    print(f"  Keys: embeddings (float32), labels (str), metadata (object)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

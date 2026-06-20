#!/usr/bin/env python3
"""Schema-validate and freeze the labeled embedding corpus.

Runs hard data-contract checks before any headline analysis, then records a
SHA-256 freeze manifest so every downstream result is tied to an exact artifact.
This is the reproducibility gate referenced in `docs/methodology.md`.

Checks (any failure exits non-zero):
  - required npz keys present (embeddings, labels, metadata)
  - embeddings are 2-D float, finite, with the expected dimension
  - labels and metadata are row-aligned with embeddings
  - every label is in the allowed ecotype set
  - required metadata fields are present on every row
  - each ecotype is represented (warns, does not fail, on single-provider classes)

Usage:
  python scripts/freeze_corpus.py \
      --embeddings data/embeddings/aves2_full_labeled.npz \
      --output reports/corpus_freeze.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_DIM = 768
ALLOWED_ECOTYPES = {"SRKW", "TKW", "OKW", "SAR"}
REQUIRED_METADATA_FIELDS = {"soundfile", "provider", "ecotype", "begin_sec", "end_sec"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embeddings", default="data/embeddings/aves2_full_labeled.npz")
    parser.add_argument("--output", default="reports/corpus_freeze.json")
    parser.add_argument("--expected-dim", type=int, default=EXPECTED_DIM)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    emb_path = (REPO_ROOT / args.embeddings) if not Path(args.embeddings).is_absolute() else Path(args.embeddings)
    if not emb_path.exists():
        print(f"ERROR: embeddings not found: {emb_path}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    data = np.load(emb_path, allow_pickle=True)
    keys = set(data.files)
    for required in ("embeddings", "labels", "metadata"):
        if required not in keys:
            errors.append(f"missing npz key: {required}")
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    embeddings = data["embeddings"]
    labels = [str(v) for v in data["labels"]]
    metadata = list(data["metadata"])

    # Embedding matrix checks.
    if embeddings.ndim != 2:
        errors.append(f"embeddings not 2-D (got shape {embeddings.shape})")
    n, dim = embeddings.shape[0], embeddings.shape[1]
    if dim != args.expected_dim:
        errors.append(f"embedding dim {dim} != expected {args.expected_dim}")
    if not np.isfinite(np.asarray(embeddings, dtype=np.float64)).all():
        errors.append("embeddings contain non-finite values (nan/inf)")

    # Row alignment.
    if len(labels) != n:
        errors.append(f"labels length {len(labels)} != n_embeddings {n}")
    if len(metadata) != n:
        errors.append(f"metadata length {len(metadata)} != n_embeddings {n}")

    # Label domain.
    bad_labels = sorted({l for l in labels} - ALLOWED_ECOTYPES)
    if bad_labels:
        errors.append(f"labels outside allowed set {sorted(ALLOWED_ECOTYPES)}: {bad_labels}")

    # Required metadata fields present on every row.
    missing_field_rows: Counter = Counter()
    for m in metadata:
        if not isinstance(m, dict):
            errors.append("metadata row is not a dict")
            break
        for field in REQUIRED_METADATA_FIELDS:
            if field not in m:
                missing_field_rows[field] += 1
    for field, count in missing_field_rows.items():
        errors.append(f"metadata field '{field}' missing on {count} rows")

    # Provider breadth per ecotype (warn-only: single-provider classes cannot be
    # decoded cross-site and must be reported as site-confounded).
    eco_provider: dict[str, set] = {}
    if not missing_field_rows and len(metadata) == n:
        for lab, m in zip(labels, metadata):
            eco_provider.setdefault(lab, set()).add(str(m.get("provider", "NA")))
        for lab, provs in eco_provider.items():
            if len(provs) <= 1:
                warnings.append(
                    f"ecotype '{lab}' appears at only {len(provs)} provider(s): "
                    f"pooled decodability is site-confounded for this class"
                )

    passed = not errors
    freeze = {
        "embeddings_path": str(emb_path.relative_to(REPO_ROOT)) if emb_path.is_relative_to(REPO_ROOT) else str(emb_path),
        "passed": passed,
        "n_rows": int(n),
        "embedding_dim": int(dim),
        "label_distribution": {k: int(v) for k, v in Counter(labels).most_common()},
        "ecotype_provider_breadth": {k: len(v) for k, v in eco_provider.items()},
        "sha256": sha256_file(emb_path),
        "errors": errors,
        "warnings": warnings,
    }

    out_path = (REPO_ROOT / args.output) if not Path(args.output).is_absolute() else Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(freeze, indent=2), encoding="utf-8")

    status = "PASS" if passed else "FAIL"
    print(f"[{status}] corpus freeze: {n:,} rows x {dim} dims")
    print(f"  label distribution: {freeze['label_distribution']}")
    print(f"  sha256: {freeze['sha256']}")
    for w in warnings:
        print(f"  WARN: {w}")
    for e in errors:
        print(f"  ERROR: {e}")
    print(f"  wrote: {out_path}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

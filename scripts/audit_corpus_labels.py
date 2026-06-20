#!/usr/bin/env python3
"""Phase 0 label audit for the orca embedding corpus.

Determines, from a labeled embedding artifact, exactly which biological and
provenance labels are available, and whether the corpus can support a
call-type repertoire analysis (Leg 1) or must fall back to a population/site
framing. Also reports per-source-file sequence feasibility for the sequence
head (Leg 3) and the ecotype-vs-provider cross-tabulation that motivates the
provider-aware controls (Leg 2).

The audit is read-only and writes a single JSON summary to `reports/`.

Usage:
  python scripts/audit_corpus_labels.py \
      --embeddings data/embeddings/aves2_full_labeled.npz \
      --output reports/label_audit.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent

# Metadata keys that, if present and well-populated, would indicate a usable
# discrete call-type / vocabulary label (the strong Leg 1 case).
CALLTYPE_KEY_HINTS = (
    "call_type",
    "calltype",
    "call",
    "vocalization",
    "vocalisation",
    "category",
    "label_call",
    "stereotyped_call",
    "sound_type",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embeddings", default="data/embeddings/aves2_full_labeled.npz")
    parser.add_argument("--output", default="reports/label_audit.json")
    parser.add_argument("--top", type=int, default=25, help="Top-N values to record per field")
    return parser.parse_args()


def top_counts(values, top: int) -> dict:
    counter = Counter(str(v) for v in values)
    return {k: int(v) for k, v in counter.most_common(top)}


def summarize_field(metadata: list, key: str, top: int) -> dict:
    present = [m[key] for m in metadata if isinstance(m, dict) and key in m]
    return {
        "present_rows": len(present),
        "coverage": round(len(present) / max(len(metadata), 1), 4),
        "n_unique": len({str(v) for v in present}),
        "top_values": top_counts(present, top),
    }


def main() -> int:
    args = parse_args()
    emb_path = (REPO_ROOT / args.embeddings) if not Path(args.embeddings).is_absolute() else Path(args.embeddings)
    if not emb_path.exists():
        print(f"ERROR: embeddings not found: {emb_path}")
        return 1

    data = np.load(emb_path, allow_pickle=True)
    keys = list(data.files)
    embeddings = data["embeddings"]
    n, dim = int(embeddings.shape[0]), int(embeddings.shape[1])

    labels = [str(v) for v in data["labels"]] if "labels" in keys else []
    metadata = list(data["metadata"]) if "metadata" in keys else []

    # Union of all metadata field names.
    field_names: set[str] = set()
    for m in metadata:
        if isinstance(m, dict):
            field_names.update(m.keys())
    field_names = sorted(field_names)

    field_summaries = {f: summarize_field(metadata, f, args.top) for f in field_names}

    # Call-type feasibility: is there any field that looks like a call-type label
    # and is well-populated with more than a handful of distinct values?
    calltype_candidates = []
    for f in field_names:
        if any(hint in f.lower() for hint in CALLTYPE_KEY_HINTS):
            summary = field_summaries[f]
            calltype_candidates.append({
                "field": f,
                "coverage": summary["coverage"],
                "n_unique": summary["n_unique"],
            })
    has_calltype = any(c["coverage"] >= 0.5 and c["n_unique"] >= 5 for c in calltype_candidates)

    # Sequence feasibility (Leg 3): calls per source file within provider.
    seq_key_per_file = []
    if metadata and all(isinstance(m, dict) for m in metadata):
        by_file: dict[str, int] = {}
        for m in metadata:
            prov = str(m.get("provider", ""))
            sf = str(m.get("soundfile", ""))
            by_file[f"{prov}::{sf}"] = by_file.get(f"{prov}::{sf}", 0) + 1
        seq_key_per_file = sorted(by_file.values(), reverse=True)
    seq_lengths = np.array(seq_key_per_file) if seq_key_per_file else np.array([0])

    # Ecotype x provider cross-tab (Leg 2 motivation): how confounded are they?
    cross = {}
    if metadata and labels and len(metadata) == len(labels):
        for lab, m in zip(labels, metadata):
            prov = str(m.get("provider", "")) if isinstance(m, dict) else ""
            cross.setdefault(lab, Counter())[prov] += 1
    cross_serializable = {lab: {p: int(c) for p, c in counts.most_common()} for lab, counts in cross.items()}

    # Does each ecotype appear across multiple providers? If an ecotype is only
    # ever seen at one provider, pooled decodability cannot be separated from site.
    ecotype_provider_breadth = {
        lab: len(counts) for lab, counts in cross.items()
    }

    rel_emb = str(emb_path.relative_to(REPO_ROOT)) if emb_path.is_relative_to(REPO_ROOT) else emb_path.name
    report = {
        "embeddings_path": rel_emb,
        "n_rows": n,
        "embedding_dim": dim,
        "npz_keys": keys,
        "label_field_used": "ecotype (via labels array)",
        "ecotype_distribution": top_counts(labels, args.top) if labels else {},
        "n_ecotypes": len({l for l in labels}) if labels else 0,
        "metadata_fields": field_names,
        "field_summaries": field_summaries,
        "calltype": {
            "candidate_fields": calltype_candidates,
            "has_usable_calltype_label": bool(has_calltype),
            "decision": (
                "LEG1_FULL: discrete call-type labels available"
                if has_calltype else
                "LEG1_FALLBACK: no call-type labels; use population/site + unsupervised structure"
            ),
        },
        "sequence_feasibility": {
            "n_source_files": int(len(seq_lengths)),
            "calls_per_file_max": int(seq_lengths.max()),
            "calls_per_file_median": int(np.median(seq_lengths)),
            "calls_per_file_mean": round(float(seq_lengths.mean()), 2),
            "files_with_ge3_calls": int((seq_lengths >= 3).sum()),
            "files_with_ge5_calls": int((seq_lengths >= 5).sum()),
        },
        "provider_confound": {
            "ecotype_by_provider": cross_serializable,
            "ecotype_provider_breadth": ecotype_provider_breadth,
            "single_provider_ecotypes": [
                lab for lab, breadth in ecotype_provider_breadth.items() if breadth <= 1
            ],
        },
    }

    out_path = (REPO_ROOT / args.output) if not Path(args.output).is_absolute() else Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Corpus: {n:,} calls x {dim} dims  |  {report['n_ecotypes']} ecotypes")
    print(f"Ecotype distribution: {report['ecotype_distribution']}")
    print(f"Metadata fields: {field_names}")
    print(f"Call-type decision: {report['calltype']['decision']}")
    print(f"Sequence feasibility: {report['sequence_feasibility']['files_with_ge3_calls']:,} "
          f"files with >=3 calls (max {report['sequence_feasibility']['calls_per_file_max']})")
    print(f"Ecotype provider breadth: {ecotype_provider_breadth}")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build conservative OrcaDolittle validation evidence tables.

This script creates a natural vocal-response proxy table from ordered Wellard
segment timings and writes a behavior/context template when no verified behavior
table is supplied. It deliberately refuses to treat filename-derived labels as
verified behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

BAD_LABEL_SOURCE_TERMS = {
    "filename_behavior_code",
    "filename",
    "session_id",
    "session",
    "inferred_from_filename",
    "derived_from_filename",
}

BEHAVIOR_COLUMNS = [
    "source_file",
    "start_time_s",
    "end_time_s",
    "encounter_id",
    "behavior_context",
    "behavior_label_set",
    "label_source",
    "citation_or_observer",
    "confidence",
    "notes",
]

RESPONSE_COLUMNS = [
    "stimulus_or_call_id",
    "source_file",
    "start_time_s",
    "end_time_s",
    "encounter_id",
    "response_window_s",
    "response_type",
    "response_present",
    "next_vocalization_start_s",
    "next_vocalization_gap_s",
    "label_source",
    "citation_or_observer",
    "notes",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_segment_manifest() -> Path | None:
    candidates = [
        Path("/content/drive/MyDrive/OrcaDolittle_validation_evidence/_cache/wellard_segment_features_manifest.csv"),
        Path("/content/drive/MyDrive/OrcaDolittle_validation_evidence/reports/wellard_segment_features_manifest.csv"),
        Path("/content/drive/MyDrive/OrcaDolittle_validation_evidence/reports/wellard_segment_manifest.csv"),
        # Backward-compatible local search only.
        Path("/content/drive/MyDrive/OrcaDolittle_validation_H1_H8/_cache/wellard_segment_features_manifest.csv"),
    ]
    for path in candidates:
        if path.exists():
            return path
    root = Path("/content/drive/MyDrive")
    if root.exists():
        for pattern in ("**/wellard_segment_features_manifest.csv", "**/wellard_segment_manifest.csv"):
            hits = sorted(root.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
            if hits:
                return hits[0]
    return None


def normalize_segment_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for column in df.columns:
        lc = column.lower()
        if lc in {"audio_file", "file", "filename", "wav", "source_file"}:
            rename[column] = "source_file"
        elif lc in {"start_sec", "start", "start_time_s", "begin_s"}:
            rename[column] = "start_time_s"
        elif lc in {"end_sec", "end", "end_time_s", "stop_s"}:
            rename[column] = "end_time_s"
        elif lc in {"group_id", "recording_id", "encounter", "encounter_id"}:
            rename[column] = "encounter_id"
        elif lc == "segment_id":
            rename[column] = "stimulus_or_call_id"
    out = df.rename(columns=rename).copy()
    missing = [c for c in ["source_file", "start_time_s", "end_time_s"] if c not in out.columns]
    if missing:
        raise ValueError(f"Segment manifest missing required columns: {missing}; columns={list(df.columns)}")
    if "stimulus_or_call_id" not in out.columns:
        out["stimulus_or_call_id"] = [f"segment_{i:06d}" for i in range(len(out))]
    if "encounter_id" not in out.columns:
        out["encounter_id"] = out["source_file"].astype(str).str.replace(r"\.wav$", "", regex=True)
    out["start_time_s"] = pd.to_numeric(out["start_time_s"], errors="coerce")
    out["end_time_s"] = pd.to_numeric(out["end_time_s"], errors="coerce")
    out = out.dropna(subset=["source_file", "start_time_s", "end_time_s"]).copy()
    return out.sort_values(["encounter_id", "source_file", "start_time_s", "end_time_s"]).reset_index(drop=True)


def build_response_proxy(seg: pd.DataFrame, window_s: float) -> pd.DataFrame:
    rows = []
    for (_, _), group in seg.groupby(["encounter_id", "source_file"], dropna=False):
        group = group.sort_values("start_time_s").reset_index(drop=True)
        starts = group["start_time_s"].to_numpy()
        for i, row in group.iterrows():
            next_start = ""
            gap = ""
            if i + 1 < len(group):
                next_start = float(starts[i + 1])
                gap = next_start - float(row["end_time_s"])
            response_present = int(gap != "" and 0 <= float(gap) <= window_s)
            rows.append({
                "stimulus_or_call_id": str(row["stimulus_or_call_id"]),
                "source_file": str(row["source_file"]),
                "start_time_s": float(row["start_time_s"]),
                "end_time_s": float(row["end_time_s"]),
                "encounter_id": str(row["encounter_id"]),
                "response_window_s": float(window_s),
                "response_type": "vocal_continuation_within_window",
                "response_present": response_present,
                "next_vocalization_start_s": next_start,
                "next_vocalization_gap_s": gap,
                "label_source": "derived_from_ordered_acoustic_segments",
                "citation_or_observer": "natural_response_proxy_not_playback",
                "notes": "Proxy only: next detected vocal segment within fixed window; not a playback experiment.",
            })
    return pd.DataFrame(rows, columns=RESPONSE_COLUMNS)


def audit_behavior_table(path: Path | None) -> dict:
    audit = {
        "path": str(path) if path else None,
        "exists": bool(path and path.exists()),
        "passed": False,
        "errors": [],
        "warnings": [],
    }
    if not path or not path.exists():
        audit["errors"].append("No verified behavior/context table supplied.")
        return audit
    df = pd.read_csv(path)
    audit["n_rows"] = int(len(df))
    audit["columns"] = list(df.columns)
    lower_cols = {c.lower(): c for c in df.columns}
    source_col = next((lower_cols[c] for c in lower_cols if any(t in c for t in ["source", "file", "audio", "wav", "recording"])), None)
    label_col = next((lower_cols[c] for c in lower_cols if any(t in c for t in ["behavior", "behaviour", "context", "activity"])), None)
    source_label_col = next((lower_cols[c] for c in lower_cols if c in {"label_source", "behavior_evidence", "evidence", "provenance"}), None)
    if not source_col:
        audit["errors"].append("Missing source/audio/file column.")
    if not label_col:
        audit["errors"].append("Missing behavior/context label column.")
    if label_col:
        counts = df[label_col].astype(str).value_counts().to_dict()
        audit["label_counts"] = counts
        if len([key for key, value in counts.items() if value >= 5]) < 2:
            audit["errors"].append("Fewer than two supported behavior/context labels.")
    if source_label_col:
        sources = set(df[source_label_col].astype(str).str.lower().str.strip())
        audit["label_source_values"] = sorted(sources)
        if any(any(term in source for term in BAD_LABEL_SOURCE_TERMS) for source in sources):
            audit["errors"].append("Label source includes filename/session-derived evidence; not valid for claimable H5-H7.")
    else:
        audit["warnings"].append("No explicit label_source/provenance column found; manual review required.")
    audit["passed"] = not audit["errors"]
    return audit


def write_behavior_template(path: Path) -> None:
    sample = [{
        "source_file": "REPLACE_WITH_AUDIO_FILE.wav",
        "start_time_s": "0.0",
        "end_time_s": "10.0",
        "encounter_id": "REPLACE_WITH_ENCOUNTER_OR_RECORDING_ID",
        "behavior_context": "traveling|foraging|socialising|milling_resting",
        "behavior_label_set": "T|F|S|M or combination such as T,F",
        "label_source": "observer_log|paper_table|verified_manual_annotation",
        "citation_or_observer": "full citation / observer log ID",
        "confidence": "high|medium|low",
        "notes": "Do not use filename-derived labels here.",
    }]
    pd.DataFrame(sample, columns=BEHAVIOR_COLUMNS).to_csv(path, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wellard-segment-manifest", default="")
    parser.add_argument("--verified-behavior-table", default="")
    parser.add_argument("--output-dir", default="/content/drive/MyDrive/OrcaDolittle_verified_evidence")
    parser.add_argument("--response-window-s", type=float, default=30.0)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    seg_path = Path(args.wellard_segment_manifest) if args.wellard_segment_manifest else find_segment_manifest()
    if not seg_path or not seg_path.exists():
        raise SystemExit("No Wellard segment manifest found. Run the Wellard segmentation notebook first.")
    seg = normalize_segment_columns(pd.read_csv(seg_path))
    response = build_response_proxy(seg, args.response_window_s)
    response_path = out / "verified_response_proxy_table.csv"
    response.to_csv(response_path, index=False)

    behavior_path = Path(args.verified_behavior_table) if args.verified_behavior_table else None
    behavior_audit = audit_behavior_table(behavior_path)
    if behavior_audit["passed"] and behavior_path:
        pd.read_csv(behavior_path).to_csv(out / "verified_behavior_context_table.csv", index=False)
    else:
        write_behavior_template(out / "verified_behavior_context_table_TEMPLATE.csv")

    manifest = {
        "segment_manifest_path": str(seg_path),
        "response_proxy_table": str(response_path),
        "response_rows": int(len(response)),
        "response_counts": response["response_present"].value_counts().to_dict(),
        "behavior_audit": behavior_audit,
        "claim_boundary": "Response proxy only; not playback-response evidence or semantic decoding.",
        "files": {},
    }
    for path in sorted(out.glob("*")):
        if path.is_file():
            manifest["files"][path.name] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
    (out / "behavior_context_contract_audit.json").write_text(json.dumps(behavior_audit, indent=2), encoding="utf-8")
    (out / "evidence_package_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "notebook_config_snippet.py").write_text(
        "# Paste into a Colab configuration cell\n"
        f"BEHAVIOR_TABLE_PATH = '{out / 'verified_behavior_context_table.csv'}'\n"
        f"RESPONSE_TABLE_PATH = '{response_path}'\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

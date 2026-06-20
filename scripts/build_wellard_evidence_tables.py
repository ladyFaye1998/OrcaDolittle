#!/usr/bin/env python3
"""Build verified Wellard/Dryad behavior-context evidence tables for H5-H7.

This script uses the Wellard et al. Appendix 2 encounter table as the behavior
source and the Dryad ZIP listing as the recording source. It never treats file
or session labels as behavior labels. For same-date encounters, it maps a
date/session group to an observer-table encounter only when the group's inferred
audio duration matches the table duration within tolerance.

Outputs:
  - wellard_recording_context_map.csv
  - wellard_segment_manifest.csv
  - verified_behavior_context_table.csv
  - wellard_context_audit.csv
  - wellard_evidence_summary.json
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTEXT = REPO_ROOT / "data" / "join_tables" / "wellard_encounter_context.csv"

CHANNELS = 2
WAV_HEADER_BYTES = 44
BEHAVIOR_NAMES = {
    "F": "foraging",
    "S": "socializing",
    "T": "traveling",
    "M": "milling_resting",
}

FILENAME_RE = re.compile(
    r"(?P<survey>\d{4}MM)_(?P<date>\d{2}-[A-Za-z]{3}-\d{2})_"
    r"(?P<session>S\d{2})_.*_(?P<file_id>file\d+)\.wav$"
)


@dataclass(frozen=True)
class Recording:
    source_file: str
    date_iso: str
    session_id: str
    file_id: str
    file_size_bytes: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dryad-zip", required=True, help="Outer Dryad ZIP downloaded from DOI 10.5061/dryad.37pvmcvfr")
    parser.add_argument("--encounter-context", default=str(DEFAULT_CONTEXT))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--segment-s", type=float, default=5.0)
    parser.add_argument("--min-segment-s", type=float, default=1.0)
    parser.add_argument("--duration-match-tolerance-s", type=float, default=2.0)
    return parser.parse_args()


def parse_table_duration(value: str) -> float:
    match = re.fullmatch(r"\s*(\d+):(\d{2}(?:\.\d+)?)\s*", str(value))
    if not match:
        raise ValueError(f"Bad mm:ss duration: {value!r}")
    return int(match.group(1)) * 60 + float(match.group(2))


def parse_recording_name(name: str, size: int) -> Recording:
    base = Path(name).name
    match = FILENAME_RE.search(base)
    if not match:
        raise ValueError(f"Unexpected Wellard WAV filename: {name}")
    date_iso = datetime.strptime(match.group("date"), "%d-%b-%y").date().isoformat()
    return Recording(
        source_file=base,
        date_iso=date_iso,
        session_id=match.group("session"),
        file_id=match.group("file_id"),
        file_size_bytes=int(size),
    )


def list_dryad_recordings(dryad_zip: Path) -> list[Recording]:
    """List WAVs inside the nested Dryad archive without decompressing audio.

    The outer Dryad ZIP stores a single inner ZIP. The inner ZIP uses Deflate64
    for the WAV payloads, which Python's stdlib cannot decompress, but its
    central directory is readable and contains the file sizes needed for
    duration-matching and segment manifests.
    """
    recordings: list[Recording] = []
    with zipfile.ZipFile(dryad_zip) as outer:
        inner_names = [n for n in outer.namelist() if n.lower().endswith(".zip")]
        if len(inner_names) != 1:
            raise ValueError(f"Expected one inner ZIP in {dryad_zip}, found {inner_names}")
        with outer.open(inner_names[0]) as inner_stream:
            with zipfile.ZipFile(inner_stream) as inner:
                for info in inner.infolist():
                    if info.filename.lower().endswith(".wav"):
                        recordings.append(parse_recording_name(info.filename, info.file_size))
    if not recordings:
        raise ValueError(f"No WAV files found in {dryad_zip}")
    return sorted(recordings, key=lambda r: (r.date_iso, r.session_id, r.file_id))


def inferred_duration_s(file_sizes: list[int], sampling_khz: float, bit_depth: int) -> float:
    data_bytes = sum(max(0, int(size) - WAV_HEADER_BYTES) for size in file_sizes)
    bytes_per_second = float(sampling_khz) * 1000.0 * (int(bit_depth) / 8.0) * CHANNELS
    return data_bytes / bytes_per_second


def load_context(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {
        "encounter_id",
        "date_iso",
        "behavior_label_set",
        "sampling_frequency_khz",
        "bit_depth",
        "duration_mmss",
        "label_source",
        "citation_key",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {sorted(missing)}")
    df["duration_s"] = df["duration_mmss"].map(parse_table_duration)
    return df


def best_duration_assignment(
    groups: dict[str, list[Recording]],
    encounters: pd.DataFrame,
    tolerance_s: float,
) -> tuple[dict[str, pd.Series], list[dict]]:
    sessions = sorted(groups)
    if len(sessions) != len(encounters):
        audit = [{
            "date_iso": str(encounters.iloc[0]["date_iso"]),
            "status": "unmatched_session_count",
            "session_count": len(sessions),
            "encounter_count": len(encounters),
        }]
        return {}, audit

    best = None
    for perm in itertools.permutations(range(len(encounters))):
        rows = []
        total_abs_diff = 0.0
        ok = True
        for session, enc_idx in zip(sessions, perm):
            encounter = encounters.iloc[enc_idx]
            files = groups[session]
            duration = inferred_duration_s(
                [r.file_size_bytes for r in files],
                float(encounter["sampling_frequency_khz"]),
                int(encounter["bit_depth"]),
            )
            diff = abs(duration - float(encounter["duration_s"]))
            rows.append({
                "date_iso": str(encounter["date_iso"]),
                "session_id": session,
                "encounter_id": str(encounter["encounter_id"]),
                "session_duration_s": round(duration, 3),
                "table_duration_s": round(float(encounter["duration_s"]), 3),
                "abs_diff_s": round(diff, 3),
                "status": "candidate_match",
            })
            total_abs_diff += diff
            ok = ok and diff <= tolerance_s
        if ok and (best is None or total_abs_diff < best[0]):
            best = (total_abs_diff, perm, rows)

    if best is None:
        audit = []
        for session in sessions:
            for _, encounter in encounters.iterrows():
                files = groups[session]
                duration = inferred_duration_s(
                    [r.file_size_bytes for r in files],
                    float(encounter["sampling_frequency_khz"]),
                    int(encounter["bit_depth"]),
                )
                audit.append({
                    "date_iso": str(encounter["date_iso"]),
                    "session_id": session,
                    "encounter_id": str(encounter["encounter_id"]),
                    "session_duration_s": round(duration, 3),
                    "table_duration_s": round(float(encounter["duration_s"]), 3),
                    "abs_diff_s": round(abs(duration - float(encounter["duration_s"])), 3),
                    "status": "duration_match_failed",
                })
        return {}, audit

    assignment = {session: encounters.iloc[enc_idx] for session, enc_idx in zip(sessions, best[1])}
    audit = [{**row, "status": "duration_matched"} for row in best[2]]
    return assignment, audit


def assign_context(recordings: list[Recording], context: pd.DataFrame, tolerance_s: float):
    by_date_session: dict[tuple[str, str], list[Recording]] = {}
    for rec in recordings:
        by_date_session.setdefault((rec.date_iso, rec.session_id), []).append(rec)

    assignments: dict[tuple[str, str], pd.Series] = {}
    audit: list[dict] = []
    for date_iso, encounters in context.groupby("date_iso", sort=True):
        session_groups = {
            session: files
            for (d, session), files in by_date_session.items()
            if d == date_iso
        }
        if len(encounters) == 1:
            encounter = encounters.iloc[0]
            for session, files in session_groups.items():
                assignments[(date_iso, session)] = encounter
                duration = inferred_duration_s(
                    [r.file_size_bytes for r in files],
                    float(encounter["sampling_frequency_khz"]),
                    int(encounter["bit_depth"]),
                )
                audit.append({
                    "date_iso": date_iso,
                    "session_id": session,
                    "encounter_id": str(encounter["encounter_id"]),
                    "session_duration_s": round(duration, 3),
                    "table_duration_s": round(float(encounter["duration_s"]), 3),
                    "abs_diff_s": round(abs(duration - float(encounter["duration_s"])), 3),
                    "status": "single_encounter_date",
                })
        else:
            matched, rows = best_duration_assignment(session_groups, encounters.reset_index(drop=True), tolerance_s)
            audit.extend(rows)
            for session, encounter in matched.items():
                assignments[(date_iso, session)] = encounter

    return assignments, audit


def build_recording_context_rows(recordings: list[Recording], assignments: dict[tuple[str, str], pd.Series]) -> list[dict]:
    rows: list[dict] = []
    by_date_session: dict[tuple[str, str], list[Recording]] = {}
    for rec in recordings:
        by_date_session.setdefault((rec.date_iso, rec.session_id), []).append(rec)

    for key, files in sorted(by_date_session.items()):
        if key not in assignments:
            continue
        encounter = assignments[key]
        cursor = 0.0
        for rec in sorted(files, key=lambda r: r.file_id):
            duration = inferred_duration_s(
                [rec.file_size_bytes],
                float(encounter["sampling_frequency_khz"]),
                int(encounter["bit_depth"]),
            )
            rows.append({
                "source_file": rec.source_file,
                "recording_id": rec.source_file.replace(".wav", ""),
                "encounter_id": str(encounter["encounter_id"]),
                "date_iso": rec.date_iso,
                "session_id": rec.session_id,
                "file_id": rec.file_id,
                "recording_start_s": round(cursor, 3),
                "recording_end_s": round(cursor + duration, 3),
                "recording_duration_s": round(duration, 3),
                "behavior_label_set": str(encounter["behavior_label_set"]).replace(" ", ""),
                "label_source": "Wellard2020_paper_table_duration_matched",
                "citation_or_observer": (
                    "Wellard et al. 2020 Appendix 2 Table 1; "
                    "Dryad doi 10.5061/dryad.37pvmcvfr"
                ),
                "confidence": "medium",
                "mapping_basis": "observer_table_date_plus_duration_matched_recording_group",
                "notes": (
                    "Recording-level observed context. Behavior label is from the "
                    "Wellard observer table, not from filename/session text."
                ),
            })
            cursor += duration
    return rows


def build_segments(recording_rows: list[dict], segment_s: float, min_segment_s: float) -> list[dict]:
    rows: list[dict] = []
    for rec in recording_rows:
        duration = float(rec["recording_duration_s"])
        start = 0.0
        idx = 0
        while start < duration:
            end = min(start + segment_s, duration)
            if end - start >= min_segment_s:
                rows.append({
                    "segment_id": f"{rec['recording_id']}__{idx:05d}",
                    "source_file": rec["source_file"],
                    "start_time_s": round(start, 3),
                    "end_time_s": round(end, 3),
                    "duration_s": round(end - start, 3),
                    "encounter_id": rec["encounter_id"],
                    "recording_id": rec["recording_id"],
                    "date_iso": rec["date_iso"],
                    "session_id": rec["session_id"],
                    "behavior_label_set": rec["behavior_label_set"],
                    "label_source": rec["label_source"],
                    "citation_or_observer": rec["citation_or_observer"],
                    "confidence": rec["confidence"],
                    "notes": rec["notes"],
                })
            start += segment_s
            idx += 1
    return rows


def build_behavior_table(segment_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for seg in segment_rows:
        labels = [x.strip() for x in str(seg["behavior_label_set"]).split(",") if x.strip()]
        for label in labels:
            rows.append({
                "source_file": seg["source_file"],
                "start_time_s": seg["start_time_s"],
                "end_time_s": seg["end_time_s"],
                "encounter_id": seg["encounter_id"],
                "recording_id": seg["recording_id"],
                "segment_id": seg["segment_id"],
                "behavior_context": BEHAVIOR_NAMES.get(label, label),
                "behavior_label_set": ",".join(labels),
                "label_source": seg["label_source"],
                "citation_or_observer": seg["citation_or_observer"],
                "confidence": seg["confidence"],
                "notes": (
                    "Weak recording-level observed context inherited by segment; "
                    "not exact segment-level behavior. Exclude from strong semantic claims."
                ),
            })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    dryad_zip = Path(args.dryad_zip)
    if not dryad_zip.exists():
        print(f"ERROR: Dryad ZIP not found: {dryad_zip}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)
    context = load_context(Path(args.encounter_context))
    recordings = list_dryad_recordings(dryad_zip)
    assignments, audit = assign_context(recordings, context, args.duration_match_tolerance_s)
    recording_rows = build_recording_context_rows(recordings, assignments)
    segment_rows = build_segments(recording_rows, args.segment_s, args.min_segment_s)
    behavior_rows = build_behavior_table(segment_rows)

    write_csv(output_dir / "wellard_context_audit.csv", audit)
    write_csv(output_dir / "wellard_recording_context_map.csv", recording_rows)
    write_csv(output_dir / "wellard_segment_manifest.csv", segment_rows)
    write_csv(output_dir / "verified_behavior_context_table.csv", behavior_rows)

    mapped_recordings = {row["source_file"] for row in recording_rows}
    summary = {
        "dryad_zip": str(dryad_zip),
        "encounter_context": str(Path(args.encounter_context)),
        "recordings_in_zip": len(recordings),
        "recordings_mapped": len(mapped_recordings),
        "segments": len(segment_rows),
        "behavior_rows": len(behavior_rows),
        "segment_s": args.segment_s,
        "min_segment_s": args.min_segment_s,
        "duration_match_tolerance_s": args.duration_match_tolerance_s,
        "behavior_context_counts": (
            pd.DataFrame(behavior_rows)["behavior_context"].value_counts().to_dict()
            if behavior_rows else {}
        ),
        "outputs": {
            "recording_context_map": str(output_dir / "wellard_recording_context_map.csv"),
            "segment_manifest": str(output_dir / "wellard_segment_manifest.csv"),
            "behavior_context_table": str(output_dir / "verified_behavior_context_table.csv"),
            "audit": str(output_dir / "wellard_context_audit.csv"),
        },
    }
    (output_dir / "wellard_evidence_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    if len(mapped_recordings) != len(recordings):
        print("ERROR: not all recordings could be mapped to observer-table context.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

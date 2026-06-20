#!/usr/bin/env python3
"""H7: playback-candidate motif discovery from Wellard context tokens.

This head identifies acoustic motif tokens enriched in independently observed
recording-level contexts. It does not claim playback response evidence or
semantic meaning; it produces reproducible candidate windows for future tests.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokens", required=True, help="Token CSV from H6")
    parser.add_argument("--behavior-table", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--min-support", type=int, default=8)
    parser.add_argument("--min-odds-ratio", type=float, default=1.5)
    parser.add_argument("--max-windows-per-candidate", type=int, default=12)
    return parser.parse_args()


def bh_fdr(pvalues: list[float]) -> list[float]:
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    q = np.empty_like(p)
    prev = 1.0
    n = len(p)
    for rank, idx in enumerate(order[::-1], start=1):
        i = n - rank + 1
        value = min(prev, p[idx] * n / i)
        q[idx] = value
        prev = value
    return q.tolist()


def build_segment_context(tokens: pd.DataFrame, behavior: pd.DataFrame) -> pd.DataFrame:
    contexts = sorted(behavior["behavior_context"].dropna().astype(str).unique())
    labels = behavior.assign(value=1).pivot_table(
        index="segment_id",
        columns="behavior_context",
        values="value",
        aggfunc="max",
        fill_value=0,
    )
    labels = labels.reindex(columns=contexts, fill_value=0)
    joined = tokens.merge(labels, left_on="segment_id", right_index=True, how="inner")
    if joined.empty:
        raise ValueError("no token rows joined to behavior table")
    return joined


def discover_candidates(df: pd.DataFrame, min_support: int, min_odds_ratio: float) -> list[dict]:
    contexts = [
        c for c in df.columns
        if c not in {
            "segment_id", "source_file", "start_time_s", "end_time_s", "duration_s",
            "encounter_id", "recording_id", "date_iso", "session_id",
            "behavior_label_set", "label_source", "citation_or_observer",
            "confidence", "notes", "token_id",
        }
        and set(pd.Series(df[c]).dropna().unique()).issubset({0, 1})
    ]
    rows = []
    for token in sorted(df["token_id"].astype(int).unique()):
        token_mask = df["token_id"].astype(int).to_numpy() == token
        for context in contexts:
            ctx_mask = df[context].to_numpy(dtype=int) == 1
            a = int(np.sum(token_mask & ctx_mask))
            b = int(np.sum(token_mask & ~ctx_mask))
            c = int(np.sum(~token_mask & ctx_mask))
            d = int(np.sum(~token_mask & ~ctx_mask))
            if a < min_support:
                continue
            odds = float(((a + 0.5) * (d + 0.5)) / ((b + 0.5) * (c + 0.5)))
            _, pvalue = fisher_exact([[a, b], [c, d]], alternative="greater")
            context_rate = float(a / max(a + c, 1))
            wrong_context_rate = float(b / max(b + d, 1))
            rows.append({
                "token_id": int(token),
                "context": context,
                "support": a,
                "token_outside_context": b,
                "context_without_token": c,
                "neither": d,
                "context_token_rate": context_rate,
                "wrong_context_token_rate": wrong_context_rate,
                "odds_ratio": odds,
                "pvalue": float(pvalue),
                "passes_threshold": bool(odds >= min_odds_ratio),
            })
    if rows:
        qvalues = bh_fdr([r["pvalue"] for r in rows])
        for row, qvalue in zip(rows, qvalues):
            row["qvalue_bh"] = float(qvalue)
            row["candidate_ready"] = bool(row["passes_threshold"] and qvalue < 0.1)
    return sorted(rows, key=lambda r: (not r.get("candidate_ready", False), -r["odds_ratio"], -r["support"]))


def candidate_windows(df: pd.DataFrame, candidates: list[dict], max_windows: int) -> pd.DataFrame:
    rows = []
    for cand in candidates:
        mask = (df["token_id"].astype(int) == cand["token_id"]) & (df[cand["context"]].astype(int) == 1)
        subset = df.loc[mask].sort_values(["source_file", "start_time_s"]).head(max_windows)
        for _, seg in subset.iterrows():
            rows.append({
                "token_id": cand["token_id"],
                "context": cand["context"],
                "source_file": seg["source_file"],
                "start_time_s": seg["start_time_s"],
                "end_time_s": seg["end_time_s"],
                "encounter_id": seg.get("encounter_id", ""),
                "recording_id": seg.get("recording_id", ""),
                "segment_id": seg.get("segment_id", ""),
                "notes": "Candidate extraction window; not playback-response evidence.",
            })
    return pd.DataFrame(rows)


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tokens = pd.read_csv(args.tokens)
    behavior = pd.read_csv(args.behavior_table)
    required = {"segment_id", "token_id", "source_file", "start_time_s", "end_time_s"}
    missing = required - set(tokens.columns)
    if missing:
        print(f"ERROR: tokens CSV missing columns: {sorted(missing)}", file=sys.stderr)
        return 2

    joined = build_segment_context(tokens, behavior)
    candidates = discover_candidates(joined, args.min_support, args.min_odds_ratio)
    candidates_df = pd.DataFrame(candidates)
    windows_df = candidate_windows(joined, candidates, args.max_windows_per_candidate)

    candidates_path = output_dir / "h7_candidate_motifs_wellard.csv"
    windows_path = output_dir / "h7_candidate_windows_wellard.csv"
    candidates_df.to_csv(candidates_path, index=False)
    windows_df.to_csv(windows_path, index=False)

    ready_count = int(sum(1 for c in candidates if c.get("candidate_ready")))
    summary = {
        "head": "H7",
        "status": "pass",
        "claim": (
            "Candidate motif/context associations discovered for future playback-style tests; "
            "no playback response or semantic meaning is claimed."
        ),
        "tokens": str(Path(args.tokens)),
        "behavior_table": str(Path(args.behavior_table)),
        "n_segments_joined": int(len(joined)),
        "n_candidate_tests_reported": int(len(candidates)),
        "n_candidate_ready": ready_count,
        "min_support": args.min_support,
        "min_odds_ratio": args.min_odds_ratio,
        "candidates_csv": str(candidates_path),
        "candidate_windows_csv": str(windows_path),
        "top_candidates": candidates[:20],
    }
    metrics_path = output_dir / "h7_metrics_wellard.json"
    metrics_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

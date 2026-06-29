#!/usr/bin/env python3
"""Build a reproducibility manifest for the current local result set.

Hashes the frozen embedding artifact, every per-head metrics JSON and figure,
and the report summaries, into a single manifest with the exact commands that
regenerate each number. This is the public reproducibility bundle referenced in
`docs/local_environment_manifest.md`. It is separate from
`reports/artifact_hashes.json`, which records the original Colab run provenance;
this manifest records the local re-run that produced the published figures.

Usage:
  python scripts/make_repro_bundle.py --output reports/repro_bundle.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ARTIFACT = "data/embeddings/aves2_full_labeled.npz"

REGEN_COMMANDS = {
    "freeze": "python scripts/freeze_corpus.py --embeddings data/embeddings/aves2_full_labeled.npz --output reports/corpus_freeze.json",
    "label_audit": "python scripts/audit_corpus_labels.py --embeddings data/embeddings/aves2_full_labeled.npz --output reports/label_audit.json",
    "h1": "python scripts/run_h1_probes.py --embeddings data/embeddings/aves2_full_labeled.npz --n-perm 200 --perm-train-subsample 2000 --group-field provider",
    "h2": "python scripts/run_h2_clustering.py --embeddings data/embeddings/aves2_full_labeled.npz --min-cluster-size 25 --min-samples 5",
    "h3": "python scripts/run_h3_sequence_lm.py --embeddings data/embeddings/aves2_full_labeled.npz --epochs 30 --n-perm 100 --device cuda --vocab-size 40",
    "h4_within_and_site": "python scripts/run_h4_confound.py --embeddings data/embeddings/aves2_full_labeled.npz --n-perm 200 --min-per-class 40",
    "h4_transfer_fast": "python scripts/run_h4_confound.py --embeddings data/embeddings/aves2_full_labeled.npz --skip-within",
    "h4_figure": "python scripts/plot_h4_summary.py --metrics figures/h4_metrics_aves2_full_labeled.json",
    "rung4_sequence_structure": "python scripts/run_sequence_structure.py --embeddings data/embeddings/aves2_full_labeled.npz --vocab-size 40 --n-perm 1000",
    "rung1_calltype_discovery": "python scripts/run_calltype_discovery.py --embeddings data/embeddings/aves2_full_labeled.npz --ecotype SRKW",
    "rung1_calltype_discovery_single_site": "python scripts/run_calltype_discovery.py --embeddings data/embeddings/aves2_full_labeled.npz --ecotype SRKW --single-provider",
    "calltype_manifest": "python scripts/build_calltype_manifest.py",
    "rung1_calltype_model": "python scripts/run_calltype_model.py --embeddings data/embeddings/aves2_full_labeled.npz --manifest data/join_tables/call_type_manifest.csv --min-per-type 30",
    "rung1_calltype_model_full": "run notebooks/calltype_encode_colab.ipynb on a GPU (encodes the full DCLDE call-type catalogue and runs the site-controlled models; writes reports/calltype_model_full_summary.json and figures/calltype_model_full.png)",
    "rung4_calltype_sequence": "python scripts/run_calltype_sequence.py --manifest data/join_tables/call_type_manifest.csv --n-perm 1000",
    "public_data_audit": "python scripts/fetch_orcasound_labels.py --bucket acoustic-sandbox --list labeled-data/",
}

INCLUDE_GLOBS = [
    "figures/h1_metrics_aves2_full_labeled.json",
    "figures/h2_metrics_aves2_full_labeled.json",
    "figures/h3_metrics_aves2_full_labeled.json",
    "figures/h4_metrics_aves2_full_labeled.json",
    "figures/sequence_structure_aves2_full_labeled.json",
    "figures/calltype_discovery_srkw.json",
    "figures/calltype_discovery_srkw_single.json",
    "figures/h1_probes_aves2_full_labeled.png",
    "figures/h2_clustering_aves2_full_labeled.png",
    "figures/h3_sequence_lm_aves2_full_labeled.png",
    "figures/h4_confound_aves2_full_labeled.png",
    "figures/sequence_structure_aves2_full_labeled.png",
    "figures/calltype_discovery_srkw.png",
    "figures/calltype_discovery_srkw_single.png",
    "figures/calltype_model_srkw.png",
    "figures/calltype_model_full.png",
    "figures/calltype_sequence.png",
    "reports/corpus_freeze.json",
    "reports/label_audit.json",
    "reports/results_summary.json",
    "reports/calltype_model_summary.json",
    "reports/calltype_model_full_summary.json",
    "reports/calltype_sequence_summary.json",
    "reports/calltype_manifest_summary.json",
    "reports/dclde_calltype_survey.json",
    "data/join_tables/call_type_manifest.csv",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/repro_bundle.json")
    args = parser.parse_args()

    artifact_path = REPO_ROOT / ARTIFACT
    hashes: dict[str, str] = {}
    missing: list[str] = []

    if artifact_path.exists():
        hashes[ARTIFACT] = sha256_file(artifact_path)
    else:
        missing.append(ARTIFACT)

    for rel in INCLUDE_GLOBS:
        p = REPO_ROOT / rel
        if p.exists():
            hashes[rel] = sha256_file(p)
        else:
            missing.append(rel)

    bundle = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "artifact": ARTIFACT,
        "regeneration_commands": REGEN_COMMANDS,
        "sha256": hashes,
        "missing": missing,
        "note": (
            "Local re-run manifest for the published figures/metrics. "
            "reports/artifact_hashes.json records the original Colab run provenance."
        ),
    }

    out_path = (REPO_ROOT / args.output) if not Path(args.output).is_absolute() else Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    print(f"Repro bundle: {len(hashes)} files hashed, {len(missing)} missing")
    for rel, digest in hashes.items():
        print(f"  {digest[:12]}  {rel}")
    if missing:
        print("  MISSING (run the regeneration command first):")
        for m in missing:
            print(f"    {m}")
    print(f"  wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

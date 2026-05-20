"""Load per-encounter call-ID streams from the DCLDE 2026 ``Annotations.csv``.

Reference
---------
DCLDE 2026 corpus (Palmer et al., 2025) [@palmer2025dclde; @palmer2025dclde_data].
US Government public domain. Dataset DOI ``10.25921/15ey-mh50``.

This loader implements the data path described in
``docs/dataset_plan.md`` (Stage 1 / Week 1) and the encounter-streaming step
of head H3 in ``docs/ai_architecture.md``. It is a pure-Python parser; the
real run on the 4090 workstation does not need PyTorch in this module's
import path. ``pandas`` is the only optional dependency, and the loader
falls back to a stdlib ``csv`` parser if pandas is not available.

The DCLDE 2026 schema is not fully fixed in advance, and per-provider folders
in the corpus may name columns differently. Column names are therefore
configurable on the loader call rather than baked in. The Stage-1 schema
confirmation task in ``docs/dataset_plan.md`` is what pins these names for
a given pull of the data.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from orcadolittle.data.call_streams import Vocab


@dataclass
class DCLDEColumns:
    """Column-name mapping for the DCLDE 2026 ``Annotations.csv``.

    Defaults reflect the column names reported on the dataset's NCEI
    landing page at time of writing; verify against the actual CSV header
    on download per the Stage-1 schema-confirmation task in
    ``docs/dataset_plan.md``.
    """

    call_type: str = "call_type"
    start_time: str = "start_time_s"
    site: str = "site"
    ecotype: str = "ecotype"
    encounter_id: Optional[str] = None


@dataclass
class EncounterStreamConfig:
    """Controls how raw annotation rows are sessionised into encounters.

    If ``columns.encounter_id`` is set on the input, that column is used
    directly and ``gap_seconds`` is ignored. Otherwise an encounter is
    defined as a maximal run of consecutive annotations at the same
    ``site`` whose successive ``start_time`` values differ by no more
    than ``gap_seconds``.
    """

    gap_seconds: float = 300.0
    min_calls_per_encounter: int = 4
    ecotype: Optional[str] = None


def _iter_rows(csv_path: Path) -> Iterable[dict]:
    try:
        import pandas as pd  # type: ignore

        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            yield {k: row[k] for k in df.columns}
    except ImportError:
        with csv_path.open("r", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                yield row


def load_dclde_streams(
    csv_path: str | Path,
    columns: DCLDEColumns | None = None,
    cfg: EncounterStreamConfig | None = None,
) -> tuple[list[list[int]], Vocab, dict]:
    """Load DCLDE 2026 annotations and emit per-encounter call-ID streams.

    Parameters
    ----------
    csv_path:
        Path to ``Annotations.csv`` (or a per-provider subset thereof).
    columns:
        Column-name mapping. Pass an explicit ``DCLDEColumns`` if the
        downloaded CSV uses different headers than the defaults.
    cfg:
        Sessionisation policy. ``cfg.ecotype`` filters to a single
        ecotype if set (e.g. ``"SRKW"``); ``None`` keeps all rows.

    Returns
    -------
    streams:
        ``list[list[int]]`` of per-encounter call-ID streams, with IDs in
        the shared vocabulary (already offset past special tokens by the
        ``Vocab`` object).
    vocab:
        The ``Vocab`` built from the call-type values that survived
        filtering, in insertion order.
    meta:
        Diagnostic dict: ``num_rows``, ``num_kept``, ``num_encounters``,
        ``ecotype_filter``, ``mean_len``.
    """
    columns = columns or DCLDEColumns()
    cfg = cfg or EncounterStreamConfig()
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"DCLDE annotations CSV not found at {csv_path}. Pull per Stage-1 of "
            "EXECUTION_PLAN.md before running the H3 head."
        )

    rows: list[dict] = []
    num_rows = 0
    for row in _iter_rows(csv_path):
        num_rows += 1
        if cfg.ecotype is not None and str(row.get(columns.ecotype, "")) != cfg.ecotype:
            continue
        call = row.get(columns.call_type)
        if call is None or str(call).strip() == "":
            continue
        rows.append(row)

    rows.sort(
        key=lambda r: (
            str(r.get(columns.site, "")),
            float(r.get(columns.start_time, 0.0) or 0.0),
        )
    )

    if columns.encounter_id is not None:
        groups: dict[tuple, list[str]] = {}
        for r in rows:
            key = (str(r.get(columns.site, "")), str(r.get(columns.encounter_id, "")))
            groups.setdefault(key, []).append(str(r[columns.call_type]))
        encounter_seqs = list(groups.values())
    else:
        encounter_seqs = []
        current: list[str] = []
        current_site: Optional[str] = None
        last_t: Optional[float] = None
        for r in rows:
            site = str(r.get(columns.site, ""))
            t = float(r.get(columns.start_time, 0.0) or 0.0)
            same = (
                site == current_site
                and last_t is not None
                and (t - last_t) <= cfg.gap_seconds
            )
            if not same and current:
                encounter_seqs.append(current)
                current = []
            current.append(str(r[columns.call_type]))
            current_site = site
            last_t = t
        if current:
            encounter_seqs.append(current)

    encounter_seqs = [
        s for s in encounter_seqs if len(s) >= cfg.min_calls_per_encounter
    ]

    vocab = Vocab.from_streams(encounter_seqs)
    streams = [vocab.encode(s) for s in encounter_seqs]

    meta = {
        "num_rows": num_rows,
        "num_kept": len(rows),
        "num_encounters": len(streams),
        "ecotype_filter": cfg.ecotype,
        "mean_len": (
            sum(len(s) for s in streams) / max(1, len(streams)) if streams else 0.0
        ),
    }
    return streams, vocab, meta

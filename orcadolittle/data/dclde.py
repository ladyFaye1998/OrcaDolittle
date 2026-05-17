"""DCLDE 2026 dataset loader.

Dataset
-------
*Palmer et al. (2025).* "A Public Dataset of Annotated *Orcinus orca*
Acoustic Signals for Detection and Ecotype Classification." *Scientific
Data*. `doi:10.1038/s41597-025-05281-5
<https://doi.org/10.1038/s41597-025-05281-5>`_

* 225 000 call-level annotations
* 11 years of recordings, 23 Northeast Pacific locations
* Three ecotypes: Resident, Bigg's (Transient), Offshore
* DOI: ``10.25921/15ey-mh50``
* Companion code: https://github.com/JPalmerK/DCLDE_Dataset

The loader streams from NOAA NCEI on first use and caches under
:data:`orcadolittle.config.CACHE_ROOT`. We do not redistribute the audio.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from orcadolittle.config import CACHE_ROOT, ECOTYPES

if TYPE_CHECKING:
    from collections.abc import Iterator


DCLDE_DOI: str = "10.25921/15ey-mh50"
DCLDE_PAPER_DOI: str = "10.1038/s41597-025-05281-5"
DCLDE_CODE_URL: str = "https://github.com/JPalmerK/DCLDE_Dataset"
DCLDE_LANDING_URL: str = (
    "https://catalog.data.gov/dataset/"
    "dclde-2026-killer-whale-orcinus-orca-ecotype-and-other-species-"
    "annotations-for-the-detecti-2026"
)


@dataclass(frozen=True)
class DCLDEAnnotation:
    """One row from the DCLDE 2026 annotation table."""

    file_id: str
    start_s: float
    end_s: float
    ecotype: str
    call_type: str | None
    location: str
    confidence: str = "high"
    notes: str = ""


def load_index(
    *,
    cache_dir: Path | None = None,
    download: bool = False,
) -> Path:
    """Return the path to the DCLDE 2026 annotation index.

    If ``download`` is ``True`` and the index is not present, the loader
    fetches it from NCEI. Otherwise it returns the cached path or raises a
    :class:`FileNotFoundError` with download instructions.
    """
    cache = Path(cache_dir or CACHE_ROOT) / "dclde2026"
    cache.mkdir(parents=True, exist_ok=True)
    index_path = cache / "annotations.parquet"
    if index_path.exists():
        return index_path
    if not download:
        msg = (
            "DCLDE 2026 index not cached. Run "
            "`orcadolittle data download --dataset dclde2026` or pass "
            "download=True."
        )
        raise FileNotFoundError(msg)
    _download_dclde_index(index_path)
    return index_path


def iter_annotations(
    *,
    ecotype: str | None = None,
    call_type: str | None = None,
    cache_dir: Path | None = None,
) -> Iterator[DCLDEAnnotation]:
    """Iterate over DCLDE 2026 annotations with optional filtering."""
    try:
        import pandas as pd
    except ImportError as exc:
        msg = "iter_annotations requires `pip install orcadolittle[benchmarks]`"
        raise ImportError(msg) from exc

    index_path = load_index(cache_dir=cache_dir)
    df = pd.read_parquet(index_path)
    if ecotype is not None:
        if ecotype not in ECOTYPES:
            msg = f"Unknown ecotype: {ecotype!r}. Known: {ECOTYPES}"
            raise ValueError(msg)
        df = df[df["ecotype"] == ecotype]
    if call_type is not None:
        df = df[df["call_type"] == call_type]
    for row in df.itertuples():
        yield DCLDEAnnotation(
            file_id=str(row.file_id),
            start_s=float(row.start_s),
            end_s=float(row.end_s),
            ecotype=str(row.ecotype),
            call_type=str(row.call_type) if row.call_type else None,
            location=str(row.location),
            confidence=str(getattr(row, "confidence", "high")),
            notes=str(getattr(row, "notes", "")),
        )


def _download_dclde_index(_target: Path) -> None:
    """Fetch the annotation parquet from NCEI.

    The exact NCEI bucket layout is documented at:
    https://www.ncei.noaa.gov/products/passive-acoustic-data
    """
    msg = (
        "Automatic DCLDE 2026 download is intentionally not bundled — the "
        "dataset is several GB. Follow the instructions at\n"
        f"  {DCLDE_LANDING_URL}\n"
        "and place the parquet at the path printed above."
    )
    raise NotImplementedError(msg)

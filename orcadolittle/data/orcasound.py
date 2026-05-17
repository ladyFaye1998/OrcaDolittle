"""OrcaSound public hydrophone dataset.

Source
------
- AWS Open Data Registry: https://registry.opendata.aws/orcasound/
- Project portal: https://www.orcasound.net/portfolio/ai-for-orcas-open-bioacoustic-data-science
- GitHub (ML-ready labels): https://github.com/orcasound/orca-dclde

The buckets ``s3://acoustic-sandbox`` and ``s3://orcasound-hls`` host live
HLS streams from Salish Sea hydrophones plus archived FLAC at 48 / 96 /
192 kHz. We use the archived FLAC for offline evaluation and the HLS
streams for real-time deployment testing.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from orcadolittle.config import CACHE_ROOT


ORCASOUND_REGISTRY_URL: str = "https://registry.opendata.aws/orcasound/"
ORCASOUND_REPO_URL: str = "https://github.com/orcasound/orca-dclde"
ORCASOUND_HLS_PUBLIC: str = "https://live.orcasound.net"
ORCASOUND_ARCHIVE_BUCKET: str = "acoustic-sandbox"


@dataclass(frozen=True)
class OrcaSoundClip:
    """A single archived OrcaSound clip."""

    s3_key: str
    duration_s: float
    sample_rate: int
    location: str
    captured_at: str
    has_orca: bool | None = None


def list_archive(
    *,
    location: str | None = None,
    cache_dir: Path | None = None,
) -> list[OrcaSoundClip]:
    """List archived OrcaSound clips with optional location filtering.

    Live S3 access is intentionally lazy — the function returns the cached
    index if present, otherwise raises :class:`FileNotFoundError`. Use the
    CLI ``orcadolittle data download --dataset orcasound`` to populate.
    """
    cache = Path(cache_dir or CACHE_ROOT) / "orcasound"
    cache.mkdir(parents=True, exist_ok=True)
    index_path = cache / "archive_index.json"
    if not index_path.exists():
        msg = (
            "OrcaSound archive index not cached. Run "
            "`orcadolittle data download --dataset orcasound` to populate."
        )
        raise FileNotFoundError(msg)

    import json

    raw = json.loads(index_path.read_text(encoding="utf-8"))
    clips = [OrcaSoundClip(**row) for row in raw]
    if location is not None:
        clips = [c for c in clips if c.location == location]
    return clips


def stream_hls(node: str = "rpi_orcasound_lab") -> str:
    """Return the HLS URL for a live OrcaSound hydrophone node.

    Known nodes (see :data:`ORCASOUND_REGISTRY_URL` for the live list):
    * ``rpi_orcasound_lab`` — Bush Point, Whidbey Island
    * ``rpi_port_townsend`` — Port Townsend
    * ``rpi_sunset_bay`` — Sunset Bay
    """
    return f"{ORCASOUND_HLS_PUBLIC}/listen/{node}"

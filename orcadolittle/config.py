"""Project-wide configuration constants.

Everything that is *not* a tunable hyperparameter belongs here. Hyperparameters
live next to the modules that use them and are surfaced through the CLI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PACKAGE_ROOT: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = PACKAGE_ROOT.parent

DATA_ROOT: Path = PROJECT_ROOT / "data"
CACHE_ROOT: Path = DATA_ROOT / "cache"
WEIGHTS_ROOT: Path = PACKAGE_ROOT / "models" / "weights"

SAMPLE_RATE: int = 16_000
N_MELS: int = 128
HOP_LENGTH: int = 256
WIN_LENGTH: int = 1024

ECOTYPES: tuple[str, ...] = ("resident", "biggs", "offshore")
RESPONSE_CLASSES: tuple[str, ...] = ("reply", "approach", "avoid", "no_response")

CONFIDENCE_TIERS: tuple[str, ...] = ("very_high", "high", "medium", "low", "very_low")

ENCODER_REPOS: dict[str, str] = {
    "aves2-bio": "EarthSpeciesProject/esp-aves2-sl-beats-bio",
    "aves2-all": "EarthSpeciesProject/esp-aves2-sl-beats-all",
    "aves": "earthspecies/aves",
    "perch-2.0": "google/perch-2.0",
}

DEFAULT_ENCODER: str = "aves2-bio"


@dataclass(frozen=True)
class RuntimeConfig:
    """Container for the runtime knobs surfaced through the CLI."""

    encoder: str = DEFAULT_ENCODER
    device: str = "auto"
    sample_rate: int = SAMPLE_RATE
    seed: int = 42
    cache_dir: Path = field(default_factory=lambda: CACHE_ROOT)
    weights_dir: Path = field(default_factory=lambda: WEIGHTS_ROOT)
    log_level: str = "INFO"


DEFAULT_RUNTIME = RuntimeConfig()

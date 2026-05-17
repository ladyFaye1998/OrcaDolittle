# Data directory

This folder is intentionally empty in the source tree. Datasets are downloaded into ``data/cache/<dataset_id>/`` on first use.

The provenance and download instructions for every dataset OrcaDolittle depends on are documented in [`docs/data.md`](../docs/data.md).

## Quick reference

| Dataset | Subfolder | First-use command |
|:---|:---|:---|
| DCLDE 2026 | `data/cache/dclde2026/` | `orcadolittle data download --dataset dclde2026` |
| OrcaSound archive | `data/cache/orcasound/` | `orcadolittle data download --dataset orcasound` |
| Playback corpus (curated) | shipped in the package, no download required | — |

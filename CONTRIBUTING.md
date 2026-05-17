# Contributing to OrcaDolittle

OrcaDolittle is an open project that genuinely benefits from contributions across disciplines — cetacean ethology, bioacoustics, machine learning, field operations, and ethics review. This document describes how to help.

## Areas where contributions are most useful

- **Per-trial playback data.** &ensp;The off-policy bandit and response predictor currently learn from per-condition statistics extracted from published papers. If you authored or have access to per-trial raw response data from a published orca playback experiment, that single contribution would materially improve the system.
- **Under-represented ecotypes.** &ensp;DCLDE 2026 is dominated by Northeast Pacific Resident populations. Recordings or annotations for Bigg's (Transient), Offshore, Norwegian, Icelandic, Crozet, Antarctic, and Atlantic populations meaningfully extend the calibrated coverage.
- **Field-deployment partnerships.** &ensp;Teams with IRB-approved playback protocols and active deployments can validate the closed loop in situ.
- **Methodological audits.** &ensp;Counter-examples to the response-predictor's counterfactual checks, alternative falsifiability tests, and adversarial input distributions are explicitly welcome.

## Code contributions

1. Open an issue first if the contribution is non-trivial — it saves duplicated effort.
2. Fork the repository, create a feature branch from `main`.
3. Install the development extras: `pip install -e ".[dev]"`.
4. Run the linters before committing: `ruff check . && mypy orcadolittle && pytest`.
5. Open a pull request that explains *what changed*, *why*, and *how it was tested*. Reference any related issues.

## Style

- Follow the existing structure (`orcadolittle/core/*` for analysis engines, `orcadolittle/models/*` for architectures, `orcadolittle/data/*` for loaders, `orcadolittle/benchmarks/*` for evaluation).
- Public functions and classes should have type annotations and concise docstrings.
- Avoid adding heavyweight dependencies; prefer to extend an existing one or document the trade-off in the pull request.
- Comments explain *intent and constraints*, not what the code does. We trust the reader to read.

## Data and weights

- Audio and large weights are **not** committed to the repository. Small reference taxonomy files and calibration heads (`< 5 MB`) may be committed under `orcadolittle/models/weights/`.
- Public datasets are pulled from their canonical source on first use. New data sources should be documented in `docs/data.md` with provenance, licence, and citation.

## Reproducibility

Every benchmark in the README is regenerable from `orcadolittle benchmark` with deterministic seeds. If you add a benchmark, follow the same pattern (`orcadolittle/benchmarks/<name>_eval.py`) and update `docs/benchmarks.md` with the protocol.

## Code of conduct

Be kind and assume good intent. The project sits at the intersection of welfare-sensitive animal research, machine learning, and a prize culture — disagreements are normal and welcomed when they advance the work; ad-hominem and bad faith are not.

## Licence

By contributing you agree that your contributions are licensed under the MIT licence of the repository.

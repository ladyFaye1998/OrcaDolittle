# Data

The repository uses public killer-whale acoustic data and small derived artifacts. Raw audio is downloaded on demand and is excluded from Git.

## DCLDE 2026

DCLDE 2026 is the primary corpus because it provides public killer-whale acoustic annotations, source-file provenance, provider metadata, and ecotype labels suitable for reproducible embedding analyses [@palmer2025dclde; @palmer2025dclde_data].

## Stored In Git

- Small metadata joins in `data/join_tables/`
- Compact embedding matrices where file size and provenance are manageable
- Hash and environment summaries in `reports/`

## Excluded From Git

- Raw audio
- Audio caches
- Large model weights
- Local secrets and tokens
- Scratch runs and temporary outputs

## Data Integrity Checks

Every full run should log annotation counts, provider distribution, ecotype distribution, source-file coverage, encoder name, command-line parameters, and artifact hashes.

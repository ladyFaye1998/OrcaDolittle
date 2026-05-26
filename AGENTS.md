# AGENTS.md

## Cursor Cloud specific instructions

This repository is a **documentation-only research planning workspace** for a Coller-Dolittle Prize 2026-27 submission focused on killer whale bioacoustics.

### Key facts

- **No executable code exists.** The repository contains only Markdown documentation, a BibTeX bibliography (`paper/refs.bib`), a banner image, and standard project files (LICENSE, CITATION.cff, `.gitignore`).
- **No dependencies to install.** There is no `requirements.txt`, `pyproject.toml`, `package.json`, `Dockerfile`, or any other dependency manifest.
- **No services to run.** There is no backend, frontend, database, or any runnable process.
- **No tests or linting configured.** There are no test suites, linters, or formatters set up.
- The `.gitignore` anticipates future Python code, model weights, and audio data, but none of these exist yet.

### Repository structure

| Path | Purpose |
|------|---------|
| `README.md` | Project overview and file map |
| `EXECUTION_PLAN.md` | Stage-gated execution plan (Stages 1-6) |
| `docs/ai_architecture.md` | Locked four-head model stack specification |
| `docs/dataset_plan.md` | Locked dataset strategy and weekly ops plan |
| `docs/` (other files) | Literature reviews, audits, methodology notes |
| `paper/manuscript.md` | Manuscript draft (structural outline only) |
| `paper/refs.bib` | BibTeX bibliography (single source of truth) |
| `paper/video_script.md` | Two-minute video script |

### When code is added

The planned tech stack (per `docs/ai_architecture.md` and `.gitignore`) will use:
- Python with PyTorch
- NatureLM-audio and AVES2 as frozen encoders
- UMAP + HDBSCAN for clustering
- A ~30M-param Transformer for sequence modeling
- scikit-learn for linear/MLP probes

When Python code is eventually added, the update script should be updated to install dependencies (likely via `pip install -r requirements.txt` or `pip install -e .`).

### Development workflow

Since this is currently documentation-only:
- Edits are to Markdown files and BibTeX
- Every numerical or factual claim must cite a key in `paper/refs.bib` (per `.cursor/rules/citations.mdc`)
- The `EXECUTION_PLAN.md` is the entry point for understanding project status

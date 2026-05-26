# AGENTS.md

## Cursor Cloud specific instructions

### Repository overview

This is a **documentation-only research planning workspace** for a Coller-Dolittle Prize 2026-27 submission on killer whale (orca) acoustics. It contains:

- Markdown documentation (`docs/`, `paper/`, `README.md`, `EXECUTION_PLAN.md`)
- A BibTeX bibliography (`paper/refs.bib`)
- A single image asset (`assets/banner.png`)
- Standard metadata (`CITATION.cff`, `LICENSE`, `.gitignore`)

**There is no source code, no dependencies, no services, and no application to run.** The `.gitignore` is prepared for eventual Python/ML code (PyTorch, audio processing), but no code has been written yet.

### Development environment

- No package manager files exist (`requirements.txt`, `pyproject.toml`, `package.json`, etc.)
- No build system or test framework is configured
- No Docker containers, dev servers, or background services are needed
- The only tool required is `git`

### What future agents should know

1. **Do not attempt to install Python ML dependencies** (PyTorch, NatureLM-audio, AVES2, etc.) unless source code files are added to the repository first.
2. **All files follow a citation rule**: every numerical or factual claim must reference a key in `paper/refs.bib`. See `.cursor/rules/citations.mdc` if it exists.
3. **Locked decisions** are documented in `EXECUTION_PLAN.md`. Changes to locked decisions require a decision-log entry in `docs/ai_architecture.md`.
4. The repository structure is documented in the README file map table.

### Lint / Test / Build / Run

| Action | Command | Notes |
|--------|---------|-------|
| Lint | N/A | No linter configured (no code exists) |
| Test | N/A | No test framework configured |
| Build | N/A | No build system |
| Run | N/A | No application to run |

When code is eventually added, expect Python with PyTorch on a local RTX 4090 GPU workstation (per `EXECUTION_PLAN.md`).

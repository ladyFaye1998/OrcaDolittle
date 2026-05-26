# AGENTS.md

## Cursor Cloud specific instructions

This repository is a **documentation-only research planning workspace** for a Coller-Dolittle Prize 2026-27 submission focused on killer whale bioacoustics.

### Key facts

- **Stage 1 scaffolding is in place.** Python project with `pyproject.toml`, download scripts, and a working AVES2 hello-world pipeline.
- **No heavyweight compute available in this VM.** NatureLM-audio (8B params) requires a GPU. AVES2 works on CPU and is the comparator encoder.
- There is no backend, frontend, database, or any long-running service.
- No tests or linting configured beyond what's in `pyproject.toml` (ruff, pytest).

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

### Development setup

```bash
pip install -e ".[dev]"          # Install the project + dev tools (ruff, pytest, jupyter)
pip install avex                  # AVES2 encoder (BEATs backbone)
python3 scripts/download_annotations.py   # Download Annotations.csv (~48 MB) from NOAA GCS
python3 scripts/download_sample_audio.py  # Download 3 sample clips (~15 MB)
python3 scripts/hello_world.py            # Run AVES2 on a sample clip → 768-dim embedding
```

### Data access

- DCLDE 2026 data lives on GCS at `gs://noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/`
- Public bucket, no auth needed (uses `gcsfs` with `token="anon"`)
- The folder was named `2027` because the conference was renamed; it's the same DOI 10.25921/15ey-mh50 dataset
- `Annotations.csv` (~48 MB, 207K rows) is the collated metadata; audio (~1.6 TB) is in per-provider subdirectories
- Audio is gitignored. Use download scripts to pull what you need.

### Encoders

- **AVES2** (comparator): `pip install avex` → `load_model("esp_aves2_sl_beats_all", return_features_only=True, device="cpu")` → (batch, time_steps, 768) embeddings. Expects 16 kHz mono audio. Works on CPU.
- **NatureLM-audio** (primary): Requires GPU + HuggingFace access to Meta Llama 3.1 8B Instruct. ~8B params. Install via `github.com/earthspecies/NatureLM-audio`.

### Development workflow

- Every numerical or factual claim must cite a key in `paper/refs.bib` (per `.cursor/rules/citations.mdc`)
- The `EXECUTION_PLAN.md` is the entry point for understanding project status
- Downloaded data goes in `data/dclde/` (gitignored); scripts re-download as needed

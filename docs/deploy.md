# Deployment

OrcaDolittle ships two deployment paths: a HuggingFace Space (Gradio web demo) and a Docker image (full inference stack).

## HuggingFace Space

The Space is configured by [`deploy_space.py`](../deploy_space.py) and deploys the Gradio interface from [`web/app.py`](../web/app.py).

### One-time setup

1. **Install the HuggingFace CLI** (already on this machine if you installed the `huggingface-hub` extra).
2. **Authenticate.** Create a write-scoped token at <https://huggingface.co/settings/tokens> and run:

   ```bash
   hf auth login
   ```

   When prompted, paste the token. Confirm with `hf auth whoami`.

### Deploy

From the repository root:

```bash
python deploy_space.py
```

The script:

* Stages `web/`, `orcadolittle/`, and `assets/` into a temporary folder.
* Writes a Space-flavoured `requirements.txt` and `README.md` (with the YAML front-matter).
* Calls `HfApi.create_repo` (idempotent) with `private=True` and `space_sdk="gradio"`.
* Uploads via `HfApi.upload_folder`.
* Triggers a factory reboot so the build is clean.

The first build takes 4–6 minutes; subsequent updates take 1–2 minutes. The URL is printed at the end:
`https://huggingface.co/spaces/ladyFaye1998/OrcaDolittle`

### Toggling visibility

The Space is created **private** by default. To go public, change `private=True` to `private=False` in `deploy_space.py` and re-run, or toggle from the Space settings on the HF web UI.

## Docker

See [`orcadolittle/docker/Dockerfile`](../orcadolittle/docker/Dockerfile).

```bash
docker build -t orcadolittle:latest -f orcadolittle/docker/Dockerfile .
docker run --rm -v $PWD/data:/data orcadolittle:latest loop --hydrophone /data/sample.wav --dry-run
```

For GPU inference, switch the base image to `nvidia/cuda:12.1.1-runtime-ubuntu22.04` and add the CUDA-matched `torch` wheels. The container's entry-point is the OrcaDolittle CLI, so any subcommand (`perceive`, `generate`, `select`, `predict`, `loop`, `benchmark`) works directly.

## GitHub CI

The CI workflow at `.github/workflows/ci.yml` runs `ruff`, `mypy`, and `pytest` across Python 3.10 / 3.11 / 3.12 on every push and pull request.

If you ever see *"refusing to allow an OAuth App to create or update workflow `.github/workflows/ci.yml` without `workflow` scope"* when pushing CI changes, the local `gh` token is missing the `workflow` scope. Fix with:

```bash
gh auth refresh -s workflow
```

(The flow opens a browser; the resulting token is stored in the `gh` keyring.)
